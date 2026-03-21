import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
from database import Session, Shipment, init_db
from sklearn.ensemble import IsolationForest

st.set_page_config(page_title="Smart Risk Scanner", layout="wide")

# INIT DATABASE
init_db()

# ==============================
# LOGIN
# ==============================
PASSWORD = os.getenv("APP_PASSWORD", "admin123")

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Secure Access")

    pwd = st.text_input("Enter password", type="password")

    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Wrong password")

    st.stop()

# ==============================
# AI
# ==============================
def ai_risk_analysis(row):
    score = 0

    country = str(row.get("Country", "")).lower()
    company = str(row.get("Company", "")).lower()
    route = str(row.get("Route", "")).lower()
    weight = float(row.get("Weight", 0))
    hour = int(row.get("Hour", 12))

    if country in ["colombia", "afghanistan", "mexico", "unknown"]:
        score += 30

    if hour < 5 or hour > 22:
        score += 20

    if weight < 50 or weight > 5000:
        score += 20

    if route == "unusual":
        score += 15

    if company not in ["dhl", "maersk", "fedex", "ups"]:
        score += 15

    score += random.randint(0, 10)

    return min(score, 100)

# ==============================
# ML
# ==============================
def ml_anomaly_detection(df):
    try:
        model = IsolationForest(contamination=0.2, random_state=42)
        df["ML"] = model.fit_predict(df[["Weight", "Hour"]])
        df["ML Risk"] = df["ML"].apply(lambda x: 100 if x == -1 else 20)
    except:
        df["ML Risk"] = 0
    return df

# ==============================
# MAIN
# ==============================
st.title("🚨 Smart Risk Scanner PRO")

session = Session()

# ==============================
# FILE UPLOAD
# ==============================
st.subheader("📂 Upload CSV")

file = st.file_uploader("Upload file", type=["csv"])

if file:
    df = pd.read_csv(file)

    required = ["Country", "Weight", "Route", "Company", "Hour"]

    if all(col in df.columns for col in required):
        df.fillna(0, inplace=True)

        df["AI Risk"] = df.apply(ai_risk_analysis, axis=1)
        df = ml_anomaly_detection(df)

        df["Final Risk"] = (df["AI Risk"] * 0.6 + df["ML Risk"] * 0.4).astype(int)

        st.dataframe(df)
        st.bar_chart(df["Final Risk"])

    else:
        st.error("Wrong file format")

# ==============================
# MANUAL INPUT
# ==============================
st.subheader("🧠 Manual Entry")

col1, col2 = st.columns(2)

with col1:
    country = st.text_input("Country")
    company = st.text_input("Company")
    route = st.selectbox("Route", ["Normal", "Unusual"])
    vehicle_id = st.text_input("Vehicle / Plate")

with col2:
    weight = st.number_input("Weight", min_value=1)
    hour = st.slider("Hour", 0, 23, 12)
    notes = st.text_area("Notes")

if st.button("Analyze & Save"):
    df_manual = pd.DataFrame([{
        "Country": country,
        "Weight": weight,
        "Route": route,
        "Company": company,
        "Hour": hour
    }])

    df_manual["AI Risk"] = df_manual.apply(ai_risk_analysis, axis=1)
    df_manual = ml_anomaly_detection(df_manual)

    final = int(df_manual["AI Risk"][0] * 0.6 + df_manual["ML Risk"][0] * 0.4)

    st.success(f"🚨 Risk Score: {final}/100")

    shipment = Shipment(
        country=country,
        company=company,
        route=route,
        weight=weight,
        hour=hour,
        risk_score=final,
        vehicle_id=vehicle_id,
        notes=notes,
        timestamp=str(datetime.now())
    )

    session.add(shipment)
    session.commit()

# ==============================
# VEHICLE TRACKING
# ==============================
st.subheader("🚗 Vehicle Intelligence")

search = st.text_input("Search Plate")

if search:
    data = session.query(Shipment).filter(Shipment.vehicle_id == search).all()

    if data:
        st.metric("Visits", len(data))
        st.metric("Last Seen", data[-1].timestamp)

        df_track = pd.DataFrame([{
            "Country": d.country,
            "Company": d.company,
            "Risk": d.risk_score,
            "Time": d.timestamp,
            "Notes": d.notes
        } for d in data])

        st.dataframe(df_track)
    else:
        st.warning("No data found")

# ==============================
# DATABASE VIEW
# ==============================
st.subheader("📊 All Shipments")

data = session.query(Shipment).all()

if data:
    df_all = pd.DataFrame([{
        "Plate": d.vehicle_id,
        "Country": d.country,
        "Company": d.company,
        "Risk": d.risk_score,
        "Time": d.timestamp
    } for d in data])

    st.dataframe(df_all)
else:
    st.info("No data yet")
