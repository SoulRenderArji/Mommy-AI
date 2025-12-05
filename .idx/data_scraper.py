import os
import sys
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

def get_page_content(url):
    """Fetches and returns the HTML content of a webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not retrieve content from {url}. {e}", file=sys.stderr)
        return None

def extract_text(html):
    """Extracts and cleans the visible text from HTML content."""
    if not html:
        return ""
    soup = BeautifulSoup(html, 'html.parser')
    # Remove script and style elements
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    # Get text and clean it up
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def clean_and_parse_json(raw_text):
    """Cleans Gemini's response and parses it into a JSON object."""
    # Find the start and end of the JSON block
    json_start = raw_text.find('{')
    json_end = raw_text.rfind('}')
    if json_start == -1 or json_end == -1:
        print("Error: No JSON object found in the response.", file=sys.stderr)
        return None
    
    json_str = raw_text[json_start:json_end+1]
    return json.loads(json_str)

def analyze_text_with_gemini(text):
    """Uses the Gemini API to analyze text and extract structured data."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.", file=sys.stderr)
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    prompt = f"""
    Based on the following text from an article or forum, please extract structured information about caregiver dynamics, ABDL, or related lifestyles.
    Identify key themes, roles (e.g., 'Caregiver', 'Little'), common activities, and any expressed rules or dynamics.
    Present the output as a JSON object. If no relevant information is found, return an empty JSON object.

    Text to analyze:
    ---
    {text[:10000]} 
    ---
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error: Gemini API call failed. {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python data_scraper.py <URL>", file=sys.stderr)
        sys.exit(1)

    target_url = sys.argv[1]
    html_content = get_page_content(target_url)
    if html_content:
        main_text = extract_text(html_content)
        if main_text:
            structured_data = analyze_text_with_gemini(main_text)
            if structured_data:
                cleaned_json = clean_and_parse_json(structured_data)
                try:
                    if cleaned_json:
                        # Print formatted JSON to stdout
                        print(json.dumps(cleaned_json, indent=2))
                except json.JSONDecodeError as e:
                    print(f"Error: Failed to decode JSON from API response. {e}", file=sys.stderr)
                    print(f"Raw response was:\n{structured_data}", file=sys.stderr)