import streamlit as st
import requests

st.title("Code Review Assistant (DeepSeek-Coder)")

code_input = st.text_area(
    "Paste your code here:",
    height=300
)

if st.button("Get Review"):
    response = requests.post(
        "http://localhost:8000/review/",
        data={"code": code_input}
    )
    try:
        payload = response.json()
    except ValueError:
        st.error(f"Invalid JSON received from backend (status {response.status_code}).")
        st.text(response.text)
    else:
        review = payload.get("review") or payload.get("error") or "No feedback returned."
        st.subheader("Review & Suggestions:")
        st.code(review)
