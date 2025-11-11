import gc
import json
import requests
import streamlit as st
from datetime import datetime
from save_kb import save_bot_to_kb

def local_ollama_summarizer():
    st.title("🧠 Local Bot Summarizer using Ollama")
    st.markdown("Run your summarizer fully offline using the local Ollama model.")

    # --- File Upload ---
    text_file = st.file_uploader("Upload a bot JSON or text file", type=["json", "txt"], key="ollama_upload")

    if text_file:
        try:
            content = text_file.read().decode("utf-8")
        except Exception:
            try:
                content = text_file.getvalue().decode("utf-8")
            except Exception:
                content = None

        if not content:
            st.warning("⚠️ Couldn't read uploaded JSON file.")
        else:
            show_preview = st.checkbox("📄 Show JSON Preview", value=True)
            if show_preview:
                st.text_area("Preview of Uploaded File", content[:4000], height=240)

            # --- Generate Summary Button ---
            if st.button("✨ Generate Technical Summary"):
                with st.spinner("Generating detailed technical summary locally using Ollama..."):
                    try:
                        response = requests.post(
                            "http://localhost:11434/api/generate",
                            json={
                                "model": "deepseek-r1:latest",
                                "prompt": (
                                    "You are an experienced Automation Anywhere (AA360) developer and mentor.\n"
                                    "Explain the following bot clearly:\n\n"
                                    f"{content}"
                                )
                            },
                            stream=True,
                            timeout=600,
                        )

                        summary_text = ""
                        placeholder = st.empty()

                        for line in response.iter_lines(decode_unicode=True):
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                            except Exception:
                                summary_text += line
                                placeholder.markdown(summary_text)
                                continue

                            if isinstance(data, dict) and "response" in data:
                                summary_text += data["response"]
                                placeholder.markdown(summary_text)

                        response.close()

                        if summary_text.strip():
                            st.session_state["ollama_summary"] = summary_text
                            st.success("✅ Summary generated successfully!")
                        else:
                            st.warning("⚠️ No valid summary received.")

                    except requests.exceptions.ConnectionError:
                        st.error("❌ Could not connect to Ollama. Make sure it is running.")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")

                gc.collect()

    # --- Chat Section ---
    if "ollama_summary" in st.session_state:
        st.markdown("---")
        st.subheader("💬 Chat About This Bot Summary")

        if "ollama_chat_history" not in st.session_state:
            st.session_state["ollama_chat_history"] = []

        for role, msg in st.session_state["ollama_chat_history"]:
            st.chat_message(role).markdown(msg)

        if prompt := st.chat_input("Ask about the bot..."):
            st.chat_message("user").markdown(prompt)
            st.session_state["ollama_chat_history"].append(("user", prompt))

            chat_prompt = (
                f"{st.session_state['ollama_summary']}\n\n"
                f"User question: {prompt}"
            )

            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": "gemma3:1b", "prompt": chat_prompt},
                    stream=True,
                    timeout=300,
                )

                answer = ""
                placeholder = st.chat_message("assistant").empty()

                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except Exception:
                        answer += line
                        placeholder.markdown(answer)
                        continue

                    if isinstance(data, dict) and "response" in data:
                        answer += data["response"]
                        placeholder.markdown(answer)

                response.close()
                st.session_state["ollama_chat_history"].append(("assistant", answer))

            except Exception as e:
                st.error(f"⚠️ Error while chatting: {e}")

    # --- Save Summary ---
    if "ollama_summary" in st.session_state:
        st.markdown("---")
        st.subheader("💾 Save This Summary to Knowledge Base")

        with st.form("save_to_kb_form"):
            bot_name = st.text_input("🤖 Bot Name")
            description = st.text_area("📝 Description", placeholder="What does this bot do?")
            comments = st.text_area("💡 Notes (optional):")

            save_btn = st.form_submit_button("💾 Save Summary")

            if save_btn:
                if not bot_name.strip():
                    st.error("Bot name is required.")
                else:
                    bot_data = {
                        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "bot_name": bot_name,
                        "description": description or "Summary generated locally.",
                        "functions_details": st.session_state.get("ollama_summary", ""),
                        "comments": comments,
                        "source": "Ollama Summarizer",
                    }
                    ok = save_bot_to_kb(bot_data)
                    if ok:
                        st.success(f"✅ Saved successfully!")
                    else:
                        st.error("❌ Failed to save. Check storage permissions.")
