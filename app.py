import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Federated Population Health Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for additional styling if needed beyond config.toml
st.markdown("""
<style>
    .success-banner {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .warning-banner {
        padding: 1rem;
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOCK DATA GENERATION
# ------------------------------------------------------------------------------
@st.cache_data
def generate_mock_data():
    np.random.seed(42)
    hospitals = ['Apollo Navi Mumbai', 'Fortis Thane', 'Manipal Kharghar']

    # Generate 7 days of anomaly data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    date_range = pd.date_range(start=start_date, end=end_date, freq='h')

    anomaly_records = []
    patient_records = []

    for hospital in hospitals:
        # Time-series anomaly data
        base_anomalies = np.random.poisson(lam=5, size=len(date_range))
        # Add some random spikes
        spikes = np.random.choice([0, 10, 20], size=len(date_range), p=[0.9, 0.08, 0.02])
        anomalies = base_anomalies + spikes

        for dt, count in zip(date_range, anomalies):
            anomaly_records.append({
                'timestamp': dt,
                'hospital': hospital,
                'anomaly_count': count
            })

        # Patient current status data (approx 100 patients per hospital)
        num_patients = np.random.randint(80, 120)
        for i in range(num_patients):
            hr = np.random.normal(75, 15)
            rr = np.random.normal(16, 4)
            spo2 = np.random.normal(97, 2)

            # Simple MEWS calculation logic for mock data
            mews = 0
            if hr < 40 or hr > 130: mews += 3
            elif hr < 50 or hr > 110: mews += 2
            elif hr > 100: mews += 1

            if rr < 9 or rr > 30: mews += 3
            elif rr > 20: mews += 2
            elif rr > 14: mews += 1

            if spo2 < 89: mews += 3
            elif spo2 < 92: mews += 2
            elif spo2 < 94: mews += 1

            # Cap MEWS at 10 for slider compatibility
            mews = min(mews, 10)

            patient_records.append({
                'patient_id': f"{hospital[:3].upper()}-{np.random.randint(1000, 9999)}",
                'hospital': hospital,
                'hr': round(hr),
                'rr': round(rr),
                'spo2': round(spo2),
                'mews': mews
            })

    df_anomalies = pd.DataFrame(anomaly_records)
    df_patients = pd.DataFrame(patient_records)
    return df_anomalies, df_patients

df_anomalies, df_patients = generate_mock_data()

# ------------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# ------------------------------------------------------------------------------
st.sidebar.title("Data Governance Controls")
st.sidebar.markdown("---")

selected_hospitals = st.sidebar.multiselect(
    "Select Hospital Networks",
    options=['Apollo Navi Mumbai', 'Fortis Thane', 'Manipal Kharghar'],
    default=['Apollo Navi Mumbai', 'Fortis Thane', 'Manipal Kharghar']
)

st.sidebar.markdown("---")
enable_fhir = st.sidebar.toggle("Enable ABDM FHIR Interoperability", value=False)
enable_encryption = st.sidebar.toggle("Activate Homomorphic Encryption", value=False)

st.sidebar.markdown("---")
mews_threshold = st.sidebar.slider(
    "Deterioration Alert Threshold (MEWS)",
    min_value=1, max_value=10, value=5, step=1,
    help="Patients with a MEWS score >= this threshold are classified as High Risk."
)

# ------------------------------------------------------------------------------
# 4. MAIN DASHBOARD COMPONENTS
# ------------------------------------------------------------------------------
st.title("Federated Population Health Dashboard")
st.markdown("A strategic overview of inter-hospital data sharing and patient acuity.")

# Filter data based on selected hospitals
df_anomalies_filtered = df_anomalies[df_anomalies['hospital'].isin(selected_hospitals)].copy()
df_patients_filtered = df_patients[df_patients['hospital'].isin(selected_hospitals)].copy()

# Top Section: Status Banner
if enable_encryption:
    st.markdown('<div class="success-banner">🔒 Zero-Trust Federated Aggregation Active: PII Encrypted</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="warning-banner">⚠️ Warning: Data is siloed and vulnerable. Homomorphic Encryption is OFF.</div>', unsafe_allow_html=True)

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Interoperability Node Map")

    # Create Network Graph
    G = nx.Graph()
    G.add_node("Federated Cloud", pos=(0.5, 0.5), size=40, color="#d2b48c") # Beige accent

    hospital_nodes = {
        'Apollo Navi Mumbai': (0.2, 0.8),
        'Fortis Thane': (0.8, 0.8),
        'Manipal Kharghar': (0.5, 0.2)
    }

    edge_x = []
    edge_y = []

    for idx, (h, pos) in enumerate(hospital_nodes.items()):
        if h in selected_hospitals:
            G.add_node(h, pos=pos, size=30, color="#333333")
            if enable_fhir:
                G.add_edge("Federated Cloud", h)
                x0, y0 = G.nodes["Federated Cloud"]['pos']
                x1, y1 = G.nodes[h]['pos']
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            else:
                # Add broken edges visually by not drawing full lines or drawing dashed
                # We will represent siloed by not adding edges to edge_x/edge_y for plotting
                pass

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []

    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
        node_text.append(node)
        node_color.append(G.nodes[node]['color'])
        node_size.append(G.nodes[node]['size'])

    # Plot Edges
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=3, color='#888'),
        hoverinfo='none',
        mode='lines')

    # Plot Nodes
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        hoverinfo='text',
        text=node_text,
        textposition="top center",
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line_width=2))

    fig_network = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    plot_bgcolor="#faf9f6",
                    paper_bgcolor="#faf9f6"
                 ))

    if not enable_fhir:
        fig_network.add_annotation(
            text="Siloed: No FHIR Connection",
            x=0.5, y=0.9, showarrow=False,
            font=dict(color="red", size=14)
        )

    st.plotly_chart(fig_network, use_container_width=True)

with col2:
    st.subheader("Federated Insights: Acuity Distribution")

    # Calculate Acuity based on slider threshold
    # Rule: Stable < threshold/2, Moderate >= threshold/2 and < threshold, High >= threshold
    # To keep it simple based on the user's implicit "High Risk >= Threshold":
    def categorize_acuity(mews, threshold):
        if mews >= threshold:
            return "High Risk"
        elif mews >= threshold / 2:
            return "Moderate"
        else:
            return "Stable"

    df_patients_filtered['Acuity'] = df_patients_filtered['mews'].apply(lambda x: categorize_acuity(x, mews_threshold))

    acuity_counts = df_patients_filtered.groupby(['hospital', 'Acuity']).size().reset_index(name='Count')

    fig_bar = px.bar(
        acuity_counts,
        x="hospital",
        y="Count",
        color="Acuity",
        title=f"Patient Acuity (Threshold: {mews_threshold})",
        color_discrete_map={
            "Stable": "#a8c6a1", # Soft green
            "Moderate": "#f4d03f", # Soft yellow
            "High Risk": "#e74c3c" # Red
        }
    )
    fig_bar.update_layout(
        plot_bgcolor="#faf9f6",
        paper_bgcolor="#faf9f6",
        font=dict(color="#333333")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.subheader("Predictive Epidemic Radar")

# Aggregate Anomalies
agg_anomalies = df_anomalies_filtered.groupby(['timestamp', 'hospital'])['anomaly_count'].sum().reset_index()

fig_line = px.line(
    agg_anomalies,
    x='timestamp',
    y='anomaly_count',
    color='hospital',
    title="7-Day Aggregated Respiratory Anomalies",
    color_discrete_sequence=['#d2b48c', '#85929e', '#5dade2']
)
fig_line.update_layout(
    plot_bgcolor="#faf9f6",
    paper_bgcolor="#faf9f6",
    font=dict(color="#333333"),
    xaxis_title="Time",
    yaxis_title="Anomaly Count"
)
st.plotly_chart(fig_line, use_container_width=True)
