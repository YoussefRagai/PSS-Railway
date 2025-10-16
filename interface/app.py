import os, requests, streamlit as st
BACKEND = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("PSS Control Panel")
st.write("Kick off ETL, compute metrics, and run n8n flows.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("ETL")
    ls = st.number_input("Limit seasons", min_value=0, value=0, help="0 = all")
    lm = st.number_input("Limit matches/season", min_value=0, value=0, help="0 = all")
    if st.button("Run ETL"):
        r = requests.post(f"{BACKEND}/run/etl", params={
            "limit_seasons": None if ls == 0 else int(ls),
            "limit_matches": None if lm == 0 else int(lm)
        }, timeout=3600)
        st.write(r.json())

with col2:
    st.subheader("Compute")
    if st.button("Compute Player-Match Metrics"):
        r = requests.post(f"{BACKEND}/run/compute", timeout=3600)
        st.write(r.json())

st.divider()
st.subheader("Quick Health")
try:
    h = requests.get(f"{BACKEND}/health", timeout=10).json()
    st.success(h)
except Exception as e:
    st.error(str(e))