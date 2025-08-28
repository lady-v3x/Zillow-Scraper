# zillow_streamlit_app.py
import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from PIL import Image
import re

st.set_page_config(page_title="Zillow Scraper App")
st.title("Zillow Listing Extractor 🏡")

st.markdown("Paste Zillow links below (one per line). We'll extract key details and group by location.")

zillow_input = st.text_area("Zillow Links")

@st.cache_data(show_spinner=False)
def extract_data_from_zillow(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        def extract_text(pattern, fallback="N/A"):
            match = soup.find("span", string=re.compile(pattern))
            return match.get_text(strip=True) if match else fallback

        price = extract_text(r"\$\d{1,3}(,\d{3})+")
        bed_bath_info = soup.select("span[data-testid='bed-bath-item']")
        beds = bed_bath_info[0].get_text(strip=True).split()[0] if len(bed_bath_info) > 0 else "N/A"
        baths = bed_bath_info[1].get_text(strip=True).split()[0] if len(bed_bath_info) > 1 else "N/A"
        sqft = bed_bath_info[2].get_text(strip=True) if len(bed_bath_info) > 2 else "N/A"

        location_elem = soup.find("h1", attrs={"data-testid": "home-details-summary-headline"})
        if location_elem and "," in location_elem.text:
            city, state = map(str.strip, location_elem.text.split(","))
        else:
            city, state = "N/A", "N/A"

        og_image = soup.find("meta", property="og:image")
        thumbnail = og_image["content"] if og_image else None

        return {
            "URL": url,
            "Price": price,
            "Beds": beds,
            "Baths": baths,
            "Square Feet": sqft,
            "City": city,
            "State": state,
            "High School": "Coming soon",
            "School Rating": "Coming soon",
            "Thumbnail": thumbnail
        }
    except Exception as e:
        return {
            "URL": url,
            "Price": "Error",
            "Beds": "Error",
            "Baths": "Error",
            "Square Feet": "Error",
            "City": "Error",
            "State": "Error",
            "High School": "Error",
            "School Rating": "Error",
            "Thumbnail": None
        }

if st.button("Fetch Listings"):
    with st.spinner("Extracting data from Zillow links..."):
        links = zillow_input.strip().split("\n")
        listings = [extract_data_from_zillow(link.strip()) for link in links if link.strip()]
        df = pd.DataFrame(listings)

        if not df.empty:
            st.success("Listings extracted!")
            st.dataframe(df.drop(columns=["Thumbnail"]))

            # Show preview images
            for i, row in df.iterrows():
                st.markdown(f"**{row['City']}, {row['State']} — {row['Price']}**")
                if row["Thumbnail"]:
                    try:
                        img_data = requests.get(row["Thumbnail"]).content
                        st.image(Image.open(BytesIO(img_data)), width=300)
                    except:
                        st.warning("Thumbnail failed to load.")

            # Export to Excel
            excel_buffer = BytesIO()
            df.drop(columns=["Thumbnail"]).to_excel(excel_buffer, index=False)
            st.download_button("Download Excel File", excel_buffer.getvalue(), file_name="zillow_grouped_listings.xlsx")
        else:
            st.warning("No valid listings extracted.")
