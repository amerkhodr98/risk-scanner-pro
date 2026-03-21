import streamlit as st
import pandas as pd
import random
import os
from database import Session, Shipment
from sklearn.ensemble import IsolationForest

st.set_page_config(page_title="Smart Risk Scanner", layout="wide")

# ==============================
# LOGIN (WORKING VERSION)
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
# AI ENGINE
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
# ML ENGINE
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
# MAIN UI
# ==============================
st.title("🚨 Smart Risk Scanner PRO")
st.markdown("AI + ML shipment analysis system")

session = Session()

# ==============================
# FILE UPLOAD
# ==============================
st.subheader("📂 Upload Shipment File")

file = st.file_uploader("Upload CSV", type=["csv"])

if file:
    df = pd.read_csv(file)

    required = ["Country", "Weight", "Route", "Company", "Hour"]

    if all(col in df.columns for col in required):
        df.fillna(0, inplace=True)

        df["AI Risk"] = df.apply(ai_risk_analysis, axis=1)
        df = ml_anomaly_detection(df)

        df["Final Risk"] = (df["AI Risk"] * 0.6 + df["ML Risk"] * 0.4).astype(int)

        st.success("Analysis done")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total", len(df))
        col2.metric("High Risk", (df["Final Risk"] > 70).sum())
        col3.metric("Average", int(df["Final Risk"].mean()))

        threshold = st.slider("Filter Risk", 0, 100, 50)
        df_filtered = df[df["Final Risk"] >= threshold]

        st.dataframe(df_filtered, use_container_width=True)
        st.bar_chart(df_filtered["Final Risk"])

        csv = df_filtered.to_csv(index=False).encode()
        st.download_button("Download CSV", csv, "results.csv")

    else:
        st.error("Wrong file format")

# ==============================
# MANUAL INPUT
# ==============================
st.subheader("🧠 Manual Input")

col1, col2 = st.columns(2)

with col1:
    country = st.text_input("Country")
    company = st.text_input("Company")
    route = st.selectbox("Route", ["Normal", "Unusual"])

with col2:
    weight = st.number_input("Weight", min_value=1)
    hour = st.slider("Hour", 0, 23, 12)

if st.button("Analyze & Save"):
    data = pd.DataFrame([{
        "Country": country,
        "Weight": weight,
        "Route": route,
        "Company": company,
        "Hour": hour
    }])

    data["AI Risk"] = data.apply(ai_risk_analysis, axis=1)
    data = ml_anomaly_detection(data)

    final = int(data["AI Risk"][0] * 0.6 + data["ML Risk"][0] * 0.4)

    st.success(f"Risk Score: {final}/100")

    shipment = Shipment(
        country=country,
        weight=weight,
        route=route,
        company=company,
        risk_score=final
    )

    session.add(shipment)
    session.commit()

# ==============================
# DATABASE VIEW
# ==============================
st.subheader("📊 Stored Data")

data = session.query(Shipment).all()

if data:
    df_db = pd.DataFrame([{
        "Country": d.country,
        "Weight": d.weight,
        "Route": d.route,
        "Company": d.company,
        "Risk": d.risk_score
    } for d in data])

    search = st.text_input("Search")

    if search:
        df_db = df_db[df_db.apply(lambda x: search.lower() in str(x).lower(), axis=1)]

    st.dataframe(df_db, use_container_width=True)
else:
    st.info("No data yet")

