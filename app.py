import streamlit as st
from local_ollama_summarizer import local_ollama_summarizer

st.set_page_config(page_title="Local Bot Summarizer", layout="wide")

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["🧠 Local Summarizer (Ollama)"])

if page == "🧠 Local Summarizer (Ollama)":
    local_ollama_summarizer()
