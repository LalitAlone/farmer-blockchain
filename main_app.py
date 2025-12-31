import streamlit as st
import pandas as pd
import plotly.express as px
import hashlib, json, qrcode
from io import BytesIO
from datetime import timedelta

# ==========================================================
# STREAMLIT CONFIG
# ==========================================================
st.set_page_config(
    page_title="Farmer Milk Procurement Blockchain Dashboard",
    layout="wide"
)

st.title("🔗 Farmer Milk Procurement Blockchain Dashboard")

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
# URL PARAMS (QR SUPPORT)
# ==========================================================
query = st.query_params
qr_farmer = query.get("farmer")
qr_batch = query.get("batch")

# ==========================================================
# 1️⃣ FILTERS (POWER BI STYLE)
# ==========================================================
st.subheader("🔍 Filters")

df_ctx = df_base.copy()
c1, c2, c3, c4 = st.columns(4)

with c1:
    farmer_sel = st.selectbox(
        "Farmer Code",
        ["All"] + sorted(df_ctx["Farmer Code"].astype(str).unique()),
        index=(
            sorted(df_ctx["Farmer Code"].astype(str).unique()).index(qr_farmer) + 1
            if qr_farmer in df_ctx["Farmer Code"].astype(str).unique()
            else 0
        )
    )

if farmer_sel != "All":
    df_ctx = df_ctx[df_ctx["Farmer Code"].astype(str) == farmer_sel]

with c2:
    batch_sel = st.selectbox(
        "Batch ID",
        ["All"] + sorted(df_ctx["Batch ID"].astype(str).unique()),
        index=(
            sorted(df_ctx["Batch ID"].astype(str).unique()).index(qr_batch) + 1
            if qr_batch in df_ctx["Batch ID"].astype(str).unique()
            else 0
        )
    )

if batch_sel != "All":
    df_ctx = df_ctx[df_ctx["Batch ID"].astype(str) == batch_sel]

with c3:
    shift_sel = st.multiselect("Shift", sorted(df_ctx["Shift"].dropna().unique()))
if shift_sel:
    df_ctx = df_ctx[df_ctx["Shift"].isin(shift_sel)]

with c4:
    milk_sel = st.multiselect("Milk Type (Breed)", sorted(df_ctx["Milk Type"].dropna().unique()))
if milk_sel:
    df_ctx = df_ctx[df_ctx["Milk Type"].isin(milk_sel)]

if df_ctx.empty:
    st.warning("No data found for selected filters")
    st.stop()

single_farmer = df_ctx["Farmer Code"].nunique() == 1
farmer = df_ctx.iloc[0] if single_farmer else None

# ==========================================================
# PREPARE LAST 10 DAYS DATA
# ==========================================================
end_date = df_ctx["Milk Collection Date"].max()
start_date = end_date - timedelta(days=10)

df_10 = df_ctx[
    (df_ctx["Milk Collection Date"] >= start_date) &
    (df_ctx["Milk Collection Date"] <= end_date)
]

# ==========================================================
# 2️⃣ FARMER PROFILE
# ==========================================================
if single_farmer:
    st.subheader("👨‍🌾 Farmer Profile")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Farmer Name", farmer["Farmer Name"])
    c2.metric("Village", farmer["Farmer village"])
    c3.metric("State", farmer["Farmer state"])
    c4.metric("Farmer Code", farmer["Farmer Code"])

# ==========================================================
# 3️⃣ FARMER OVERALL SUMMARY
# ==========================================================
st.subheader("📊 Farmer Overall Summary")

c1, c2, c3 = st.columns(3)
c1.metric("Total Milk (L)", round(df_10["Milk Quantity Litres"].sum(), 2))
c2.metric("Total Amount (₹)", round(df_10["Amount Actually Paid"].sum(), 2))
c3.metric("Total Days", df_10["Milk Collection Date"].nunique())

# ==========================================================
# 4️⃣ PAYMENT SUMMARY (LAST 10 DAYS)
# ==========================================================
st.subheader("💰 Payment Summary (Last 10 Days)")

st.dataframe(
    df_10[
        [
            "Milk Collection Date",
            "Milk Quantity Litres",
            "Amount Actually Paid",
            "Payment Duration",
            "Payment Status",
            "Farmer Credit Pay Date"
        ]
    ],
    use_container_width=True
)

# ==========================================================
# 5️⃣ FARMER BANK DETAILS
# ==========================================================
if single_farmer:
    st.subheader("🏦 Farmer Bank Details")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Bank Code", farmer["Bank Code"])
    c2.metric("Account No", farmer["Account No"])
    c3.metric("Branch Code", farmer["Branch Code"])
    c4.metric("Reference No", farmer["Reference No"])

# ==========================================================
# 6️⃣ UNION VERIFICATION
# ==========================================================
if single_farmer:
    st.subheader("✅ Union Verification")
    if str(farmer["Union Validation"]).upper() == "Y":
        st.success("Payment Validated by Union ✔")
    else:
        st.error("Union Validation Pending ✖")

# ==========================================================
# 7️⃣ SOCIETY DETAILS
# ==========================================================
if single_farmer:
    st.subheader("🏠 Society Details")
    c1, c2 = st.columns(2)
    c1.metric("Society Code", farmer["Society Code"])
    c2.metric("Batch ID", farmer["Batch ID"])

# ==========================================================
# 8️⃣ VISUALIZATIONS (INTERACTIVE 1×3)
# ==========================================================
st.subheader("📈 Milk Analytics (Last 10 Days)")

HEIGHT = 320
MARGIN = dict(l=40, r=40, t=50, b=40)
c1, c2, c3 = st.columns(3)

with c1:
    trend = df_10.groupby("Milk Collection Date", as_index=False)["Milk Quantity Litres"].sum()
    fig = px.line(trend, x="Milk Collection Date", y="Milk Quantity Litres",
                  markers=True, title="Last 10 Days Milk Trend")
    fig.update_layout(height=HEIGHT, margin=MARGIN)
    fig.update_yaxes(range=[10, 150])
    st.plotly_chart(fig, use_container_width=True)

with c2:
    shift_df = df_10.groupby("Shift", as_index=False)["Milk Quantity Litres"].sum()
    fig = px.bar(shift_df, x="Shift", y="Milk Quantity Litres", title="Shift-wise Milk")
    fig.update_layout(height=HEIGHT, margin=MARGIN)
    st.plotly_chart(fig, use_container_width=True)

with c3:
    breed_df = df_10.groupby("Milk Type", as_index=False)["Milk Quantity Litres"].sum()
    fig = px.pie(breed_df, names="Milk Type", values="Milk Quantity Litres",
                 title="Breed-wise Milk Collection")
    fig.update_layout(height=HEIGHT, margin=MARGIN)
    st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# 9️⃣ BLOCKCHAIN BACKTRACK FLOW (MINIMIZABLE)
# ==========================================================
if single_farmer:
    st.subheader("⛓ Blockchain Backtrack Flow")

    with st.expander(f"🧱 Batch Block → {farmer['Batch ID']}", expanded=False):
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
# 🔟 QR CODE (MOBILE + DOWNLOAD)
# ==========================================================
if single_farmer:
    def build_qr_url(batch_id, farmer_code):
        BASE_URL = "https://farmer-blockchain-9z3pj9f9pnmyuzimmzsusy.streamlit.app"
        return f"{BASE_URL}/?batch={batch_id}&farmer={farmer_code}"

    qr_url = build_qr_url(farmer["Batch ID"], farmer["Farmer Code"])
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
            """
            **Scan this QR code to view:**  
            - Same dashboard  
            - Same farmer  
            - Mobile-friendly  
            """
        )
        st.download_button(
            "⬇️ Download QR Code",
            qr_bytes,
            file_name=f"Farmer_{farmer['Farmer Code']}_Batch_{farmer['Batch ID']}.png",
            mime="image/png"
        )
