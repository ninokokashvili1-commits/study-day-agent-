import os
import uuid
import streamlit as st
from langgraph.types import Command
from agent import build_graph

st.set_page_config(page_title="Study Day Assistant", page_icon="📚")
st.title("📚 Study Day Assistant")
st.caption("მართე სასწავლო დავალებები, შეამოწმე თბილისის ამინდი და მოიძიე წიგნები.")

if "GROQ_API_KEY" in st.secrets:
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

if "graph" not in st.session_state:
    st.session_state.graph = build_graph()
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.pending_interrupt = None

config = {"configurable": {"thread_id": st.session_state.thread_id}}

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state.pending_interrupt:
    st.warning(st.session_state.pending_interrupt)
    col1, col2 = st.columns(2)
    if col1.button("✅ დადასტურება"):
        res = st.session_state.graph.invoke(Command(resume=True), config)
        reply = res["messages"][-1].content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.pending_interrupt = None
        st.rerun()
    if col2.button("❌ უარის თქმა"):
        res = st.session_state.graph.invoke(Command(resume=False), config)
        reply = res["messages"][-1].content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.pending_interrupt = None
        st.rerun()

if prompt := st.chat_input("მომწერე დავალება, მკითხე ამინდი ან წიგნი..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        res = st.session_state.graph.invoke({"messages": [("user", prompt)]}, config)
        state = st.session_state.graph.get_state(config)
        if state.tasks and state.tasks[0].interrupts:
            st.session_state.pending_interrupt = state.tasks[0].interrupts[0].value
            st.rerun()
        else:
            reply = res["messages"][-1].content
            st.session_state.messages.append({"role": "assistant", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)
    except Exception as e:
        st.error(f"შეცდომა API-სთან კავშირისას: {e}")
