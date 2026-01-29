import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# Regular Expressions for data extraction
EMAIL_REGEX = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
# Matches various phone formats: (123) 456-7890, 123-456-7890, etc.
PHONE_REGEX = r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}'

def scrape_contacts(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract Text
        page_text = soup.get_text()
        
        # Find Matches
        emails = list(set(re.findall(EMAIL_REGEX, page_text)))
        phones = list(set(re.findall(PHONE_REGEX, page_text)))
        
        # Name extraction is tricky; here we look for common patterns near contact info
        # This is a simplified approach looking at <a> tags and <h3> tags
        names = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'strong', 'b']):
            clean_name = tag.get_text().strip()
            if len(clean_name.split()) <= 3 and len(clean_name) > 2:
                names.append(clean_name)
        
        return emails, phones, list(set(names))
    
    except Exception as e:
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
