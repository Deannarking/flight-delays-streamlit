import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2015 US Flight Delays", layout="wide")

st.title("2015 US Flight Delays & Cancellations Analytics")
st.markdown("**Analytical Question:** Which airlines and airports have the worst delays and cancellations, what causes them, and how do patterns vary by month?")

# ====================== DATA LOADING ======================
@st.cache_data
def load_data():
    try:
        # Try CSV first (recommended)
        df = pd.read_csv("flights_sample.csv")
    except FileNotFoundError:
        # Fallback to Excel if CSV not found
        df = pd.read_excel("Sample_flights.csv.xlsx", sheet_name="Sample_flights")
    
    airlines = pd.read_csv("airlines.csv")
    airports = pd.read_csv("airports.csv")
    
    # Merge airline names
    df = df.merge(airlines, left_on='AIRLINE', right_on='IATA_CODE', how='left')
    df = df.rename(columns={'AIRLINE_x': 'AIRLINE_CODE', 'AIRLINE_y': 'AIRLINE_NAME'})
    
    # Create useful columns
    df['DATE'] = pd.to_datetime(df[['YEAR', 'MONTH', 'DAY']])
    df['MONTH_NAME'] = df['DATE'].dt.strftime('%B')
    
    df['IS_DELAYED'] = (df['ARRIVAL_DELAY'] > 15).astype(int)
    
    return df, airports

df, airports = load_data()

# ====================== FILTERS ======================
st.sidebar.header("Filters")

selected_airlines = st.sidebar.multiselect(
    "Select Airlines",
    options=sorted(df['AIRLINE_NAME'].dropna().unique()),
    default=list(df['AIRLINE_NAME'].dropna().unique())[:6]
)

selected_months = st.sidebar.multiselect(
    "Select Months",
    options=sorted(df['MONTH_NAME'].unique()),
    default=df['MONTH_NAME'].unique()
)

df_filtered = df[
    df['AIRLINE_NAME'].isin(selected_airlines) &
    df['MONTH_NAME'].isin(selected_months)
]

# ====================== KPIs ======================
st.header("Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

total = len(df_filtered)
delay_rate = (df_filtered['IS_DELAYED'].sum() / total * 100) if total > 0 else 0
avg_delay = df_filtered['ARRIVAL_DELAY'].mean()
cancel_rate = (df_filtered['CANCELLED'].sum() / total * 100) if total > 0 else 0

col1.metric("Total Flights", f"{total:,}")
col2.metric("Delay Rate", f"{delay_rate:.1f}%")
col3.metric("Avg Arrival Delay", f"{avg_delay:.1f} min")
col4.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# Charts...
st.header("Visualizations")

col_v1, col_v2 = st.columns(2)

with col_v1:
    avg_delay_by_airline = df_filtered.groupby('AIRLINE_NAME')['ARRIVAL_DELAY'].mean().reset_index().sort_values('ARRIVAL_DELAY', ascending=False)
    fig1 = px.bar(avg_delay_by_airline.head(12), x='AIRLINE_NAME', y='ARRIVAL_DELAY',
                  title="Average Arrival Delay by Airline")
    st.plotly_chart(fig1, use_container_width=True)

with col_v2:
    monthly = df_filtered.groupby('MONTH_NAME')['IS_DELAYED'].mean().reset_index()
    monthly['Delay %'] = monthly['IS_DELAYED'] * 100
    fig2 = px.line(monthly, x='MONTH_NAME', y='Delay %', title="Delay Rate by Month", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

# More charts and findings...
st.success("Dashboard loaded successfully!")

# Raw data + download
st.header("Filtered Data")
st.dataframe(df_filtered.head(1000))

csv = df_filtered.to_csv(index=False).encode()
st.download_button("Download Filtered CSV", csv, "filtered_flights.csv", "text/csv")
