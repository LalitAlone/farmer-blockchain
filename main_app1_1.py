import streamlit as st
import pandas as pd
import hashlib, json, qrcode
from io import BytesIO
from datetime import timedelta

# ==========================================================
# STREAMLIT CONFIG
# ==========================================================
st.set_page_config(
    page_title="Farmer Milk Procurement Dashboard",
    layout="wide"
)

st.title("🔗 Farmer Milk Procurement Dashboard")

# ==========================================================
# LOAD DATA
# ==========================================================
@st.cache_data
def load_data():
    df = pd.read_excel("farmer_milk_data.xlsx")
    df.columns = df.columns.str.strip().str.replace("_", " ", regex=False)
    df["Milk Collection Date"] = pd.to_datetime(df["Milk Collection Date"], errors="coerce")
    return df

df_base = load_data()

# ==========================================================
# GET BATCH ID FROM QUERY PARAM
# ==========================================================
# Example link: ?batch=10092025F9013
query_params = st.experimental_get_query_params()
batch_id = query_params.get("batch", [None])[0]

if not batch_id:
    st.error("No Batch ID provided in URL. Example: ?batch=10092025F9013")
    st.stop()

# ==========================================================
# FILTER DATA BY BATCH ONLY
# ==========================================================
df_ctx = df_base[df_base["Batch ID"].astype(str) == batch_id]

if df_ctx.empty:
    st.error(f"No data found for Batch ID: {batch_id}")
    st.stop()

farmer = df_ctx.iloc[0]  # Assume one farmer per batch

# ==========================================================
# DISPLAY FARMER DETAILS
# ==========================================================
st.subheader("👨‍🌾 Farmer Details")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Farmer Name", farmer["Farmer Name"])
c2.metric("Village", farmer["Farmer village"])
c3.metric("State", farmer["Farmer state"])
c4.metric("Batch ID", batch_id)

# ==========================================================
# LAST 10 DAYS DATA
# ==========================================================
end_date = df_ctx["Milk Collection Date"].max()
start_date = end_date - timedelta(days=10)
df_10 = df_ctx[(df_ctx["Milk Collection Date"] >= start_date) &
               (df_ctx["Milk Collection Date"] <= end_date)]

# ==========================================================
# SUMMARY
# ==========================================================
st.subheader("📊 Batch Summary (Last 10 Days)")
c1, c2, c3 = st.columns(3)
c1.metric("Total Milk (L)", round(df_10["Milk Quantity Litres"].sum(), 2))
c2.metric("Total Amount (₹)", round(df_10["Amount Actually Paid"].sum(), 2))
c3.metric("Total Days", df_10["Milk Collection Date"].nunique())

# ==========================================================
# PAYMENT DETAILS
# ==========================================================
st.subheader("💰 Payment Details (Last 10 Days)")
st.dataframe(
    df_10[[
        "Milk Collection Date",
        "Milk Quantity Litres",
        "Amount Actually Paid",
        "Payment Duration",
        "Payment Status",
        "Farmer Credit Pay Date"
    ]],
    use_container_width=True
)

# ==========================================================
# BLOCKCHAIN BACKTRACK
# ==========================================================
st.subheader("⛓ Blockchain Backtrack Flow")
with st.expander(f"🧱 Batch Block → {batch_id}", expanded=False):
    prev_hash = "0"
    for _, r in df_10.sort_values("Milk Collection Date").iterrows():
        block = {
            "Date": str(r["Milk Collection Date"].date()),
            "Milk Litres": r["Milk Quantity Litres"],
            "Fat %": r["Fat %"],
            "SNF %": r["SNF %"],
            "Amount Paid": r["Amount Actually Paid"],
            "Previous Hash": prev_hash
        }
        current_hash = hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()
        block["Current Hash"] = current_hash
        st.json(block)
        prev_hash = current_hash

# ==========================================================
# QR CODE (LINK TO THIS BATCH)
# ==========================================================
def build_qr_url(batch_id):
    BASE_URL = "https://farmer-blockchain-9z3pj9f9pnmyuzimmzsusy.streamlit.app"
    return f"{BASE_URL}/?batch={batch_id}"

qr_url = build_qr_url(batch_id)
qr = qrcode.make(qr_url)
buf = BytesIO()
qr.save(buf, format="PNG")
qr_bytes = buf.getvalue()

st.subheader("📱 Blockchain QR Access")
c1, c2 = st.columns([1, 2])
with c1:
    st.image(qr_bytes, width=180)
with c2:
    st.markdown(
        f"""
        **Scan this QR code to view Batch {batch_id}:**  
        - Mobile-friendly  
        - Direct access to batch data
        """
    )
    st.download_button(
        "⬇️ Download QR Code",
        qr_bytes,
        file_name=f"Batch_{batch_id}.png",
        mime="image/png"
    )
