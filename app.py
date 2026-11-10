import streamlit as st
import pandas as pd
import os

# Set page configurations
st.set_page_config(
    page_title="Learn@TLC - Training Calendar",
    page_icon="📅",
    layout="wide"
)

# 1. Display the Custom Header Banner
IMAGE_PATH = "LearnTLC_.png"
if os.path.exists(IMAGE_PATH):
    st.image(IMAGE_PATH, use_container_width=True)
else:
    st.title("Learn @ TLC")
    st.subheader("Learning Development and Documentation Support")

st.markdown("---")

# 2. Helper function to load and clean data
@st.cache_data
def load_and_clean_data(file_path):
    if not os.path.exists(file_path):
        return None
    
    # Read CSV
    df = pd.read_csv(file_path)
    
    # Drop rows that have NaN values in critical columns
    df = df.dropna(subset=['Date', 'Title', 'StartTime', 'EndTime'])
    
    # Exclude aggregate or error rows (e.g., #VALUE!, #REF!)
    df = df[~df['Date'].astype(str).str.contains('#')]
    df = df[~df['Title'].astype(str).str.contains('#')]
    
    # Convert Date to integers
    df['Date'] = pd.to_numeric(df['Date']).astype(int)
    
    # Sort by Date and StartTime
    df = df.sort_values(by=['Date', 'StartTime'])
    return df

# Check for local file or allow upload
csv_file_path = "csv_html.csv"
uploaded_file = st.sidebar.file_uploader("Upload a new training CSV file", type=["csv"])

if uploaded_file is not None:
    df_clean = load_and_clean_data(uploaded_file)
elif os.path.exists(csv_file_path):
    df_clean = load_and_clean_data(csv_file_path)
else:
    st.warning("⚠️ No data file found. Please upload a CSV file in the sidebar.")
    df_clean = None

if df_clean is not None:
    # Sidebar Filters
    st.sidebar.header("Filter Calendar")
    search_query = st.sidebar.text_input("🔍 Search class title", "")
    
    # Unique locations filter
    locations = ["All"] + sorted(df_clean['Location'].dropna().unique().tolist())
    selected_loc = st.sidebar.selectbox("📍 Filter by Location", locations)
    
    # Filter DataFrame based on selection
    filtered_df = df_clean.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_query, case=False)]
    if selected_loc != "All":
        filtered_df = filtered_df[filtered_df['Location'] == selected_loc]
        
    st.markdown("### 📅 Course Training Calendar")
    
    # Define weeks structure based on Monday dates
    # Week 1: 2-6 | Week 2: 9-13 | Week 3: 16-20 | Week 4: 23-27 | Week 5: 30-31
    weeks_mapping = [
        {"label": "Week 1 (Days 2 - 6)", "days": [2, 3, 4, 5, 6]},
        {"label": "Week 2 (Days 9 - 13)", "days": [9, 10, 11, 12, 13]},
        {"label": "Week 3 (Days 16 - 20)", "days": [16, 17, 18, 19, 20]},
        {"label": "Week 4 (Days 23 - 27)", "days": [23, 24, 25, 26, 27]},
        {"label": "Week 5 (Days 30 - 31)", "days": [30, 31, None, None, None]}
    ]
    
    # Grid column names
    cols_header = st.columns(5)
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for i, day_name in enumerate(weekdays):
        cols_header[i].markdown(f"<h4 style='text-align: center; color: #1f4e79;'>{day_name}</h4>", unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Render each week row
    for week in weeks_mapping:
        # Check if the week has any classes in the filtered dataset to save screen space
        active_days_in_week = [d for d in week["days"] if d is not None]
        has_classes = filtered_df['Date'].isin(active_days_in_week).any()
        
        if not has_classes:
            # Skip empty weeks unless they are explicitly wanted
            continue
            
        st.markdown(f"##### **{week['label']}**")
        week_cols = st.columns(5)
        
        for idx, date_num in enumerate(week["days"]):
            with week_cols[idx]:
                if date_num is not None:
                    # Create card container for the calendar square
                    with st.container(border=True):
                        # Top-right style date header
                        st.markdown(f"<div style='text-align: right; font-weight: bold; font-size: 1.1em; color: #888;'>{date_num}</div>", unsafe_allow_html=True)
                        
                        # Filter classes on this specific date
                        day_classes = filtered_df[filtered_df['Date'] == date_num]
                        
                        if len(day_classes) == 0:
                            st.markdown("<p style='color: #bbb; font-style: italic; text-align: center;'>No classes scheduled</p>", unsafe_allow_html=True)
                        else:
                            for _, course in day_classes.iterrows():
                                # Course Card UI
                                st.markdown(f"**📘 {course['Title']}**")
                                st.markdown(f"🕒 {course['StartTime']} - {course['EndTime']}")
                                st.markdown(f"📍 *{course['Location']}*")
                                
                                # Enroll Button Link
                                enroll_url = course['InPersonLink']
                                if pd.notna(enroll_url):
                                    st.markdown(
                                        f'<a href="{enroll_url}" target="_blank" style="'
                                        f'display: inline-block; width: 100%; text-align: center; '
                                        f'background-color: #1f4e79; color: white; padding: 4px; '
                                        f'border-radius: 4px; text-decoration: none; font-size: 0.9em; '
                                        f'margin-bottom: 12px; transition: 0.3s;">🔗 Enroll</a>',
                                        unsafe_allow_html=True
                                    )
                                st.markdown("<hr style='margin: 8px 0; border: none; border-top: 1px dashed #ddd;' />", unsafe_allow_html=True)
                else:
                    st.write("") # Empty filler space for invalid weekday dates at the end of the month

# Summary of clean dataset below calendar
with st.expander("📊 View Data Details"):
    if df_clean is not None:
        st.dataframe(df_clean, use_container_width=True)
