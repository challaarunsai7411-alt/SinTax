import os
import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight 

# ==========================================
# 1. INITIALIZE MEMORY FIRST (Must be at the top!)
# ==========================================
if "backup_memory" not in st.session_state:
    st.session_state.backup_memory = []

# ==========================================
# 2. SETUP & KEYS
# ==========================================
load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

hindsight_client = Hindsight(
    base_url="https://api.hindsight.vectorize.io", 
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

MEMORY_BANK_ID = "quantum_project_intel"

# ==========================================
# 3. USER INTERFACE
# ==========================================
st.title("🕵️‍♂️ Competitive Intelligence Agent")
st.markdown("Track your competitors and ask strategic questions.")
st.divider()

# --- SECTION 1: ADD INTEL ---
st.subheader("1. Add Competitor Intel to Memory")
new_intel = st.text_area("Paste a news article, pricing update, or feature launch here:")

if st.button("Save to Memory"):
    if new_intel:
        with st.spinner("Saving..."):
            try:
                # Try the Cloud first
                hindsight_client.retain(bank_id=MEMORY_BANK_ID, content=new_intel)
                st.success("Intel successfully securely saved to your Hindsight database!")
            except Exception as e:
                # Fallback to local memory if server is down
                st.session_state.backup_memory.append(new_intel)
                st.warning("Hindsight cloud is overloaded. Saved locally to backup memory so you can keep testing!")
                with st.expander("View Error Details"):
                    st.write(e)
    else:
        st.warning("Please paste some text first.")

st.divider()

# --- SECTION 2: CHAT AGENT ---
st.subheader("2. Ask the Agent for Strategy")
user_question = st.text_input("Ask a question (e.g., 'What phone did Quantum Mobile release?')")

if st.button("Analyze"):
    if user_question:
        with st.spinner("Searching Memory..."):
            
            memory_context = ""
            
            try:
                # Try to search the Cloud
                recall_results = hindsight_client.recall(bank_id=MEMORY_BANK_ID, query=user_question)
                memory_context = "\n".join([str(result) for result in recall_results])
            except Exception as e:
                # Fallback to local memory if server is down
                memory_context = "\n\n".join(st.session_state.backup_memory)
                st.toast("Using local backup memory while servers are down.")
            
            if not memory_context or memory_context.isspace():
                memory_context = "No competitor intel available in memory yet."

            system_prompt = f"""
            You are a brilliant Competitive Intelligence Analyst. 
            Use ONLY the following context from your memory to answer the user's question.
            If the answer is not in the memory context, say "I don't have enough information in my memory."
            Do not make up facts outside of the provided memory.
            
            Memory Context: 
            {memory_context}
            """
            
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_question}
                ],
                model="openai/gpt-oss-120b", 
            )
            
            st.write(chat_completion.choices[0].message.content)
    else:
        st.warning("Please ask a question first.")