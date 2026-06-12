import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Clinical Prescription Safety Dashboard",
    layout="wide"
)

# ---------------- HEADER ----------------
st.title("💊 Antibiotic Prescription Audit System")
st.caption("Decision Support System for Antimicrobial Stewardship")
st.caption("⚠️ Educational tool only. Not for clinical decision-making.")

st.divider()

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ Control Panel")

show_raw_data = st.sidebar.checkbox("Show Dataset", False)
download_report = st.sidebar.checkbox("Enable Report Download", True)

# ---------------- LOAD DATA ----------------
try:
    df = pd.read_csv("antibiotic_data.csv")
except FileNotFoundError:
    st.error("❌ antibiotic_data.csv not found")
    st.stop()

required_cols = [
    "Disease", "Antibiotic", "Bacteria",
    "Typical_Dose_mg", "Duration_Days", "First_Line_Treatment"
]

missing = [c for c in required_cols if c not in df.columns]
if missing:
    st.error(f"❌ Missing columns: {missing}")
    st.stop()

if show_raw_data:
    st.subheader("📁 Dataset Preview")
    st.dataframe(df)

# ---------------- RULE ENGINE ----------------
clean_rules = {}

for disease in df["Disease"].unique():
    subset = df[df["Disease"] == disease]
    first_line = subset[subset["First_Line_Treatment"] == "Yes"]

    if not first_line.empty:
        row = first_line.iloc[0]

        symptoms = ["Fever", "Pain", "Cough"]
        if "Key_Symptoms" in df.columns:
            symptoms = str(row["Key_Symptoms"]).split(",")
            symptoms = [s.strip() for s in symptoms if s.strip()]

        clean_rules[disease] = {
            "bacteria": row["Bacteria"],
            "antibiotic": row["Antibiotic"],
            "dose": row["Typical_Dose_mg"],
            "duration": row["Duration_Days"],
            "resistance": row.get("Resistant_Bacteria", "Unknown"),
            "symptoms": symptoms
        }

if not clean_rules:
    st.error("❌ No valid treatment rules found in dataset")
    st.stop()

# ---------------- DISEASE INFORMATION (NEW ADDITION) ----------------
disease_info = {
    "UTI": {
        "description": "Urinary tract infection affecting bladder and urinary system.",
        "area": "Urinary Tract",
        "cause": "Mostly caused by E. coli bacteria."
    },
    "Pneumonia": {
        "description": "Infection causing inflammation in lungs.",
        "area": "Lungs",
        "cause": "Commonly Streptococcus pneumoniae."
    },
    "Tuberculosis": {
        "description": "Chronic bacterial infection affecting lungs.",
        "area": "Lungs",
        "cause": "Mycobacterium tuberculosis."
    },
    "Skin Infection": {
        "description": "Bacterial infection of skin and soft tissues.",
        "area": "Skin",
        "cause": "Staphylococcus aureus."
    }
}

# ---------------- INPUT ----------------
st.subheader("🧑‍⚕️ Prescription Entry")

col1, col2 = st.columns(2)

with col1:
    disease = st.selectbox("Select Disease", sorted(clean_rules.keys()))

    # ✅ Disease Info Box
    if disease in disease_info:
        with st.expander("📖 Disease Information", expanded=False):
            st.write(f"**Description:** {disease_info[disease]['description']}")
            st.write(f"**Affected Area:** {disease_info[disease]['area']}")
            st.write(f"**Common Cause:** {disease_info[disease]['cause']}")

    expected_symptoms = clean_rules[disease]["symptoms"]

    selected_symptoms = st.multiselect(
        "Select Symptoms",
        options=expected_symptoms + ["Other"],
        default=expected_symptoms[:2] if len(expected_symptoms) >= 2 else expected_symptoms
    )

with col2:
    available_antibiotics = sorted(
        df.loc[df["Disease"] == disease, "Antibiotic"]
        .dropna()
        .unique()
    )

    antibiotic = st.selectbox("Prescribed Antibiotic", available_antibiotics)

st.divider()

# ---------------- CLINICAL PANEL ----------------
st.subheader("🩺 Clinical Reference Panel")

rule = clean_rules[disease]

c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Recommended Dose", f"{rule['dose']} mg")
with c2:
    st.metric("Recommended Duration", f"{rule['duration']} days")
with c3:
    st.metric("Target Bacteria", rule["bacteria"])

st.divider()

# ---------------- AUDIT ENGINE ----------------
st.subheader("🧠 Prescription Safety Analysis")

risk_score = 0

if antibiotic == rule["antibiotic"]:
    st.success("✔ Correct first-line antibiotic")
else:
    st.error("❌ Antibiotic mismatch")
    st.info(f"Recommended: {rule['antibiotic']}")
    risk_score += 3

if not selected_symptoms:
    st.warning("⚠ No symptoms entered")
    risk_score += 1

elif "Other" in selected_symptoms and len(selected_symptoms) == 1:
    st.warning("⚠ Atypical symptom pattern")

if "resistant" in str(rule["resistance"]).lower():
    st.warning(f"⚠ Resistance risk: {rule['resistance']}")
    risk_score += 2
else:
    st.info(f"Resistance info: {rule['resistance']}")

if len(selected_symptoms) >= 4:
    st.warning("⚠ Possible high severity infection")
    risk_score += 1

st.divider()

# ---------------- RISK RESULT ----------------
st.subheader("📊 Risk Classification")

col1, col2 = st.columns(2)

with col1:
    if risk_score == 0:
        st.success("🟢 LOW RISK")
    elif risk_score <= 2:
        st.warning("🟡 MODERATE RISK")
    else:
        st.error("🔴 HIGH RISK")

with col2:
    st.metric("Risk Score", risk_score)

st.divider()

# ---------------- REFERENCES ----------------
st.subheader("📚 Clinical Guidelines")

encoded_query = urllib.parse.quote(f"antibiotic guidelines {disease}")

col1, col2, col3 = st.columns(3)

with col1:
    st.link_button("WHO", "https://www.who.int")
with col2:
    st.link_button("CDC", "https://www.cdc.gov")
with col3:
    st.link_button("Evidence Search", f"https://www.google.com/search?q={encoded_query}")

# ---------------- REPORT ----------------
if download_report:

    report = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Disease": disease,
        "Symptoms": ", ".join(selected_symptoms),
        "Prescribed Antibiotic": antibiotic,
        "Recommended Antibiotic": rule["antibiotic"],
        "Dose": rule["dose"],
        "Duration": rule["duration"],
        "Bacteria": rule["bacteria"],
        "Resistance": rule["resistance"],
        "Risk Score": risk_score,
        "Status": (
            "Low Risk" if risk_score == 0 else
            "Moderate Risk" if risk_score <= 2 else
            "High Risk"
        )
    }

    report_df = pd.DataFrame([report])
    csv = report_df.to_csv(index=False).encode("utf-8")

    st.sidebar.download_button(
        "📥 Download Report",
        csv,
        file_name=f"clinical_audit_{disease}.csv",
        mime="text/csv"
    )
