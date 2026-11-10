import html
import io
import os
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Page Configuration
st.set_page_config(
    page_title="Learn@TLC - Training Calendar",
    page_icon="📅",
    layout="wide"
)

# 1. Custom Brand Banner
BANNER_FILE = "LearnTLC_.png"
if os.path.exists(BANNER_FILE):
    st.image(BANNER_FILE, use_container_width=True)
else:
    st.title("Learn @ TLC")
    st.subheader("Training & Course Schedule")

st.markdown("---")

# 2. Data Ingestion & Sanitization
@st.cache_data
def load_and_clean_data(file_source) -> pd.DataFrame:
    """Loads CSV and filters out corrupted spreadsheet formulas and blank rows."""
    df = pd.read_csv(file_source)
    
    # Drop rows missing primary scheduling metadata
    df = df.dropna(subset=['Date', 'Title', 'StartTime', 'EndTime'])
    
    # Strip Excel error artifacts (#VALUE!, #REF!, etc.)
    df = df[~df['Date'].astype(str).str.contains('#')]
    df = df[~df['Title'].astype(str).str.contains('#')]
    
    # Standardize data types
    df['Date'] = pd.to_numeric(df['Date'], errors='coerce').fillna(0).astype(int)
    df = df[df['Date'] > 0]
    
    return df.sort_values(by=['Date', 'StartTime'])

# 3. PDF Compilation Engine (ReportLab)
def generate_calendar_pdf(df: pd.DataFrame) -> io.BytesIO:
    """Assembles a high-resolution landscape calendar with active enrollment links."""
    pdf_buffer = io.BytesIO()
    
    # Landscape Letter (792 x 612 pt) with 18 pt margins (756 pt printable width)
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(letter),
        leftMargin=18,
        rightMargin=18,
        topMargin=20,
        bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=15, leading=17, textColor=colors.HexColor('#1f4e79'), alignment=1)
    day_header_style = ParagraphStyle('DayHeader', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=colors.white, alignment=1)
    date_num_style = ParagraphStyle('DateNum', parent=styles['Normal'], fontSize=8.5, leading=10, fontName='Helvetica-Bold', textColor=colors.HexColor('#555555'), alignment=2)
    course_name_style = ParagraphStyle('CourseName', parent=styles['Normal'], fontSize=7, leading=8.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#1f4e79'))
    course_meta_style = ParagraphStyle('CourseMeta', parent=styles['Normal'], fontSize=6, leading=7.5, textColor=colors.HexColor('#333333'))
    link_style = ParagraphStyle('LinkStyle', parent=styles['Normal'], fontSize=6, leading=7.5, textColor=colors.HexColor('#0056b3'))
    empty_cell_style = ParagraphStyle('EmptyCell', parent=styles['Normal'], fontSize=6, leading=7, textColor=colors.HexColor('#cccccc'), alignment=1)
    
    elements = [
        Paragraph("Learn@TLC - Course Training Calendar", title_style),
        Spacer(1, 8)
    ]
    
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    table_data = [[Paragraph(day, day_header_style) for day in weekdays]]
    
    # Monday-Friday week allocations
    calendar_weeks = [
        [2, 3, 4, 5, 6],
        [9, 10, 11, 12, 13],
        [16, 17, 18, 19, 20],
        [23, 24, 25, 26, 27],
        [30, 31, None, None, None]
    ]
    
    for week in calendar_weeks:
        row_cells = []
        for day in week:
            cell_content = []
            if day is not None:
                cell_content.append(Paragraph(str(day), date_num_style))
                cell_content.append(Spacer(1, 2))
                
                day_classes = df[df['Date'] == day]
                if not day_classes.empty:
                    for _, course in day_classes.iterrows():
                        safe_title = html.escape(str(course['Title']))
                        safe_loc = html.escape(str(course['Location']))
                        safe_time = f"{course['StartTime']} - {course['EndTime']}"
                        
                        cell_content.append(Paragraph(safe_title, course_name_style))
                        cell_content.append(Paragraph(f"{safe_time} | {safe_loc}", course_meta_style))
                        
                        enroll_link = course.get('InPersonLink')
                        if pd.notna(enroll_link) and str(enroll_link).startswith("http"):
                            # Clickable PDF URI anchor
                            cell_content.append(Paragraph(f'<a href="{enroll_link}"><u>Enroll Now &rarr;</u></a>', link_style))
                        cell_content.append(Spacer(1, 3))
                else:
                    cell_content.append(Paragraph("&nbsp;", empty_cell_style))
            else:
                cell_content.append(Paragraph("&nbsp;", empty_cell_style))
            
            row_cells.append(cell_content)
        table_data.append(row_cells)
    
    # 756 pt width distributed across 5 equal columns (151.2 pt each)
    cal_table = Table(table_data, colWidths=[151.2] * 5)
    cal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1f4e79')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    
    elements.append(cal_table)
    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

# 4. Source Data Resolution
default_csv = "csv_html.csv"
uploaded_csv = st.sidebar.file_uploader("Upload Calendar CSV", type=["csv"])

if uploaded_csv is not None:
    df_raw = load_and_clean_data(uploaded_csv)
elif os.path.exists(default_csv):
    df_raw = load_and_clean_data(default_csv)
else:
    df_raw = None
    st.warning("⚠️ No dataset located. Upload a training schedule CSV in the sidebar.")

# 5. Application View & Interaction
if df_raw is not None:
    st.sidebar.header("Filter Options")
    search_term = st.sidebar.text_input("🔍 Search Title", "")
    
    available_locs = ["All"] + sorted(df_raw['Location'].dropna().unique().tolist())
    selected_loc = st.sidebar.selectbox("📍 Location", available_locs)
    
    # Apply user filters
    filtered_df = df_raw.copy()
    if search_term:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_term, case=False, na=False)]
    if selected_loc != "All":
        filtered_df = filtered_df[filtered_df['Location'] == selected_loc]
        
    # PDF Download Button
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export")
    pdf_output = generate_calendar_pdf(filtered_df)
    st.sidebar.download_button(
        label="📥 Download Printable PDF",
        data=pdf_output,
        file_name="TLC_Training_Calendar.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
    # Calendar UI Layout
    st.markdown("### 📅 Monthly Schedule")
    
    weekday_labels = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    header_cols = st.columns(5)
    for idx, day_str in enumerate(weekday_labels):
        header_cols[idx].markdown(
            f"<div style='background-color: #1f4e79; color: white; text-align: center; "
            f"font-weight: bold; padding: 6px; border-radius: 4px;'>{day_str}</div>", 
            unsafe_allow_html=True
        )
    
    st.write("")
    
    calendar_weeks = [
        {"name": "Week 1", "days": [2, 3, 4, 5, 6]},
        {"name": "Week 2", "days": [9, 10, 11, 12, 13]},
        {"name": "Week 3", "days": [16, 17, 18, 19, 20]},
        {"name": "Week 4", "days": [23, 24, 25, 26, 27]},
        {"name": "Week 5", "days": [30, 31, None, None, None]}
    ]
    
    for week in calendar_weeks:
        st.markdown(f"### {week['name']}")
        week_cols = st.columns(5)
        
        for c_idx, date_val in enumerate(week["days"]):
            with week_cols[c_idx]:
                if date_val is not None:
                    with st.container(border=True):
                        st.markdown(
                            f"<div style='text-align: right; font-weight: bold; "
                            f"color: #777; font-size: 0.9em;'>{date_val}</div>",
                            unsafe_allow_html=True
                        )
                        
                        classes_today = filtered_df[filtered_df['Date'] == date_val]
                        if classes_today.empty:
                            st.markdown("<p style='color: #ccc; font-style: italic; text-align: center;'>No classes</p>", unsafe_allow_html=True)
                        else:
                            for _, item in classes_today.iterrows():
                                st.markdown(f"**📘 {item['Title']}**")
                                st.caption(f"🕒 {item['StartTime']} - {item['EndTime']}")
                                st.caption(f"📍 {item['Location']}")
                                
                                link = item.get('InPersonLink')
                                if pd.notna(link) and str(link).startswith("http"):
                                    st.markdown(
                                        f'<a href="{link}" target="_blank" style="'
                                        f'display: block; text-align: center; '
                                        f'background-color: #1f4e79; color: white; '
                                        f'padding: 4px; border-radius: 4px; '
                                        f'text-decoration: none; font-size: 0.8em; '
                                        f'margin-top: 4px; margin-bottom: 8px;">🔗 Enroll</a>',
                                        unsafe_allow_html=True
                                    )
                                st.markdown("<hr style='margin: 6px 0; border: none; border-top: 1px dashed #eee;' />", unsafe_allow_html=True)
                else:
                    st.write("")

    with st.expander("📊 Raw Data Inspector"):
        st.dataframe(filtered_df, use_container_width=True)
