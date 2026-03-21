import streamlit as st
from ai_engine import ai_risk_analysis
import pandas as pd
import random
from database import Session, Shipment
from risk_engine import calculate_risk

st.set_page_config(page_title="Risk Scanner", layout="centered")

st.title("🚨 Smart Risk Scanner PRO")
st.subheader("📂 Upload Shipment File")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.write("### Uploaded Data")
    st.dataframe(df)

    # AI analysis
    df["AI Risk Score"] = df.apply(ai_risk_analysis, axis=1)

    st.write("### AI Analysis Result")
    st.dataframe(df)

    st.write("### Risk Distribution")
    st.bar_chart(df["AI Risk Score"])
session = Session()
def ai_risk_analysis(row):
    score = 0

    if row.get("Country") in ["Colombia", "Afghanistan", "Unknown"]:
        score += 30

    if row.get("Hour", 12) < 6:
        score += 20

    if row.get("Weight", 0) > 5000 or row.get("Weight", 0) < 50:
        score += 20

    if row.get("Company") not in ["DHL", "Maersk", "FedEx"]:
        score += 15

    score += random.randint(0, 15)

    return min(score, 100)
st.subheader("➕ Add Shipment")

country = st.selectbox("Country", ["Netherlands", "Colombia", "Germany", "Unknown"])
weight = st.number_input("Weight", min_value=1)
route = st.selectbox("Route", ["Normal", "Unusual"])
company = st.selectbox("Company", ["Known", "New"])

if st.button("Analyze & Save"):
    score = calculate_risk(country, weight, route, company)

    shipment = Shipment(
        country=country,
        weight=weight,
        route=route,
        company=company,
        risk_score=score
    )

    session.add(shipment)
    session.commit()

    st.success(f"Saved with Risk Score: {score}")

st.subheader("📊 All Shipments")

data = session.query(Shipment).all()

if data:
    for d in data:
        st.write(f"{d.country} | {d.weight}kg | Score: {d.risk_score}")
else:
    st.info("No shipments yet")
