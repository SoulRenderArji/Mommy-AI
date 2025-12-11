# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    PORT=8080

WORKDIR $APP_HOME

# Install system dependencies required for your python packages
# tesseract-ocr for pytesseract, espeak for pyttsx3, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    espeak \
    libespeak1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the container will listen on
EXPOSE 8080

# Run the application using python directly to ensure background threads start
CMD ["python", "mommy_ai.py"]