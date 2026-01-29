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
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium" 

    try:
        service = Service("/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 1. Scrape the Directory Page
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "SFbizinf")))
        time.sleep(2)
        
        page_source = driver.page_source
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_source)
        phones = re.findall(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', page_source)
        
        names = [el.text.strip() for el in driver.find_elements(By.CLASS_NAME, "SFbizctcnam")]

        # 2. Deep Dive: If no email, find the external website link
        if not emails:
            try:
                # Look for the 'Website' link specifically
                website_link_el = driver.find_element(By.CLASS_NAME, "SFbizctcweb")
                external_url = website_link_el.get_attribute("href")
                
                if external_url:
                    driver.get(external_url)
                    time.sleep(3) # Wait for business site to load
                    external_source = driver.page_source
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', external_source)
                    # If we find phones on the main site, add them too
                    external_phones = re.findall(r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', external_source)
                    phones.extend(external_phones)
            except Exception:
                pass # If there's no website link, we just move on

        driver.quit()
        return list(set(emails)), list(set(phones)), list(set(names))
        
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
