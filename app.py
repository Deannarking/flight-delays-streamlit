import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="US Flight Delays 2015", layout="wide")
st.title("🛫 2015 US Flight Delays & Cancellations Analytics")
st.markdown("**Analytical Question:** Which U.S. airlines and airports experience the highest flight delays and cancellations, what are the main causes, and how do these patterns vary by month and region?")

# ------------------- Data Loading -------------------
@st.cache_data
def load_data():
    flights = pd.read_csv("Sample_flights.csv")
    airlines = pd.read_csv("airlines.csv")
    airports = pd.read_csv("airports.csv")
    
    # Merge airline names
    flights = flights.merge(airlines, left_on='AIRLINE', right_on='IATA_CODE', how='left')
    flights = flights.rename(columns={'AIRLINE_x': 'AIRLINE_CODE', 'AIRLINE_y': 'AIRLINE_NAME'})
    
    # Create date and month name
    flights['DATE'] = pd.to_datetime(flights[['YEAR', 'MONTH', 'DAY']])
    flights['MONTH_NAME'] = flights['DATE'].dt.strftime('%B')
    
    # Delay flags
    flights['IS_DELAYED'] = (flights['ARRIVAL_DELAY'] > 15).astype(int)
    flights['ON_TIME'] = (flights['ARRIVAL_DELAY'] <= 0).astype(int)  # early or on-time
    
    return flights, airlines, airports

df, airlines_df, airports_df = load_data()

# ------------------- Sidebar Filters (at least 2) -------------------
st.sidebar.header("🔎 Filters")

selected_airlines = st.sidebar.multiselect(
    "Select Airlines",
    options=sorted(df['AIRLINE_NAME'].unique()),
    default=df['AIRLINE_NAME'].unique()[:5]  # start with a few
)

selected_months = st.sidebar.multiselect(
    "Select Months",
    options=sorted(df['MONTH_NAME'].unique()),
    default=df['MONTH_NAME'].unique()
)

# Filter the data
df_filtered = df[
    (df['AIRLINE_NAME'].isin(selected_airlines)) &
    (df['MONTH_NAME'].isin(selected_months))
]

# ------------------- KPIs (at least 3) -------------------
st.header("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

total_flights = len(df_filtered)
delayed_flights = df_filtered['IS_DELAYED'].sum()
delay_pct = (delayed_flights / total_flights * 100) if total_flights > 0 else 0
avg_arr_delay = df_filtered['ARRIVAL_DELAY'].mean()
cancel_pct = (df_filtered['CANCELLED'].sum() / total_flights * 100) if total_flights > 0 else 0

col1.metric("Total Flights", f"{total_flights:,}", delta=None)
col2.metric("Delay Rate (>15 min)", f"{delay_pct:.1f}%", delta=None)
col3.metric("Avg Arrival Delay", f"{avg_arr_delay:.1f} min", delta=None)
col4.metric("Cancellation Rate", f"{cancel_pct:.2f}%", delta=None)

# ------------------- Visualizations (at least 3 different types) -------------------
st.header("📈 Visualizations")

col_chart1, col_chart2 = st.columns(2)

# 1. Bar Chart - Average Delay by Airline
with col_chart1:
    avg_delay_airline = df_filtered.groupby('AIRLINE_NAME')['ARRIVAL_DELAY'].mean().reset_index().sort_values('ARRIVAL_DELAY', ascending=False)
    fig1 = px.bar(avg_delay_airline.head(15), x='AIRLINE_NAME', y='ARRIVAL_DELAY',
                  title="Average Arrival Delay by Airline (minutes)",
                  labels={"ARRIVAL_DELAY": "Avg Arrival Delay (min)"})
    st.plotly_chart(fig1, use_container_width=True)

# 2. Line Chart - Delay Rate by Month
with col_chart2:
    monthly = df_filtered.groupby('MONTH_NAME')['IS_DELAYED'].mean().reset_index()
    monthly['Delay Rate %'] = monthly['IS_DELAYED'] * 100
    fig2 = px.line(monthly, x='MONTH_NAME', y='Delay Rate %',
                   title="Monthly Flight Delay Rate",
                   markers=True)
    st.plotly_chart(fig2, use_container_width=True)

# 3. Scatter Plot - Relationship between Distance and Delay
fig3 = px.scatter(df_filtered.sample(5000), x='DISTANCE', y='ARRIVAL_DELAY',
                  color='AIRLINE_NAME',
                  title="Flight Distance vs Arrival Delay (sample)",
                  labels={"DISTANCE": "Distance (miles)", "ARRIVAL_DELAY": "Arrival Delay (min)"})
st.plotly_chart(fig3, use_container_width=True)

# Optional 4: Delay Causes (Stacked Bar or Pie)
cause_cols = ['AIR_SYSTEM_DELAY', 'AIRLINE_DELAY', 'LATE_AIRCRAFT_DELAY', 'WEATHER_DELAY', 'SECURITY_DELAY']
causes = df_filtered[cause_cols].mean().reset_index()
causes.columns = ['Cause', 'Avg Minutes']
fig4 = px.pie(causes, names='Cause', values='Avg Minutes', title="Average Delay Minutes by Cause")
st.plotly_chart(fig4, use_container_width=True)

# ------------------- Key Findings -------------------
st.header("🔑 Key Findings")
st.markdown("""
- **Finding 1**: [Write your insight here, e.g., "Airlines such as Spirit and Frontier have significantly higher average arrival delays compared to major carriers like Delta and United."]
- **Finding 2**: [e.g., "Delay rates peak in the summer months (June–August), likely due to weather and high travel volume."]
- **Finding 3**: [e.g., "Late aircraft delay is the leading contributor to overall delays, suggesting scheduling and turnaround issues are a key operational bottleneck."]
""")

# Optional: Raw Data Table + Download
st.header("📋 Filtered Data")
st.dataframe(df_filtered.head(1000))

csv = df_filtered.to_csv(index=False).encode('utf-8')
st.download_button("📥 Download Filtered Data as CSV", csv, "filtered_flights.csv", "text/csv")
