import streamlit as st
import pandas as pd
import hashlib, json, qrcode
from io import BytesIO
from datetime import timedelta

# ==========================================================
# STREAMLIT CONFIG (MOBILE FIRST)
# ==========================================================
st.set_page_config(
    page_title="Farmer Milk Procurement Dashboard",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ==========================================================
# MOBILE CSS
# ==========================================================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
    padding-left: 0.6rem;
    padding-right: 0.6rem;
}
div[data-testid="metric-container"] {
    background-color: #f8f9fa;
    border-radius: 10px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🔗 Farmer Milk Procurement Dashboard")

# ==========================================================
# LOAD DATA
# ==========================================================
@st.cache_data
def load_data():
    df = pd.read_excel("farmer_milk_data.xlsx")
    df.columns = df.columns.str.strip().str.replace("_", " ", regex=False)
    df["Milk Collection Date"] = pd.to_datetime(
        df["Milk Collection Date"], errors="coerce"
    )
    return df

df_base = load_data()

# ==========================================================
# READ BATCH ID FROM URL
# ==========================================================
batch_id = st.query_params.get("batch")

# ==========================================================
# STAGE 1 : ENTRY PAGE
# ==========================================================
if batch_id is None:
    st.subheader("🔍 Track Your Milk Batch")

    batch_input = st.text_input(
        "Enter / Scan Batch ID",
        placeholder="e.g. 10092025F9015"
    )

    if st.button("View Batch", use_container_width=True):
        if batch_input.strip():
            st.query_params["batch"] = batch_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a valid Batch ID")

    st.stop()

# ==========================================================
# STAGE 2 : LOAD BATCH DATA
# ==========================================================
df_ctx = df_base[df_base["Batch ID"].astype(str) == batch_id]

if df_ctx.empty:
    st.error(f"No data found for Batch ID: {batch_id}")
    st.stop()

farmer = df_ctx.iloc[0]

# ==========================================================
# BATCH HEADER
# ==========================================================
st.metric("📦 Batch ID", batch_id)

# ==========================================================
# FARMER DETAILS (RESPONSIVE)
# ==========================================================
st.subheader("👨‍🌾 Farmer Details")

col1, col2 = st.columns(2)
col1.metric("Name", farmer["Farmer Name"])
col2.metric("Village", farmer["Farmer village"])

col3, col4 = st.columns(2)
col3.metric("State", farmer["Farmer state"])
col4.metric("Batch ID", batch_id)

# ==========================================================
# LAST 10 DAYS DATA
# ==========================================================
end_date = df_ctx["Milk Collection Date"].max()
start_date = end_date - timedelta(days=10)

df_10 = df_ctx[
    (df_ctx["Milk Collection Date"] >= start_date) &
    (df_ctx["Milk Collection Date"] <= end_date)
]

# ==========================================================
# SUMMARY (STACKED)
# ==========================================================
st.subheader("📊 Last 10 Days Summary")

st.metric("🥛 Total Milk (Litres)", round(df_10["Milk Quantity Litres"].sum(), 2))
st.metric("💰 Total Amount (₹)", round(df_10["Amount Actually Paid"].sum(), 2))
st.metric("📅 Collection Days", df_10["Milk Collection Date"].nunique())

# ==========================================================
# PAYMENT DETAILS (MOBILE SAFE)
# ==========================================================
st.subheader("💰 Payment Details")

with st.expander("📄 View Payment Records", expanded=False):
    st.dataframe(
        df_10[
            [
                "Milk Collection Date",
                "Milk Quantity Litres",
                "Amount Actually Paid",
                "Payment Status",
                "Farmer Credit Pay Date"
            ]
        ],
        use_container_width=True,
        height=350
    )

# ==========================================================
# BLOCKCHAIN BACKTRACK FLOW
# ==========================================================
st.subheader("⛓ Blockchain Backtrack Flow")

with st.expander("🔗 View Blockchain Records"):
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

        current_hash = hashlib.sha256(
            json.dumps(block, sort_keys=True).encode()
        ).hexdigest()

        block["Current Hash"] = current_hash
        st.json(block)
        prev_hash = current_hash

# ==========================================================
# QR CODE (MOBILE ENTRY POINT)
# ==========================================================
def build_qr_url(batch_id):
    BASE_URL = "https://farmer-blockchain-9z3pj9f9pnmyuzimmzsusy.streamlit.app"
    return f"{BASE_URL}/?batch={batch_id}"

qr_url = build_qr_url(batch_id)
qr = qrcode.make(qr_url)

buf = BytesIO()
qr.save(buf, format="PNG")

st.subheader("📱 Scan to View on Mobile")

st.image(buf.getvalue(), width=200)
st.caption(f"Batch ID: {batch_id}")

st.download_button(
    "⬇️ Download QR Code",
    buf.getvalue(),
    file_name=f"Batch_{batch_id}.png",
    mime="image/png",
    use_container_width=True
)
