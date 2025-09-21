import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Water Assets Dashboard",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('assets_expanded_yes_no.csv')

df = load_data()

# Convert date columns to datetime
df['last_survey_date'] = pd.to_datetime(df['last_survey_date'])

# Sidebar filters
st.sidebar.title('🔍 Filters')

# State filter
state_list = ['All'] + sorted(df['state'].unique().tolist())
selected_state = st.sidebar.selectbox('Select State', state_list, index=0)

# District filter (dynamic based on state)
district_list = ['All']
if selected_state != 'All':
    district_list += sorted(df[df['state'] == selected_state]['district'].unique().tolist())
selected_district = st.sidebar.selectbox('Select District', district_list, index=0)

# Asset type filter
asset_types = ['All'] + sorted(df['asset_type'].unique().tolist())
selected_asset_type = st.sidebar.multiselect('Select Asset Type', asset_types, default=['All'])

# Status filter
statuses = ['All'] + sorted(df['status'].unique().tolist())
selected_status = st.sidebar.multiselect('Select Status', statuses, default=['All'])

# Date range filter
min_date = df['last_survey_date'].min().date()
max_date = df['last_survey_date'].max().date()
date_range = st.sidebar.date_input(
    'Select Date Range',
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df.copy()

if selected_state != 'All':
    filtered_df = filtered_df[filtered_df['state'] == selected_state]
    
if selected_district != 'All':
    filtered_df = filtered_df[filtered_df['district'] == selected_district]
    
if 'All' not in selected_asset_type:
    filtered_df = filtered_df[filtered_df['asset_type'].isin(selected_asset_type)]
    
if 'All' not in selected_status:
    filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]

# Filter by date range
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_df = filtered_df[
        (filtered_df['last_survey_date'] >= start_date) & 
        (filtered_df['last_survey_date'] <= end_date)
    ]

# Main dashboard
st.title('💧 Water Assets Management Dashboard')
st.markdown("""
This dashboard provides insights into water assets across different regions. 
Use the filters in the sidebar to explore the data.
""")

# KPI Cards
st.subheader('📊 Key Performance Indicators')
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Assets", len(filtered_df))
    
with col2:
    st.metric("Total Area (ha)", f"{filtered_df['area_ha'].sum():,.2f}")
    
with col3:
    avg_ndvi = filtered_df['ndvi'].mean()
    st.metric("Average NDVI", f"{avg_ndvi:.3f}")
    
with col4:
    avg_ndwi = filtered_df['ndwi'].mean()
    st.metric("Average NDWI", f"{avg_ndwi:.3f}")

# Row 1: Asset Distribution and Status
st.subheader('📈 Asset Distribution')
col1, col2 = st.columns(2)

with col1:
    # Asset type distribution
    asset_dist = filtered_df['asset_type'].value_counts().reset_index()
    asset_dist.columns = ['Asset Type', 'Count']
    fig1 = px.pie(asset_dist, values='Count', names='Asset Type', 
                 title='Asset Type Distribution', hole=0.4)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Status distribution
    status_dist = filtered_df['status'].value_counts().reset_index()
    status_dist.columns = ['Status', 'Count']
    fig2 = px.bar(status_dist, x='Status', y='Count', color='Status',
                 title='Asset Status Distribution', text_auto=True)
    st.plotly_chart(fig2, use_container_width=True)

# Row 2: Time Series and NDVI/NDWI
st.subheader('📅 Temporal Analysis')
col1, col2 = st.columns(2)

with col1:
    # Assets by month
    monthly_assets = filtered_df.set_index('last_survey_date').resample('M').size()
    fig3 = px.line(monthly_assets, x=monthly_assets.index, y=0,
                  labels={'0': 'Number of Assets', 'last_survey_date': 'Date'},
                  title='Assets Added Over Time')
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    # NDVI vs NDWI scatter plot
    fig4 = px.scatter(filtered_df, x='ndvi', y='ndwi', color='asset_type',
                     title='NDVI vs NDWI by Asset Type',
                     labels={'ndvi': 'NDVI', 'ndwi': 'NDWI'},
                     hover_data=['asset_name', 'state', 'district'])
    st.plotly_chart(fig4, use_container_width=True)

# Row 3: State/District Analysis
st.subheader('🌍 Geographic Analysis')
col1, col2 = st.columns(2)

with col1:
    # Top states by asset count
    state_assets = filtered_df['state'].value_counts().reset_index()
    state_assets.columns = ['State', 'Count']
    fig5 = px.bar(state_assets.head(10), x='Count', y='State', orientation='h',
                 title='Top 10 States by Asset Count', text_auto=True)
    st.plotly_chart(fig5, use_container_width=True)

with col2:
    # Asset type by state heatmap
    if len(filtered_df) > 0:
        state_asset_type = pd.crosstab(filtered_df['state'], filtered_df['asset_type'])
        fig6 = px.imshow(state_asset_type, labels=dict(x="Asset Type", y="State", color="Count"),
                        title='Asset Type Distribution by State',
                        aspect="auto")
        st.plotly_chart(fig6, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

# Raw data table
expander = st.expander("View Raw Data")
with expander:
    st.dataframe(filtered_df, use_container_width=True)
    
    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='filtered_water_assets.csv',
        mime='text/csv',
    )

# Add some styling
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stMetricValue {
        font-size: 1.2rem;
    }
    .stMetricLabel {
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# Add footer
st.markdown("---")
st.markdown("### About")
st.markdown("""
This dashboard provides insights into water assets across different regions. 
- **NDVI (Normalized Difference Vegetation Index)**: Measures vegetation health (values range from -1 to 1).
- **NDWI (Normalized Difference Water Index)**: Measures water content (values range from -1 to 1).

Data is filtered based on your selections in the sidebar.
""")
