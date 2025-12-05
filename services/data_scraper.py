import os
import sys
import json
import sqlite3
import time
from urllib.parse import urljoin, urlparse
from collections import deque
from typing import List, Dict, Any, Tuple, Optional
import io
import pytesseract
from PIL import Image

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pydantic import BaseModel, Field
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions
from dotenv import load_dotenv

def setup_api_key():
    """
    Loads the Gemini API key from a .env file.
    """
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file or environment variables.")
    genai.configure(api_key=api_key)

def setup_database(db_name="lila_data.db"):
    """
    Initializes the SQLite database and creates the table if it doesn't exist.
    """
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caregiver_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        communication_style TEXT NOT NULL,
        outcome_rating INTEGER NOT NULL,
        UNIQUE(action_type, communication_style, outcome_rating)
    )
    """)
    conn.commit()
    conn.close()
    print(f"Database '{db_name}' is set up.")

def load_site_configs(config_file: str = "site_configs.json") -> Dict[str, Dict[str, Any]]:
    """Loads site-specific scraping configurations from a JSON file."""
    try:
        with open(config_file, 'r') as f:
            configs = json.load(f)
        return {config['domain']: config for config in configs}
    except FileNotFoundError:
        print(f"Warning: Site configuration file '{config_file}' not found. Using generic fallback.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{config_file}'. Please check its format.")
        return {}

def get_site_config(url: str, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Gets the specific configuration for a given URL."""
    domain = urlparse(url).netloc
    # Find a config where the domain is a substring of the URL's domain
    for config_domain, config in configs.items():
        if config_domain in domain:
            return config
    # Fallback for sites not in the config
    return {"domain": domain, "target_element": "article", "link_keyword": None}

class CaregiverActionLog(BaseModel):
    """
    Pydantic model for structuring the extracted data.
    """
    action_type: str = Field(description="The type of action taken by the caregiver.")
    communication_style: str = Field(description="The style of communication used.")
    outcome_rating: int = Field(description="A rating of the outcome from 1 to 5.")

def fetch_page_content_with_ocr(driver: uc.Chrome, url: str) -> str:
    """
    Fetches page content by taking screenshots and using OCR. This is for sites
    like Scribd that render text on a canvas.
    """
    print("--- Using OCR method for content extraction.")
    driver.get(url)
    time.sleep(5) # Wait for the document to load

    all_text = ""
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        screenshot = driver.get_screenshot_as_png()
        image = Image.open(io.BytesIO(screenshot))
        all_text += pytesseract.image_to_string(image) + "\n\n"

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    return all_text

def fetch_page_content_and_links(driver: uc.Chrome, url: str, site_config: Dict[str, Any]) -> Tuple[Optional[str], List[str]]:
    """
    Stage 1: Fetches the content of a URL and extracts text from the main content container.
    """
    target_element = site_config.get("target_element", "article")
    try:
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        links = []
        base_url = urlparse(url)
        
        ignore_patterns = [
            "Special:", "action=edit", "action=history", "returnto=", "#"
        ]

        for link in soup.find_all('a', href=True):
            href = link['href']
            joined_url = urljoin(url, href)
            parsed_joined_url = urlparse(joined_url)

            if any(pattern in joined_url for pattern in ignore_patterns):
                continue

            if parsed_joined_url.netloc == base_url.netloc:
                links.append(joined_url)

        selectors_to_try = [
            target_element,
            "div.entry-content",
            "div.post_body",
            "div.message-content",
            "div.mw-parser-output",
            "article",
            "main",
        ]
        
        content_elements = []
        for selector in selectors_to_try:
            elements = [el for el in soup.select(selector) if el.get_text(strip=True)]
            if elements:
                content_elements = elements
                break

        if not content_elements:
            return "", links

        full_text = []
        for element in content_elements:
            for script_or_style in element(["script", "style"]):
                script_or_style.decompose()
            full_text.append(element.get_text(separator='\n', strip=True))

        return "\n\n---\n\n".join(full_text), links
    except TimeoutException:
        return f"Error: Timed out waiting for page to load on {url}", []
    except Exception as e:
        return f"An error occurred with Selenium on {url}: {e}", []

def perform_form_login(driver: uc.Chrome, site_config: Dict[str, Any]):
    """Performs a login using a username/password form."""
    login_url = site_config.get("login_url")
    credentials = site_config.get("login_credentials")
    selectors = site_config.get("login_selectors")

    if not all([login_url, credentials, selectors]):
        print("--- Login configuration is incomplete. Skipping form login.")
        return

    print(f"--- Performing login on {login_url}...")
    try:
        driver.get(login_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, selectors["email_field"])))
        
        driver.find_element(By.CSS_SELECTOR, selectors["email_field"]).send_keys(credentials["email"])
        driver.find_element(By.CSS_SELECTOR, selectors["password_field"]).send_keys(credentials["password"])
        driver.find_element(By.CSS_SELECTOR, selectors["submit_button"]).click()
        
        print("--- Login submitted. Waiting for page to load...")
        time.sleep(5)
    except Exception as e:
        print(f"--- Error during form login: {e}")

def crawl_and_scrape_site(start_url: str, site_config: Dict[str, Any], cookie_file: Optional[str] = None, headless: bool = True, max_pages: int = 10) -> List[CaregiverActionLog]:
    """
    Crawls a website starting from a URL, scrapes content, and extracts structured data.
    """
    options = uc.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    driver = uc.Chrome(options=options)

    if site_config.get("login_url"):
        perform_form_login(driver, site_config)

    if cookie_file and os.path.exists(cookie_file):
        parsed_start_url = urlparse(start_url)
        cookie_domain_url = f"{parsed_start_url.scheme}://{parsed_start_url.netloc}"
        driver.get(cookie_domain_url)
        print(f"Loading cookies from {cookie_file} for domain {cookie_domain_url}...")
        with open(cookie_file, 'r') as f:
            cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        print("Cookies loaded. Refreshing page to apply session...")
        driver.refresh()
        time.sleep(3)

    urls_to_visit = deque([start_url])
    visited_urls = set()
    all_structured_data = []
    pages_crawled = 0

    while urls_to_visit and pages_crawled < max_pages:
        current_url = urls_to_visit.popleft()
        normalized_url = urljoin(current_url, urlparse(current_url).path)
        if normalized_url in visited_urls:
            continue

        pages_crawled += 1
        print(f"\n[{pages_crawled}/{max_pages}] Scraping: {current_url}")
        
        if site_config.get("ocr", False):
            content = fetch_page_content_with_ocr(driver, current_url)
            new_links = []
        else:
            content, new_links = fetch_page_content_and_links(driver, current_url, site_config)

        visited_urls.add(normalized_url)

        if content.startswith("Error:"):
            print(content)
            continue

        print(f"--- Found {len(new_links)} links on page. Analyzing content...")
        
        topic_links = []
        other_links = []
        link_keyword = site_config.get("link_keyword")

        if link_keyword:
            for link in new_links:
                if link_keyword and link_keyword in link:
                    topic_links.append(link)
                else:
                    other_links.append(link)
            new_links = topic_links + other_links

        for link in new_links:
            if link not in visited_urls:
                urls_to_visit.append(link)

        structured_data = extract_structured_data(content, current_url)
        if structured_data:
            all_structured_data.extend(structured_data)
            print(f"+++ Extracted {len(structured_data)} new records.")

        time.sleep(1)

    driver.quit()
    return all_structured_data

def extract_structured_data(content: str, url: str) -> List[CaregiverActionLog]:
    """
    Stage 2: Uses the Gemini API to extract structured data from text content with retry logic.
    """
    model = genai.GenerativeModel('gemini-pro-latest')
    
    schema = CaregiverActionLog.model_json_schema()

    prompt = f"""
    Analyze the following content from a caregiver forum post or article.
    Based on the text, identify actions taken by a caregiver.
    For each action, extract the data and format it into a JSON object that conforms to the following schema.
    
    JSON Schema:
    {json.dumps(schema, indent=2)}

    Only analyze narratives that include the following keywords related to caregiver/little dynamics.
    Do not change these keywords.

    **Roleplay & Dynamic Terms:**
    - Mommy / Mama / Mum / Mother, Caretaker / Caregiver (CG), Daddy / Papa / Guardian, Little / Little one / Little space / Littlespace, Adult Baby (AB), ABDL / AB/DL, DD/lg (Daddy Dom/little girl), DD/lb (Daddy Dom/little boy), MD/lg (Mommy Dom/little girl), MD/lb (Mommy Dom/little boy), Ageplay / Age regression, Infantilism / Paraphilic infantilism

    **Diaper & Potty Terms:**
    - Diaper / Nappy, Diaper lover (DL) / Diapered, Crinkle / Crinkles / Crinkly, Wet / Wetting / Wetted, Mess / Messed / Messing, Used / Soiled, Change / Changies / Changing, Unpotty training / Unpotty train, Pre-potty trained, Plastic pants / Rubber pants / Diaper cover, Padded / Padding

    **Baby/Childhood Items & Actions:**
    - Bottle / Binkie / Paci (Pacifier), Sippy cup, Onesie / Footie pajamas / Sleepsuit, Bib, Crib / Playpen, Lullaby, Spanking / Scold / Chastised, Time-out, Baby voice

    Strictly return a list of JSON objects. If no relevant actions are found, return an empty list.

    Content to analyze:
    ---
    {content}
    ---

    JSON Output:
    """
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

    max_retries = 3
    delay = 5
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, safety_settings=safety_settings)
            if not response.candidates:
                    print(f"--- Gemini API block: No candidates returned. Reason: {response.prompt_feedback.block_reason.name if response.prompt_feedback else 'Unknown'}")
                    with open("skipped_urls.log", "a") as f:
                        f.write(f"{url}\n")
                    return []

            cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
            if not cleaned_response:
                    print("--- Model returned an empty response.")
                    return []
            data = json.loads(cleaned_response)
            return [CaregiverActionLog(**item) for item in data]
        except exceptions.ResourceExhausted as e:
            print(f"--- Gemini API rate limit reached. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
            delay *= 2
        except exceptions.NotFound as e:
            print(f"Error: The model name 'gemini-pro-latest' was not found. {e}")
            return []
        except ValueError as e:
            try:
                print(f"--- Gemini API safety block: The content was flagged. Reason: {response.prompt_feedback.block_reason.name}")
                with open("skipped_urls.log", "a") as f:
                    f.write(f"{url}\n")
            except Exception:
                print(f"--- A ValueError occurred, and prompt feedback was not available: {e}")
            return []
        except (json.JSONDecodeError, TypeError) as e:
            print(f"--- Error decoding JSON from model response: {e}")
            print(f"Raw response: {response.text}")
            return []
    print("--- Model failed to return valid JSON after multiple retries.")
    return []

def save_data(data: List[CaregiverActionLog], output_filename: str):
    """Saves the extracted data to the SQLite database using a bulk insert."""
    if not data:
        print("No structured data was extracted to save.")
        return

    conn = sqlite3.connect(output_filename)
    cursor = conn.cursor()

    initial_row_count = cursor.execute("SELECT COUNT(*) FROM caregiver_actions").fetchone()[0]

    records_to_insert = [
        (log.action_type, log.communication_style, log.outcome_rating) for log in data
    ]

    cursor.executemany("""
    INSERT OR IGNORE INTO caregiver_actions (action_type, communication_style, outcome_rating)
    VALUES (?, ?, ?)
    """, records_to_insert)

    inserted_count = conn.total_changes - initial_row_count

    conn.commit()
    total_rows = cursor.execute("SELECT COUNT(*) FROM caregiver_actions").fetchone()[0]
    conn.close()

    if inserted_count > 0:
        print(f"Saved {inserted_count} new records. Total records in {output_filename}: {total_rows}")

def main():
    """Main function to run the scraper."""
    setup_api_key()

    if len(sys.argv) < 2:
        print("Usage: python data_scraper.py <URL>")
        sys.exit(1)

    target_url = sys.argv[1]
    db_file = "lila_data.db"

    setup_database(db_file)
    
    site_configs = load_site_configs()
    site_config = get_site_config(target_url, site_configs)
    target_element = site_config.get("target_element", "article")

    print(f"Starting crawl at: {target_url} (targeting '{target_element}' elements using config for '{site_config['domain']}')")
    all_data = crawl_and_scrape_site(start_url=target_url, site_config=site_config, cookie_file="x_cookies.json", headless=False, max_pages=20)
    save_data(all_data, db_file)
    print("\nCrawling and scraping finished.")

if __name__ == "__main__":
    main()