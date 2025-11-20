import streamlit as st
from chatbot_ui_streamlit_backend import chatbot
from langchain_core.messages import HumanMessage


# Initialize only once checkpointer for the thread
CONFIG = {"configurable": {"thread_id": "thread-1"}}

if('message_history' not in st.session_state):
    st.session_state['message_history'] = []


#message_history=[] #it get cleared on every re-run or when user press enter

#loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input=st.chat_input("Type your message here...")

if user_input:
    #first append user message to history
    st.session_state['message_history'].append({"role":"user","content":user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    response=chatbot.invoke({"messages": [HumanMessage(content=user_input)]}, config=CONFIG)   
    ai_message=response['messages'][-1].content 
    #first add the message history to the input
    st.session_state['message_history'].append({"role":"assistant","content":ai_message})
    with st.chat_message("assistant"):
        st.markdown(ai_message)