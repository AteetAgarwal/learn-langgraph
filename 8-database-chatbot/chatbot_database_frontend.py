import streamlit as st
from chatbot_database_backend import chatbot, retrieve_all_thread_ids
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid


#**************************************Utility Functions**********************************************
def generate_thread_id():
    return str(uuid.uuid4())

def reset_thread():
    st.session_state['thread_id'] = generate_thread_id()
    st.session_state['message_history'] = []
    add_thread(st.session_state['thread_id'])
    
def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)
        
def load_conversation_history(thread_id):
    # Placeholder for loading conversation history based on thread_id
    # In a real application, this would fetch data from a database or file
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    values = state.values
    if 'messages' not in values:
        st.warning(f"No messages found for thread {thread_id}. Available keys: {list(values.keys())}")
        return []
    return values['messages']


#**********************************************Session Setup**********************************************
if('message_history' not in st.session_state):
    st.session_state['message_history'] = []

if('thread_id' not in st.session_state):
    st.session_state['thread_id'] = generate_thread_id()
    
if('chat_threads' not in st.session_state):
    st.session_state['chat_threads'] = retrieve_all_thread_ids()
    
add_thread(st.session_state['thread_id'])
    
    
#******************************Initialize Checkpointer Configuration**********************************************
# Initialize only once checkpointer for the thread
CONFIG = {
            "configurable": {"thread_id": st.session_state['thread_id']}, 
            "metadata": {
                "thread_id": st.session_state['thread_id']
            },
            "run_name": "chat_turn"
        }


#**********************************************Sidebar UI**********************************************
st.sidebar.title("Langgraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_thread()
    
st.sidebar.header("My Conversations")

for thread_id in st.session_state['chat_threads'][::-1]:
    messages=load_conversation_history(thread_id)
    preview = next(
        (
            msg.content[:40] + ("..." if len(msg.content) > 40 else "")
            for msg in messages
            if isinstance(msg, HumanMessage)
        ),
        "New Conversation",
    )
    if st.sidebar.button(preview, key=f"thread-btn-{thread_id}"):
        st.session_state['thread_id']= thread_id
        temp_message=[]
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role="user"
            else:
                role="assistant"
            temp_message.append({"role":role, "content":msg.content})
        st.session_state['message_history']=temp_message

#*********************************************Conversation History**********************************************
#loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


#*********************************************User Input**********************************************
user_input=st.chat_input("Type your message here...")


#*********************************************Processing User Input**********************************************
if user_input:
    #first append user message to history
    st.session_state['message_history'].append({"role":"user","content":user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    
    with st.chat_message("assistant"): 
        # Use a mutable holder so the generator can set/modify it
        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]}, 
                config=CONFIG, 
                stream_mode='messages'
            ):
                # Lazily create & update the SAME status container when any tool runs
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk, AIMessage):
                    #yield only AI message content
                    yield message_chunk.content
                    
        ai_message = st.write_stream(ai_only_stream())
         # Finalize only if a tool was actually used
        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
        st.session_state['message_history'].append({"role":"assistant","content":ai_message})