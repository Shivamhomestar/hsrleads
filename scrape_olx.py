import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

# Function to extract phone numbers
def extract_phone_numbers(text):
    pattern = r'(?:\+91[\-\s]?|0)?[6-9]\d{9}'
    numbers = re.findall(pattern, text)
    
    cleaned = set()
    for num in numbers:
        num = re.sub(r'[^0-9]', '', num)
        if len(num) == 10:
            cleaned.add(num)
        elif len(num) > 10 and num.endswith(num[-10:]):
            cleaned.add(num[-10:])
    
    return list(cleaned)

# Function to scrape OLX
def scrape_olx(keyword, city='mumbai', max_results=10):
    base_url = f'https://www.olx.in/{city}/q-{keyword.replace(" ", "-")}/'
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        resp = requests.get(base_url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching OLX page: {e}")
        return []
    
    soup = BeautifulSoup(resp.content, 'lxml')
    leads = []
    
    listings = soup.find_all('li', class_='EIR5N')[:max_results]
    
    for listing in listings:
        title_tag = listing.find('span')
        title = title_tag.text.strip() if title_tag else "No Title"

        detail_link = listing.find('a', href=True)
        phone = "Not Found"

        if detail_link:
            detail_url = detail_link['href']
            # Ensure the detail URL is absolute
            if detail_url.startswith('/'):
                detail_url = f'https://www.olx.in{detail_url}'
            try:
                detail_resp = requests.get(detail_url, headers=headers, timeout=10)
                detail_resp.raise_for_status()
                detail_soup = BeautifulSoup(detail_resp.content, 'lxml')
                text = detail_soup.get_text(" ", strip=True)
                
                phones = extract_phone_numbers(text)
                phone = phones[0] if phones else "Not Found"
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching detail page: {e}")

        leads.append({'Title': title, 'Phone': phone, 'Source': detail_link['href'] if detail_link else "N/A"})
    
    return leads

# Example usage in a Streamlit app:
def main():
    st.title("OLX Phone Number Scraper")
    keyword = st.text_input("Enter search keyword:")
    city = st.text_input("Enter city:", value="mumbai")
    max_results = st.number_input("Max results:", min_value=1, max_value=50, value=10)
    
    if st.button("Scrape"):
        if not keyword:
            st.warning("Please enter a keyword.")
        else:
            leads = scrape_olx(keyword, city, max_results)
            if leads:
                df = pd.DataFrame(leads)
                st.write(df)
                st.download_button("Download CSV", df.to_csv(index=False), "olx_leads.csv")
            else:
                st.info("No leads found.")
                
if __name__ == "__main__":
    main()