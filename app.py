import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
from database import Session, Shipment, init_db
from sklearn.ensemble import IsolationForest

st.set_page_config(page_title="Smart Risk Scanner", layout="wide")

# INIT DB
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

    if str(row.get("Country", "")).lower() in ["colombia", "afghanistan", "mexico", "unknown"]:
        score += 30

    if int(row.get("Hour", 12)) < 5:
        score += 20

    if float(row.get("Weight", 0)) > 5000:
        score += 20

    if str(row.get("Route", "")).lower() == "unusual":
        score += 15

    score += random.randint(0, 10)

    return min(score, 100)

# ==============================
# ML
# ==============================
def ml(df):
    try:
        model = IsolationForest()
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
# INPUT
# ==============================
country = st.text_input("Country")
company = st.text_input("Company")
vehicle = st.text_input("Vehicle / Plate")
route = st.selectbox("Route", ["Normal", "Unusual"])
weight = st.number_input("Weight", min_value=1)
hour = st.slider("Hour", 0, 23, 12)
notes = st.text_area("Notes")

if st.button("Analyze & Save"):
    df = pd.DataFrame([{
        "Country": country,
        "Weight": weight,
        "Route": route,
        "Company": company,
        "Hour": hour
    }])

    df["AI"] = df.apply(ai_risk_analysis, axis=1)
    df = ml(df)

    final = int(df["AI"][0] * 0.6 + df["ML Risk"][0] * 0.4)

    st.success(f"Risk: {final}")

    try:
        shipment = Shipment(
            country=country,
            company=company,
            route=route,
            weight=weight,
            hour=hour,
            risk_score=final,
            vehicle_id=vehicle,
            notes=notes,
            timestamp=str(datetime.now())
        )

        session.add(shipment)
        session.commit()

    except Exception as e:
        st.error("Database error fixed automatically")
        init_db()

# ==============================
# TRACKING
# ==============================
search = st.text_input("Search vehicle")

if search:
    try:
        data = session.query(Shipment).filter(Shipment.vehicle_id == search).all()

        if data:
            st.metric("Visits", len(data))
            st.metric("Last Seen", data[-1].timestamp)

            for d in data:
                st.write(d.country, d.risk_score, d.timestamp, d.notes)
        else:
            st.warning("No data")

    except:
        init_db()

# ==============================
# ALL DATA
# ==============================
st.subheader("All Data")

try:
    data = session.query(Shipment).all()

    for d in data:
        st.write(d.vehicle_id, d.country, d.risk_score)

except:
    st.error("DB reset")
    init_db()
