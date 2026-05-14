import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# PAGE CONFIGURATION
st.set_page_config(page_title="Dozee Command Center", layout="wide", initial_sidebar_state="expanded")

# MOCK DATA
# This simulates the real-time Speed Layer and batch historical data
patient_data = [
    {"bed": "Bed 402", "status": "High Risk", "mews": 8.5, "hr": 115, "rr": 28, "spo2": 89, "readmission": 78, "action": "Page ICU Rapid Response Team"},
    {"bed": "Bed 403", "status": "Moderate Risk", "mews": 5.2, "hr": 95, "rr": 20, "spo2": 94, "readmission": 45, "action": "Auto-reroute nearest floor nurse"},
    {"bed": "Bed 404", "status": "Stable", "mews": 2.1, "hr": 72, "rr": 14, "spo2": 98, "readmission": 12, "action": "Maintain routine 4-hourly check"},
    {"bed": "Bed 405", "status": "Stable", "mews": 1.5, "hr": 68, "rr": 16, "spo2": 99, "readmission": 8, "action": "Maintain routine 4-hourly check"}
]
df = pd.DataFrame(patient_data)

# SIDEBAR AND ROUTING TOGGLE
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Medical_cross_symbol.svg/200px-Medical_cross_symbol.svg.png", width=50)
st.sidebar.title("Acuity Controls")
st.sidebar.markdown("---")

# Solves Reactive Resource Allocation by filtering out stable patients
dynamic_routing = st.sidebar.toggle("Activate Acuity-Based Routing", value=False)

if dynamic_routing:
    display_df = df[df['status'] != 'Stable']
    st.sidebar.success("Routing Active: Stable patients hidden. Resources optimized.")
else:
    display_df = df

st.sidebar.markdown("---")
st.sidebar.subheader("Unified Patient View")

# Solves Fragmented Data by allowing a deep dive into one patient
selected_bed = st.sidebar.selectbox("Select Patient for Deep Dive", df['bed'].tolist())

# MAIN DASHBOARD AREA
st.title("Smart Healthcare Command Center")
st.markdown("Real-time predictive intelligence powered by Dozee continuous monitoring.")
st.markdown("---")

# ACUITY GRID
st.subheader("Ward Acuity Overview")
cols = st.columns(len(display_df))

for index, row in display_df.reset_index().iterrows():
    with cols[index]:
        # Dynamic styling based on MEWS score
        if row['status'] == "High Risk":
            color = "red"
        elif row['status'] == "Moderate Risk":
            color = "orange"
        else:
            color = "green"
            
        st.markdown(f"""
        <div style="border-top: 5px solid {color}; padding: 15px; border-radius: 5px; background-color: #1e1e1e; box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
            <h3 style="margin-top:0px;">{row['bed']}</h3>
            <p><strong>Status:</strong> <span style="color:{color};">{row['status']}</span></p>
            <p><strong>MEWS Score:</strong> {row['mews']}</p>
            <p><em>{row['action']}</em></p>
        </div>
        <br>
        """, unsafe_allow_html=True)

st.markdown("---")

# UNIFIED PATIENT MODAL 
st.subheader(f"Clinical Deep Dive: {selected_bed}")
patient = df[df['bed'] == selected_bed].iloc[0]

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("#### Real-Time Vitals (Speed Layer)")
    v1, v2, v3 = st.columns(3)
    v1.metric("Heart Rate", f"{patient['hr']} bpm", delta="High" if patient['hr'] > 100 else "Normal", delta_color="inverse")
    v2.metric("Resp Rate", f"{patient['rr']} /min", delta="High" if patient['rr'] > 20 else "Normal", delta_color="inverse")
    v3.metric("SpO2", f"{patient['spo2']} %", delta="Low" if patient['spo2'] < 95 else "Normal", delta_color="inverse")

with col2:
    st.markdown("#### 30-Day Readmission Risk (Batch Layer)")
    # Solves the Readmission Blind Spot using a Gauge Chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = patient['readmission'],
        domain = {{'x': [0, 1], 'y': [0, 1]}},
        title = {{'text': "Risk Probability %"}},
        gauge = {{'axis': {{'range': [None, 100]}},
                 'bar': {{'color': "white"}},
                 'steps': [
                     {{'range': [0, 30], 'color': "green"}},
                     {{'range': [30, 70], 'color': "orange"}},
                     {{'range': [70, 100], 'color': "red"}}]}}
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)
