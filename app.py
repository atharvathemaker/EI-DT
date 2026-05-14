import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx
from datetime import datetime, timedelta
import json
import random

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Federated Longitudinal Patient Record",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enforce strict minimalist design aesthetic via Custom CSS (complements config.toml)
st.markdown("""
<style>
    .kpi-banner {
        padding: 1.5rem;
        background-color: #f0f0f0;
        border-left: 5px solid #d2b48c;
        border-radius: 0.25rem;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .kpi-item {
        text-align: center;
    }
    .kpi-title {
        font-size: 0.9rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #333;
    }
    .raw-data-box {
        background-color: #f0f0f0;
        padding: 1rem;
        border-radius: 0.25rem;
        font-family: monospace;
        font-size: 0.8rem;
        color: #888;
        height: 200px;
        overflow-y: scroll;
        border: 1px solid #ddd;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. MOCK DATA GENERATION
# ------------------------------------------------------------------------------
@st.cache_data
def generate_patient_history():
    np.random.seed(42)
    random.seed(42)

    hospitals = ['Apollo', 'Fortis', 'Manipal']
    departments = {
        'Apollo': ['Cardiology', 'Internal Medicine'],
        'Fortis': ['Endocrinology', 'Nephrology'],
        'Manipal': ['Emergency', 'General Surgery', 'Orthopedics']
    }

    diagnoses = [
        "Hypertensive crisis", "Type 2 Diabetes follow-up",
        "Chest pain evaluation", "Routine blood work",
        "Minor laceration repair", "Echocardiogram",
        "Renal function test", "A1C monitoring"
    ]

    # Generate 24 visits over the last 3 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)

    visits = []
    for _ in range(24):
        visit_date = start_date + timedelta(days=random.randint(0, 3*365))
        hospital = random.choice(hospitals)
        dept = random.choice(departments[hospital])
        diagnosis = random.choice(diagnoses)
        severity = random.randint(1, 5) # 1 = minor, 5 = severe
        duration_hours = random.randint(1, 48) if severity > 3 else random.randint(1, 4)

        visits.append({
            'date': visit_date,
            'hospital': hospital,
            'department': dept,
            'diagnosis': diagnosis,
            'severity': severity,
            'duration': duration_hours,
            'physician': f"Dr. {random.choice(['Smith', 'Patel', 'Sharma', 'Jones', 'Gupta'])}"
        })

    df_visits = pd.DataFrame(visits).sort_values(by='date').reset_index(drop=True)

    # Scrambled data generator for non-FHIR mode
    def generate_scrambled_json(hospital, n_records=5):
        raw_list = []
        for _ in range(n_records):
            raw_list.append({
                f"sys_{random.randint(100,999)}": f"val_{random.randint(1000,9999)}",
                "hl7_msg_type": "ORU^R01",
                "obx_segment": f"OBX|1|NM|{random.randint(10000,99999)}^UNKNOWN_CODE||{random.random()}||||||F",
                "unstructured_note": "Pt c/o " + "".join(random.choices("abcdefghijklmnopqrstuvwxyz ", k=20))
            })
        return json.dumps({f"{hospital}_raw_dump": raw_list}, indent=2)

    raw_fortis = generate_scrambled_json("Fortis")
    raw_manipal = generate_scrambled_json("Manipal")

    return df_visits, raw_fortis, raw_manipal

df_visits, raw_fortis, raw_manipal = generate_patient_history()

# ------------------------------------------------------------------------------
# 3. SIDEBAR CONTROLS
# ------------------------------------------------------------------------------
st.sidebar.title("Data Governance & Interoperability")
st.sidebar.markdown("---")

active_nodes = st.sidebar.multiselect(
    "Active Data Nodes",
    options=['Apollo', 'Fortis', 'Manipal'],
    default=['Apollo', 'Fortis', 'Manipal']
)

st.sidebar.markdown("---")
enable_fhir = st.sidebar.toggle("FHIR Standard Translation", value=True)

if enable_fhir:
    st.sidebar.success("✅ FHIR active. Data standardized.")
else:
    st.sidebar.error("❌ FHIR inactive. Format mismatch detected.")

# ------------------------------------------------------------------------------
# 4. MAIN DASHBOARD VISUALIZATIONS
# ------------------------------------------------------------------------------

# Filter data based on logic
if enable_fhir:
    # Use all active nodes
    display_df = df_visits[df_visits['hospital'].isin(active_nodes)].copy()
else:
    # Simulate break: only Apollo is mapped properly
    display_df = df_visits[(df_visits['hospital'].isin(active_nodes)) & (df_visits['hospital'] == 'Apollo')].copy()

# --- TOP KPI BANNER ---
node_count = len(display_df['hospital'].unique())
st.markdown(f"""
<div class="kpi-banner">
    <div class="kpi-item">
        <div class="kpi-title">Patient Profile</div>
        <div class="kpi-value">ID: 884-X</div>
    </div>
    <div class="kpi-item">
        <div class="kpi-title">Risk Stratification</div>
        <div class="kpi-value" style="color: #c0392b;">HIGH</div>
    </div>
    <div class="kpi-item">
        <div class="kpi-title">Data Sources</div>
        <div class="kpi-value">{node_count} Active Nodes</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.title("Federated Longitudinal Patient Record")
st.markdown("Unified patient history aggregated from disparate networks using HL7 FHIR.")
st.markdown("---")

# Shared layout settings for strict minimal aesthetic
layout_settings = dict(
    plot_bgcolor="#faf9f6",
    paper_bgcolor="#faf9f6",
    font=dict(color="#333333"),
    margin=dict(t=40, b=40, l=40, r=40)
)
color_map = {
    'Apollo': '#d2b48c',   # Tan/Beige
    'Fortis': '#a9a9a9',   # Dark Grey
    'Manipal': '#d3d3d3'   # Light Grey
}

# --- VISUALIZATION 1: Medical Visits Bubble Chart ---
st.subheader("Frequency of Medical Visits (36 Months)")

if not display_df.empty:
    fig_bubble = px.scatter(
        display_df,
        x="date",
        y="hospital",
        size="severity",
        color="hospital",
        hover_name="diagnosis",
        hover_data=["department", "physician", "duration"],
        color_discrete_map=color_map,
        size_max=30
    )

    fig_bubble.update_layout(
        **layout_settings,
        yaxis_title="Hospital Network",
        xaxis_title="Timeline",
        showlegend=False
    )
    # Minimal gridlines
    fig_bubble.update_xaxes(showgrid=True, gridcolor="#e0e0e0")
    fig_bubble.update_yaxes(showgrid=True, gridcolor="#e0e0e0")

    st.plotly_chart(fig_bubble, use_container_width=True)
else:
    st.warning("No data available to display for selected nodes.")


# --- VISUALIZATION 2: Longitudinal Timeline (Gantt-style) ---
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("Longitudinal Clinical History")

if not display_df.empty:
    # Create a Gantt chart using timeline
    # We add a small duration to make points visible as blocks
    display_df['end_date'] = display_df['date'] + pd.to_timedelta(display_df['duration'], unit='h')

    fig_timeline = px.timeline(
        display_df,
        x_start="date",
        x_end="end_date",
        y="diagnosis",
        color="hospital",
        hover_name="diagnosis",
        hover_data=["hospital", "physician"],
        color_discrete_map=color_map
    )

    fig_timeline.update_layout(
        **layout_settings,
        yaxis=dict(autorange="reversed"), # Top-down chronological feel
        xaxis_title="Timeline",
        yaxis_title="Diagnosis / Event",
        showlegend=True,
        legend_title="Source"
    )
    fig_timeline.update_xaxes(showgrid=True, gridcolor="#e0e0e0")
    fig_timeline.update_yaxes(showgrid=True, gridcolor="#e0e0e0")

    st.plotly_chart(fig_timeline, use_container_width=True)
else:
    st.warning("No clinical history available.")


# --- FALLBACK RAW DATA PANELS (IF FHIR OFF) ---
if not enable_fhir:
    st.markdown("### Unprocessed Legacy Payloads")
    st.markdown("Without FHIR translation, incoming HL7v2/Custom API data from external networks cannot be normalized for longitudinal viewing.")

    col_f, col_m = st.columns(2)
    with col_f:
        if 'Fortis' in active_nodes:
            st.markdown("**Fortis Network (Raw)**")
            st.markdown(f'<div class="raw-data-box">{raw_fortis}</div>', unsafe_allow_html=True)
    with col_m:
        if 'Manipal' in active_nodes:
            st.markdown("**Manipal Network (Raw)**")
            st.markdown(f'<div class="raw-data-box">{raw_manipal}</div>', unsafe_allow_html=True)


# --- VISUALIZATION 3: Family Medical History Pedigree ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("Family Medical History Pedigree")

# Build standard hierarchical tree
G = nx.DiGraph()

# Add Nodes
nodes = {
    "Paternal Grandfather": {"layer": 0, "risk": True, "desc": "Coronary Artery Disease"},
    "Paternal Grandmother": {"layer": 0, "risk": False, "desc": "Healthy"},
    "Maternal Grandfather": {"layer": 0, "risk": True, "desc": "Type 2 Diabetes"},
    "Maternal Grandmother": {"layer": 0, "risk": False, "desc": "Healthy"},
    "Father": {"layer": 1, "risk": True, "desc": "Hypertension"},
    "Mother": {"layer": 1, "risk": True, "desc": "Prediabetic"},
    "Patient 884-X": {"layer": 2, "risk": True, "desc": "High Risk Profile"}
}

for node, attrs in nodes.items():
    G.add_node(node, **attrs)

# Add Edges (Relationships)
G.add_edge("Paternal Grandfather", "Father")
G.add_edge("Paternal Grandmother", "Father")
G.add_edge("Maternal Grandfather", "Mother")
G.add_edge("Maternal Grandmother", "Mother")
G.add_edge("Father", "Patient 884-X")
G.add_edge("Mother", "Patient 884-X")

# Assign static positions for a clean hierarchical look
pos = {
    "Paternal Grandfather": (0.1, 1),
    "Paternal Grandmother": (0.3, 1),
    "Maternal Grandfather": (0.7, 1),
    "Maternal Grandmother": (0.9, 1),
    "Father": (0.2, 0.5),
    "Mother": (0.8, 0.5),
    "Patient 884-X": (0.5, 0)
}

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=2, color='#cccccc'),
    hoverinfo='none',
    mode='lines'
)

node_x = []
node_y = []
node_text = []
node_color = []
line_color = []
line_width = []
hover_text = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(node)
    hover_text.append(f"{node}<br>Status: {G.nodes[node]['desc']}")

    # Minimalist palette: #F5F5DC (Beige) for nodes
    node_color.append("#f5f5dc")

    # Subtle red outline for risks
    if G.nodes[node]['risk']:
        line_color.append("red")
        line_width.append(2)
    else:
        line_color.append("#a9a9a9")
        line_width.append(1)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    hoverinfo='text',
    hovertext=hover_text,
    text=node_text,
    textposition="bottom center",
    marker=dict(
        showscale=False,
        color=node_color,
        size=45,
        line=dict(color=line_color, width=line_width)
    )
)

fig_tree = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=40, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor="#faf9f6",
                paper_bgcolor="#faf9f6",
                font=dict(color="#333333")
             ))

# Pad axes so text isn't cut off
fig_tree.update_xaxes(range=[-0.1, 1.1])
fig_tree.update_yaxes(range=[-0.2, 1.2])

st.plotly_chart(fig_tree, use_container_width=True)
