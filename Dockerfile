FROM apache/airflow:3.1.3

USER root

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg unzip curl

# Install Brave Browser
RUN curl -fsS https://dl.brave.com/install.sh | bash

# Install ChromeDriver
RUN wget -q "https://storage.googleapis.com/chrome-for-testing-public/142.0.7444.175/linux64/chromedriver-linux64.zip" && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver && \
    rm chromedriver-linux64.zip && \
    rm -rf chromedriver-linux64

USER airflow

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt