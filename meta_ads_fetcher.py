import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import BytesIO

# Function to decode the Unix timestamp
def decode_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Function to fetch data from the API
def fetch_data(query, start_date, end_date):
    url = "https://meta-ad-library.p.rapidapi.com/search/ads"
    querystring = {
        "query": query,
        "country_code": "US",
        "active_status": "active",
        "media_types": "image",
        "platform": "facebook,instagram",
        "start_min_date": start_date,
        "start_max_date": end_date,
        "ad_type": "all"
    }
    x_rapidapi_key = st.secrets['X_RAPIDAPI_KEY']
    headers = {
        "x-rapidapi-key": x_rapidapi_key,
        "x-rapidapi-host": "meta-ad-library.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return None

# Streamlit app layout
st.title("Meta Ads Data Fetcher")

# User inputs
query = st.text_input("Enter query (e.g., Cosmetics):", "Cosmetics")
start_date = st.date_input("Start date:")
end_date = st.date_input("End date:")

# Fetch and process data
if st.button("Fetch Data"):
    if start_date > end_date:
        st.error("Start date cannot be later than end date.")
    else:
        data = fetch_data(query, start_date.isoformat(), end_date.isoformat())
        
        if data:
            # Extract and process the data
            ads_info = []
            for ad_set in data.get("results", []):
                for ad in ad_set:
                    ad_info = {
                        "Title": ad["snapshot"].get("title"),
                        "Link URL": ad["snapshot"].get("link_url"),
                        "Page Name": ad.get("pageName"),
                        "Image URL": ad["snapshot"]["images"][0].get("original_image_url") if ad["snapshot"].get("images") else None,
                        "Body": ad["snapshot"]["body"]["markup"].get("__html") if ad["snapshot"].get("body", {}).get("markup") else None,
                        "Creation Time": decode_timestamp(ad["snapshot"].get("creation_time")),
                        "End Date": decode_timestamp(ad.get("endDate")) if ad.get("endDate") else None,
                        "Page URL": ad["snapshot"].get("page_profile_uri"),
                        "Page Like Count": ad["snapshot"].get("page_like_count"),
                        "Publisher Platforms": ad.get("publisherPlatform")
                    }
                    ads_info.append(ad_info)
            
            if ads_info:
                df = pd.DataFrame(ads_info)

                # Generate Excel file in memory
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name="Meta Ads")
                output.seek(0)

                # Download button for the Excel file
                st.success("Data fetched successfully!")
                st.download_button(
                    label="Download Excel File",
                    data=output,
                    file_name="meta_ads_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No data found for the given query and date range.")
