# import streamlit as st
# import pandas as pd
# import hashlib, json, qrcode
# from io import BytesIO
# from datetime import timedelta

# # ==========================================================
# # STREAMLIT CONFIG
# # ==========================================================
# st.set_page_config(
#     page_title="Farmer Milk Procurement Dashboard",
#     layout="wide"
# )

# st.title("🔗 Farmer Milk Procurement Dashboard")

# # ==========================================================
# # LOAD DATA (NORMALIZED)
# # ==========================================================
# @st.cache_data
# def load_data():
#     df = pd.read_excel("farmer_milk_data.xlsx")

#     df.columns = (
#         df.columns
#         .str.strip()
#         .str.lower()
#         .str.replace("_", " ", regex=False)
#     )

#     df["milk collection date"] = pd.to_datetime(
#         df["milk collection date"], errors="coerce"
#     )

#     return df

# df_base = load_data()

# # ==========================================================
# # HASH UTILITY
# # ==========================================================
# def compute_hash(data: dict):
#     return hashlib.sha256(
#         json.dumps(data, sort_keys=True).encode()
#     ).hexdigest()

# # ==========================================================
# # QUERY PARAMS (ROUTING)
# # ==========================================================
# master_id = st.query_params.get("master")
# batch_id = st.query_params.get("batch")

# # Batch always overrides master (deepest route wins)
# if batch_id:
#     master_id = None

# # ==========================================================
# # ENTRY PAGE
# # ==========================================================
# if not master_id and not batch_id:
#     st.subheader("🔍 Enter Batch")

#     col1, col2 = st.columns(2)
#     master_input = col1.text_input("Master Batch", placeholder="MB001")
#     batch_input = col2.text_input("Farmer Batch ID", placeholder="FB9014")

#     if st.button("View"):
#         st.query_params.clear()
#         if master_input.strip():
#             st.query_params["master"] = master_input.strip()
#         elif batch_input.strip():
#             st.query_params["batch"] = batch_input.strip()
#         else:
#             st.warning("Please enter Master or Farmer Batch ID")
#         st.rerun()

#     st.stop()

# # ==========================================================
# # LEVEL 1 : MASTER BATCH DASHBOARD
# # ==========================================================
# if master_id and not batch_id:
#     st.subheader(f"🗂 Master Batch — {master_id}")

#     df_master = df_base[df_base["master batch"].astype(str) == master_id]

#     if df_master.empty:
#         st.error("❌ Invalid Master Batch ID")
#         st.stop()

#     # ---- Aggregated Summary ----
#     c1, c2, c3, c4 = st.columns(4)
#     c1.metric("Total Farmers", df_master["batch id"].nunique())
#     c2.metric("Total Milk (L)", round(df_master["milk quantity litres"].sum(), 2))
#     c3.metric("Total Amount (₹)", round(df_master["amount actually paid"].sum(), 2))
#     c4.metric("Collection Days", df_master["milk collection date"].nunique())

#     # ---- Farmer-wise Summary ----
#     st.subheader("👨‍🌾 Farmer Batches under Master")

#     farmer_summary = (
#         df_master
#         .groupby(
#             ["batch id", "farmer name", "farmer village"],
#             as_index=False
#         )
#         .agg(
#             total_milk=("milk quantity litres", "sum"),
#             total_amount=("amount actually paid", "sum"),
#             days=("milk collection date", "nunique")
#         )
#     )

#     st.dataframe(farmer_summary, use_container_width=True)

#     # ---- Drill Down (EXPLICIT BUTTONS) ----
#     st.subheader("🔍 Drill Down to Farmer Batch")

#     for _, row in farmer_summary.iterrows():
#         col1, col2 = st.columns([4, 1])
#         col1.markdown(
#             f"**{row['farmer name']}** | {row['farmer village']}  \n"
#             f"Batch: `{row['batch id']}` — {row['total_milk']:.2f} L | ₹{row['total_amount']:.2f}"
#         )
#         if col2.button("View", key=f"view_{row['batch id']}"):
#             st.query_params.clear()
#             st.query_params["batch"] = row["batch id"]
#             st.rerun()

#     # ---- MASTER BLOCKCHAIN (ROOT HASH) ----
#     st.subheader("⛓ Master Batch Blockchain (ROOT)")

#     master_block = {
#         "level": "MASTER",
#         "master_batch_id": master_id,
#         "total_farmers": int(df_master["batch id"].nunique()),
#         "total_milk": float(df_master["milk quantity litres"].sum()),
#         "total_amount": float(df_master["amount actually paid"].sum()),
#         "farmer_batches": sorted(farmer_summary["batch id"].tolist())
#     }

#     master_block["hash"] = compute_hash(master_block)
#     st.json(master_block)

#     st.stop()

# # ==========================================================
# # LEVEL 2 : FARMER BATCH DASHBOARD
# # ==========================================================
# df_ctx = df_base[df_base["batch id"].astype(str) == batch_id]

# if df_ctx.empty:
#     st.error(f"❌ No data found for Farmer Batch: {batch_id}")
#     st.stop()

# farmer = df_ctx.iloc[0]

# st.subheader(f"👨‍🌾 Farmer Batch — {batch_id}")

# # ---- Farmer Details ----
# c1, c2, c3, c4 = st.columns(4)
# c1.metric("Farmer Name", farmer.get("farmer name", "-"))
# c2.metric("Village", farmer.get("farmer village", "-"))
# c3.metric("City", farmer.get("farmer city", "-"))
# c4.metric("State", farmer.get("farmer state", "-"))

# # ==========================================================
# # LAST 10 DAYS SUMMARY
# # ==========================================================
# end_date = df_ctx["milk collection date"].max()
# start_date = end_date - timedelta(days=10)

# df_10 = df_ctx[
#     (df_ctx["milk collection date"] >= start_date) &
#     (df_ctx["milk collection date"] <= end_date)
# ]

# st.subheader("📊 Milk Summary (Last 10 Days)")
# c1, c2, c3 = st.columns(3)
# c1.metric("Total Milk (L)", round(df_10["milk quantity litres"].sum(), 2))
# c2.metric("Total Amount (₹)", round(df_10["amount actually paid"].sum(), 2))
# c3.metric("Collection Days", df_10["milk collection date"].nunique())

# # ==========================================================
# # PAYMENT DETAILS
# # ==========================================================
# st.subheader("💰 Payment Details")
# st.dataframe(
#     df_10[
#         [
#             "milk collection date",
#             "milk quantity litres",
#             "amount actually paid"
#         ]
#     ],
#     use_container_width=True
# )

# # ==========================================================
# # LEVEL 3 : DAY BLOCKCHAIN (LINKED CHAIN)
# # ==========================================================
# st.subheader("⛓ Day-wise Blockchain")

# prev_hash = "LINKED_TO_FARMER_BATCH"

# for _, r in df_10.sort_values("milk collection date").iterrows():
#     day_block = {
#         "level": "DAY",
#         "day_batch_id": f"{batch_id}_{r['milk collection date'].date()}",
#         "date": str(r["milk collection date"].date()),
#         "milk_litres": float(r["milk quantity litres"]),
#         "fat": float(r.get("fat %", 0)),
#         "snf": float(r.get("snf %", 0)),
#         "amount": float(r["amount actually paid"]),
#         "previous_hash": prev_hash
#     }

#     day_block["hash"] = compute_hash(day_block)
#     st.json(day_block)
#     prev_hash = day_block["hash"]

# # ==========================================================
# # QR CODE
# # ==========================================================
# def build_qr_url(batch_id):
#     BASE_URL = "https://farmer-blockchain-9z3pj9f9pnmyuzimmzsusy.streamlit.app"
#     return f"{BASE_URL}/?batch={batch_id}"

# qr = qrcode.make(build_qr_url(batch_id))
# buf = BytesIO()
# qr.save(buf, format="PNG")

# st.subheader("📱 QR Code Access")
# st.image(buf.getvalue(), width=180)


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
# LOAD DATA (CAPITALIZED → NORMALIZED)
# ==========================================================
@st.cache_data
def load_data():
    df = pd.read_excel("farmer_milk_data.xlsx")

    # Normalize for code safety
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace("_", " ", regex=False)
    )

    df["milk collection date"] = pd.to_datetime(
        df["milk collection date"], errors="coerce"
    )

    return df

df_base = load_data()

# ==========================================================
# HASH UTILITY
# ==========================================================
def compute_hash(data: dict):
    return hashlib.sha256(
        json.dumps(data, sort_keys=True).encode()
    ).hexdigest()

# ==========================================================
# ROUTING (QUERY PARAMS)
# ==========================================================
master_id = st.query_params.get("master")
batch_id = st.query_params.get("batch")

# Farmer page overrides master
if batch_id:
    master_id = None

# ==========================================================
# ENTRY PAGE
# ==========================================================
if not master_id and not batch_id:
    st.subheader("🔍 Enter or Scan Batch")

    col1, col2 = st.columns(2)
    master_input = col1.text_input("Master Batch", placeholder="XXX01")
    batch_input = col2.text_input("Farmer Batch ID", placeholder="XXXXXXXXFB9014")

    if st.button("View"):
        st.query_params.clear()
        if master_input.strip():
            st.query_params["master"] = master_input.strip()
        elif batch_input.strip():
            st.query_params["batch"] = batch_input.strip()
        else:
            st.warning("Please enter Master or Farmer Batch ID")
        st.rerun()

    st.stop()

# ==========================================================
# LEVEL 1 : MASTER BATCH DASHBOARD
# ==========================================================
if master_id and not batch_id:
    st.subheader(f"🗂 Master Batch — {master_id}")

    df_master = df_base[df_base["master batch"].astype(str) == master_id]

    if df_master.empty:
        st.error("❌ Invalid Master Batch ID")
        st.stop()

    # ---- SUMMARY ----
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Farmers", df_master["batch id"].nunique())
    c2.metric("Total Milk (L)", round(df_master["milk quantity litres"].sum(), 2))
    c3.metric("Total Amount (₹)", round(df_master["amount actually paid"].sum(), 2))
    c4.metric("Collection Days", df_master["milk collection date"].nunique())

    # ---- FARMER LIST ----
    st.subheader("👨‍🌾 Farmer Batches Under Master")

    farmer_summary = (
        df_master
        .groupby(
            ["batch id", "farmer name", "farmer village"],
            as_index=False
        )
        .agg(
            total_milk=("milk quantity litres", "sum"),
            total_amount=("amount actually paid", "sum"),
            days=("milk collection date", "nunique")
        )
    )

    st.dataframe(farmer_summary, use_container_width=True)

    # ---- DRILL DOWN ----
    st.subheader("🔍 View Farmer Batch")

    for _, row in farmer_summary.iterrows():
        col1, col2 = st.columns([4, 1])
        col1.markdown(
            f"**{row['farmer name']}** | {row['farmer village']}  \n"
            f"Batch: `{row['batch id']}` — {row['total_milk']:.2f} L | ₹{row['total_amount']:.2f}"
        )
        if col2.button("View", key=f"view_{row['batch id']}"):
            st.query_params.clear()
            st.query_params["batch"] = row["batch id"]
            st.rerun()

    # ---- MASTER BLOCKCHAIN ----
    st.subheader("⛓ Master Batch Blockchain (ROOT)")

    master_block = {
        "level": "MASTER",
        "master_batch_id": master_id,
        "total_farmers": int(df_master["batch id"].nunique()),
        "total_milk": float(df_master["milk quantity litres"].sum()),
        "total_amount": float(df_master["amount actually paid"].sum()),
        "farmer_batches": sorted(farmer_summary["batch id"].tolist())
    }

    master_block["hash"] = compute_hash(master_block)
    st.json(master_block)

    # ---- MASTER QR ----
    st.subheader("📱 Master Batch QR Code")

    def build_master_qr(mid):
        BASE_URL = "https://farmer-blockchain-9z3pj9f9pnmyuzimmzsusy.streamlit.app"
        return f"{BASE_URL}/?master={mid}"

    master_qr = qrcode.make(build_master_qr(master_id))
    buf = BytesIO()
    master_qr.save(buf, format="PNG")
    st.image(buf.getvalue(), width=180)
    st.caption("Scan to open Master Batch on mobile")

    st.stop()

# ==========================================================
# LEVEL 2 : FARMER BATCH DASHBOARD
# ==========================================================
df_ctx = df_base[df_base["batch id"].astype(str) == batch_id]

if df_ctx.empty:
    st.error(f"❌ No data found for Farmer Batch: {batch_id}")
    st.stop()

farmer = df_ctx.iloc[0]

st.subheader(f"👨‍🌾 Farmer Batch — {batch_id}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Farmer Name", farmer.get("farmer name", "-"))
c2.metric("Village", farmer.get("farmer village", "-"))
c3.metric("City", farmer.get("farmer city", "-"))
c4.metric("State", farmer.get("farmer state", "-"))

# ==========================================================
# LAST 10 DAYS SUMMARY
# ==========================================================
end_date = df_ctx["milk collection date"].max()
start_date = end_date - timedelta(days=10)

df_10 = df_ctx[
    (df_ctx["milk collection date"] >= start_date) &
    (df_ctx["milk collection date"] <= end_date)
]

st.subheader("📊 Milk Summary (Last 10 Days)")
c1, c2, c3 = st.columns(3)
c1.metric("Total Milk (L)", round(df_10["milk quantity litres"].sum(), 2))
c2.metric("Total Amount (₹)", round(df_10["amount actually paid"].sum(), 2))
c3.metric("Collection Days", df_10["milk collection date"].nunique())

# ==========================================================
# PAYMENT DETAILS
# ==========================================================
st.subheader("💰 Payment Details")
st.dataframe(
    df_10[
        [
            "milk collection date",
            "milk quantity litres",
            "amount actually paid"
        ]
    ],
    use_container_width=True
)

# ==========================================================
# LEVEL 3 : DAY BLOCKCHAIN
# ==========================================================
st.subheader("⛓ Day-wise Blockchain")

prev_hash = f"LINKED_TO_{batch_id}"

for _, r in df_10.sort_values("milk collection date").iterrows():
    day_block = {
        "level": "DAY",
        "day_batch_id": f"{batch_id}_{r['milk collection date'].date()}",
        "date": str(r["milk collection date"].date()),
        "milk_litres": float(r["milk quantity litres"]),
        "fat": float(r.get("fat %", 0)),
        "snf": float(r.get("snf %", 0)),
        "amount": float(r["amount actually paid"]),
        "previous_hash": prev_hash
    }

    day_block["hash"] = compute_hash(day_block)
    st.json(day_block)
    prev_hash = day_block["hash"]

# ==========================================================
# FARMER QR CODE
# ==========================================================
st.subheader("📱 Farmer Batch QR Code")

def build_farmer_qr(bid):
    BASE_URL = "https://farmer-blockchain-9z3pj9f9pnmyuzimmzsusy.streamlit.app"
    return f"{BASE_URL}/?batch={bid}"

farmer_qr = qrcode.make(build_farmer_qr(batch_id))
buf = BytesIO()
farmer_qr.save(buf, format="PNG")
st.image(buf.getvalue(), width=180)
st.caption("Scan to open Farmer Batch on mobile")
