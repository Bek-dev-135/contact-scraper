import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import time

# Regular Expressions for data extraction
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# Matches various phone formats: (123) 456-7890, 123-456-7890, etc.
PHONE_REGEX = r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'



def scrape_contacts(url):
    # Setup Chrome options for headless mode (required for Cloud)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)
        
        # Wait up to 10 seconds for the business info div to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "SFbizinf")))
        
        # Give it an extra second for any animations
        time.sleep(2)
        
        page_source = driver.page_source
        
        # Extract matches
        emails = list(set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source)))
        phones = list(set(re.findall(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', page_source)))
        
        # Look specifically for the name in that class you found
        names = []
        name_elements = driver.find_elements(By.CLASS_NAME, "SFbizctcnam")
        for el in name_elements:
            names.append(el.text.strip())
            
        driver.quit()
        return emails, phones, names
        
    except Exception as e:
        if 'driver' in locals(): driver.quit()
        return None, None, str(e)
# Streamlit UI
st.set_page_config(page_title="Contact Scraper", page_icon="🔍")
st.title("🔍 Web Contact Extractor")
st.write("Enter a URL to scan for emails, phone numbers, and potential names.")

url_input = st.text_input("Enter Website URL (include http:// or https://):", "https://example.com")

if st.button("Scrape Data"):
    if url_input:
        with st.spinner('Scanning page...'):
            emails, phones, names = scrape_contacts(url_input)
            
            if emails is None:
                st.error(f"Error: {names}")
            else:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📧 Emails")
                    if emails:
                        st.write(emails)
                    else:
                        st.info("No emails found.")

                with col2:
                    st.subheader("📞 Phone Numbers")
                    if phones:
                        st.write(phones)
                    else:
                        st.info("No phone numbers found.")

                st.divider()
                st.subheader("👤 Potential Contact Names")
                st.caption("Extracted from headers and bold text. May require manual verification.")
                st.write(", ".join(names[:20]) if names else "No names detected.")
                
                # Option to download
                if emails or phones:
                    df = pd.DataFrame({
                        "Type": ["Email"]*len(emails) + ["Phone"]*len(phones),
                        "Value": emails + phones
                    })
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", csv, "contacts.csv", "text/csv")
    else:
        st.warning("Please enter a valid URL.")
