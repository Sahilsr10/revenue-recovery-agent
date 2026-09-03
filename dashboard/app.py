import sys
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(layout="wide", page_title="Revenue Recovery Agent — Dashboard")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT_CSV_PATH = os.path.join(PROJECT_ROOT, "audit_log.csv")

def load_data():
    if not os.path.exists(AUDIT_CSV_PATH):
        return None
    return pd.read_csv(AUDIT_CSV_PATH)

st.title("Revenue Recovery Agent — Dashboard")

df = load_data()

if df is None:
    st.warning("No data found! Please run the pipeline first.")
else:
    # Sidebar filters
    st.sidebar.header("Filters")
    root_causes = st.sidebar.multiselect("Root Cause", options=df["root_cause"].unique())
    outcomes = st.sidebar.multiselect("Outcome", options=df["outcome"].unique())
    
    filtered_df = df.copy()
    if root_causes:
        filtered_df = filtered_df[filtered_df["root_cause"].isin(root_causes)]
    if outcomes:
        filtered_df = filtered_df[filtered_df["outcome"].isin(outcomes)]
        
    # Metrics
    total_at_risk = filtered_df["amount"].sum()
    total_recovered = filtered_df["recovered_amount"].sum()
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Revenue at Risk", f"₹{total_at_risk:,.0f}")
    col2.metric("Revenue Recovered", f"₹{total_recovered:,.0f}")
    col3.metric("Recovery Rate", f"{recovery_rate:.1f}%")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Events by Root Cause")
        pie_data = filtered_df["root_cause"].value_counts().reset_index()
        pie_data.columns = ["root_cause", "count"]
        fig_pie = px.pie(pie_data, names="root_cause", values="count", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.subheader("Recovered vs At-Risk by Root Cause")
        bar_data = filtered_df.groupby("root_cause").agg({"amount": "sum", "recovered_amount": "sum"}).reset_index()
        fig_bar = go.Figure(data=[
            go.Bar(name='At Risk', x=bar_data['root_cause'], y=bar_data['amount']),
            go.Bar(name='Recovered', x=bar_data['root_cause'], y=bar_data['recovered_amount'])
        ])
        fig_bar.update_layout(barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)
        
    # Table
    st.subheader("Audit Trail")
    st.dataframe(filtered_df)
    
    # Case Studies
    st.header("🔍 Case Studies: What Broke and How We Handled It")
    
    recovered_cases = filtered_df[filtered_df["outcome"] == "recovered"]
    escalated_cases = filtered_df[filtered_df["outcome"] == "escalated"]
    
    if not recovered_cases.empty and not escalated_cases.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Case 1: Successful Recovery")
            case_rec = recovered_cases.iloc[0]
            with st.expander(f"Event ID: {case_rec['event_id']}"):
                st.write(f"**Customer ID:** {case_rec['customer_id']}")
                st.write(f"**Root Cause:** {case_rec['root_cause']}")
                st.write(f"**Amount:** ₹{case_rec['amount']:,.0f}")
                st.write(f"**Action Taken:** {case_rec['action_taken']}")
                st.write(f"**Message Sent:** {case_rec['message_sent']}")
                st.write(f"**Outcome:** {case_rec['outcome']}")
                
        with col2:
            st.subheader("Case 2: Escalation to Human")
            case_esc = escalated_cases.iloc[0]
            with st.expander(f"Event ID: {case_esc['event_id']}"):
                st.write(f"**Customer ID:** {case_esc['customer_id']}")
                st.write(f"**Root Cause:** {case_esc['root_cause']}")
                st.write(f"**Amount:** ₹{case_esc['amount']:,.0f}")
                st.write(f"**Action Taken:** {case_esc['action_taken']}")
                st.write(f"**Message Sent:** {case_esc['message_sent']}")
                st.write(f"**Outcome:** {case_esc['outcome']}")
    else:
        st.info("Not enough data for case studies.")
