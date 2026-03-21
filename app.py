import streamlit as st
import pandas as pd
import random
import os
from database import Session, Shipment

# ML
from sklearn.ensemble import IsolationForest

st.set_page_config(page_title="Smart Risk Scanner", layout="wide")

# ==============================
# BASIC SECURITY (env + fallback)
# ==============================
PASSWORD = os.getenv("APP_PASSWORD", "admin123")

def login():
    st.title("🔐 Secure Access")
    pwd = st.text_input("Enter password", type="password")
    if pwd == PASSWORD:
        st.session_state["auth"] = True
    else:
        st.warning("Enter correct password")

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login()
    st.stop()

# ==============================
# AI ENGINE (rule-based)
# ==============================
def ai_risk_analysis(row):
    score = 0

    country = str(row.get("Country", "")).lower()
    company = str(row.get("Company", "")).lower()
    route = str(row.get("Route", "")).lower()
    weight = float(row.get("Weight", 0))
    hour = int(row.get("Hour", 12))

    high_risk_countries = ["colombia", "afghanistan", "mexico", "unknown", "brazil"]

    if country in high_risk_countries:
        score += 30

    if hour < 5 or hour > 22:
        score += 20

    if weight < 50 or weight > 5000:
        score += 20

    if route == "unusual":
        score += 15

    trusted_companies = ["dhl", "maersk", "fedex", "ups"]
    if company not in trusted_companies:
        score += 15

    score += random.randint(0, 10)

    return min(score, 100)

# ==============================
# ML ENGINE (anomaly detection)
# ==============================
def ml_anomaly_detection(df):
    try:
        features = df[["Weight", "Hour"]].fillna(0)

        model = IsolationForest(contamination=0.2, random_state=42)
        preds = model.fit_predict(features)

        df["ML Anomaly"] = preds
        df["ML Risk"] = df["ML Anomaly"].apply(lambda x: 100 if x == -1 else 20)

    except Exception as e:
        df["ML Risk"] = 0

    return df

# ==============================
# HEADER
# ==============================
st.title("🚨 Smart Risk Scanner PRO")
st.markdown("AI + ML powered shipment risk analysis system")

session = Session()

# ==============================
# FILE UPLOAD
# ==============================
st.subheader("📂 Upload Shipment File")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        required_cols = ["Country", "Weight", "Route", "Company", "Hour"]

        if not all(col in df.columns for col in required_cols):
            st.error("File must contain: Country, Weight, Route, Company, Hour")
        else:
            df.fillna(0, inplace=True)

            # AI + ML
            df["AI Risk Score"] = df.apply(ai_risk_analysis, axis=1)
            df = ml_anomaly_detection(df)

            # Combined score
            df["Final Risk Score"] = (df["AI Risk Score"] * 0.6 + df["ML Risk"] * 0.4).astype(int)

            st.success("Analysis completed")

            # KPI
            colA, colB, colC = st.columns(3)
            colA.metric("Total Shipments", len(df))
            colB.metric("High Risk", (df["Final Risk Score"] > 70).sum())
            colC.metric("Avg Risk", int(df["Final Risk Score"].mean()))

            # FILTER
            threshold = st.slider("Filter by Risk Score", 0, 100, 50)
            filtered_df = df[df["Final Risk Score"] >= threshold]

            st.dataframe(filtered_df, use_container_width=True)

            # Charts
            st.bar_chart(filtered_df["Final Risk Score"])

            # Download
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download Results", csv, "analysis.csv", "text/csv")

    except Exception as e:
        st.error("Invalid file format")

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
    data = {
        "Country": country,
        "Weight": weight,
        "Route": route,
        "Company": company,
        "Hour": hour
    }

    df_manual = pd.DataFrame([data])

    df_manual["AI Risk Score"] = df_manual.apply(ai_risk_analysis, axis=1)
    df_manual = ml_anomaly_detection(df_manual)

    final_score = int(df_manual["AI Risk Score"][0] * 0.6 + df_manual["ML Risk"][0] * 0.4)

    st.success(f"🚨 Final Risk Score: {final_score}/100")

    shipment = Shipment(
        country=country,
        weight=weight,
        route=route,
        company=company,
        risk_score=final_score
    )

    session.add(shipment)
    session.commit()

# ==============================
# DATABASE VIEW + SEARCH
# ==============================
st.subheader("📊 Stored Shipments")

data = session.query(Shipment).all()

if data:
    df_db = pd.DataFrame([{
        "Country": d.country,
        "Weight": d.weight,
        "Route": d.route,
        "Company": d.company,
        "Risk Score": d.risk_score
    } for d in data])

    search = st.text_input("Search Company or Country")
    if search:
        df_db = df_db[df_db.apply(lambda row: search.lower() in str(row).lower(), axis=1)]

    st.dataframe(df_db, use_container_width=True)

else:
    st.info("No data yet")
