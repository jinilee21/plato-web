#!/usr/bin/env bash
apt-get update && apt-get install -y wget unzip curl

# Install Chrome
curl https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb
apt install -y ./chrome.deb

# Install Chromedriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+' | head -1)
CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION)
wget -N https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/local/bin/chromedriver
chmod +x /usr/local/bin/chromedriver
