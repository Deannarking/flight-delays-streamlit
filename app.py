import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2015 US Flight Delays Dashboard", layout="wide")
st.title("2015 US Flight Delays & Cancellations Analytics")
st.markdown("**Analytical Question:** Which airlines and airports have the worst delays and cancellations, what causes them, and how do patterns vary by month?")

# ====================== DATA LOADING ======================
@st.cache_data
def load_data():
    # Load sample data (Excel file)
    df = pd.read_excel("Sample_flights.csv.xlsx", sheet_name="Sample_flights")
    
    # Load lookup tables
    airlines = pd.read_csv("airlines.csv")
    airports = pd.read_csv("airports.csv")
    
    # Merge airline names
    df = df.merge(airlines, left_on='AIRLINE', right_on='IATA_CODE', how='left')
    df = df.rename(columns={'AIRLINE_x': 'AIRLINE_CODE', 'AIRLINE_y': 'AIRLINE_NAME'})
    
    # Create useful columns
    df['DATE'] = pd.to_datetime(df[['YEAR', 'MONTH', 'DAY']])
    df['MONTH_NAME'] = df['DATE'].dt.strftime('%B')
    
    # Delay flags
    df['IS_DELAYED'] = (df['ARRIVAL_DELAY'] > 15).astype(int)
    df['ON_TIME_PCT'] = (df['ARRIVAL_DELAY'] <= 0).astype(int)
    
    return df, airports

df, airports = load_data()

# ====================== SIDEBAR FILTERS ======================
st.sidebar.header("Filters")

selected_airlines = st.sidebar.multiselect(
    "Select Airlines",
    options=sorted(df['AIRLINE_NAME'].dropna().unique()),
    default=df['AIRLINE_NAME'].dropna().unique()[:6]
)

selected_months = st.sidebar.multiselect(
    "Select Months",
    options=sorted(df['MONTH_NAME'].unique()),
    default=df['MONTH_NAME'].unique()
)

# Apply filters
df_filtered = df[
    (df['AIRLINE_NAME'].isin(selected_airlines)) &
    (df['MONTH_NAME'].isin(selected_months))
]

# ====================== KPIs ======================
st.header("Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_flights = len(df_filtered)
delayed_flights = df_filtered['IS_DELAYED'].sum()
delay_rate = (delayed_flights / total_flights * 100) if total_flights > 0 else 0
avg_delay = df_filtered['ARRIVAL_DELAY'].mean()
cancel_rate = (df_filtered['CANCELLED'].sum() / total_flights * 100) if total_flights > 0 else 0

col1.metric("Total Flights", f"{total_flights:,}")
col2.metric("Delay Rate (>15 min)", f"{delay_rate:.1f}%")
col3.metric("Avg Arrival Delay", f"{avg_delay:.1f} min")
col4.metric("Cancellation Rate", f"{cancel_rate:.2f}%")

# ====================== VISUALIZATIONS ======================
st.header("Visualizations")

col_v1, col_v2 = st.columns(2)

# 1. Bar Chart - Avg Delay by Airline
with col_v1:
    avg_delay_airline = df_filtered.groupby('AIRLINE_NAME')['ARRIVAL_DELAY'].mean().reset_index()
    avg_delay_airline = avg_delay_airline.sort_values('ARRIVAL_DELAY', ascending=False)
    fig1 = px.bar(avg_delay_airline.head(12), 
                  x='AIRLINE_NAME', y='ARRIVAL_DELAY',
                  title="Average Arrival Delay by Airline (minutes)",
                  labels={"ARRIVAL_DELAY": "Avg Arrival Delay (min)"})
    st.plotly_chart(fig1, use_container_width=True)

# 2. Line Chart - Delay Rate by Month
with col_v2:
    monthly = df_filtered.groupby('MONTH_NAME')['IS_DELAYED'].mean().reset_index()
    monthly['Delay Rate %'] = monthly['IS_DELAYED'] * 100
    fig2 = px.line(monthly, x='MONTH_NAME', y='Delay Rate %',
                   title="Monthly Flight Delay Rate (%)",
                   markers=True)
    st.plotly_chart(fig2, use_container_width=True)

# 3. Scatter Plot - Distance vs Delay
fig3 = px.scatter(df_filtered.sample(min(3000, len(df_filtered))), 
                  x='DISTANCE', y='ARRIVAL_DELAY',
                  color='AIRLINE_NAME',
                  title="Flight Distance vs Arrival Delay",
                  labels={"DISTANCE": "Distance (miles)", "ARRIVAL_DELAY": "Arrival Delay (min)"})
st.plotly_chart(fig3, use_container_width=True)

# 4. Delay Causes
st.subheader("Delay Causes Breakdown")
cause_cols = ['AIR_SYSTEM_DELAY', 'AIRLINE_DELAY', 'LATE_AIRCRAFT_DELAY', 'WEATHER_DELAY', 'SECURITY_DELAY']
causes = df_filtered[cause_cols].mean().reset_index()
causes.columns = ['Cause', 'Average Minutes']
fig4 = px.pie(causes, names='Cause', values='Average Minutes', 
              title="Average Delay Minutes by Cause")
st.plotly_chart(fig4, use_container_width=True)

# ====================== KEY FINDINGS ======================
st.header("Key Findings")
st.markdown("""
- **Airline Performance**: Low-cost carriers like Spirit (NK) and Frontier (F9) tend to have higher average delays compared to major carriers like Delta and Alaska.
- **Seasonality**: Delays are generally higher in certain months (you will see this clearly in the line chart after filtering).
- **Main Causes**: Late Aircraft Delay and Airline Delay are the biggest contributors to arrival delays, suggesting operational and scheduling improvements could have the highest impact.
""")

# ====================== RAW DATA & DOWNLOAD ======================
st.header("Filtered Raw Data")
st.dataframe(df_filtered.head(1000))

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Filtered Data as CSV",
    data=csv,
    file_name="filtered_flight_delays.csv",
    mime="text/csv"
)

st.caption("Built with Streamlit • Data: USDOT 2015 Flight Delays")
