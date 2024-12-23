import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from io import BytesIO

# Function to decode the Unix timestamp
def decode_timestamp(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

# Function to fetch data from the API
def fetch_data(query, start_date, end_date, max_pages):
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

    ads_info = []
    continuation_token = None
    page_count = 0

    while True:
        if continuation_token:
            querystring["continuation_token"] = continuation_token

        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()

            for ad_set in data.get("results", []):
                for ad in ad_set:
                    ad_info = {
                        "Continuation Token": data.get("continuation_token", ""),
                        "Title": ad["snapshot"].get("title"),
                        "Link URL": ad["snapshot"].get("link_url"),
                        "Page Name": ad.get("pageName"),
                        "Image URL": ad["snapshot"]["images"][0].get("original_image_url") if ad["snapshot"].get("images") else None,
                        "Body": ad["snapshot"].get("body", {}).get("markup", {}).get("__html"),
                        "Creation Time": decode_timestamp(ad["snapshot"].get("creation_time")),
                        "End Date": decode_timestamp(ad.get("endDate")) if ad.get("endDate") else None,
                        "Page URL": ad["snapshot"].get("page_profile_uri"),
                        "Page Like Count": ad["snapshot"].get("page_like_count"),
                        "Publisher Platforms": ad.get("publisherPlatform")
                    }
                    ads_info.append(ad_info)

            continuation_token = data.get("continuation_token")
            page_count += 1

            if not continuation_token or page_count >= max_pages:
                break
        else:
            st.error(f"Error fetching data: {response.status_code}")
            break

    return ads_info

# Streamlit app layout
st.title("Meta Ads Data Fetcher")

# User inputs
query = st.text_input("Enter query (e.g., Cosmetics):", "")
start_date = st.date_input("Start date:")
end_date = st.date_input("End date:")
max_pages = st.number_input("Enter the number of pages to fetch:", min_value=1, step=1)

# Fetch and process data
if st.button("Fetch Data"):
    if start_date > end_date:
        st.error("Start date cannot be later than end date.")
    else:
        ads_info = fetch_data(query, start_date.isoformat(), end_date.isoformat(), max_pages)

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
