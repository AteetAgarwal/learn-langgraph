import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver

load_dotenv()
llm = AzureChatOpenAI(model="gpt-4o-mini")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
def chat_node(state: ChatState) -> ChatState:
    messages = state['messages']
    response = llm.invoke(messages)
    return {"messages": [response]}  # LangGraph will append automatically


conn=sqlite3.connect('chatbot_conversations.db', check_same_thread=False)
#checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
#add nodes
graph.add_node('chat_node', chat_node)
#add edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_thread_ids():
    all_threads = set()
    for entry in checkpointer.list(None):
        config = entry[0] if isinstance(entry, tuple) else entry
        if isinstance(config, dict):
            thread_id = config.get("configurable", {}).get("thread_id")
            if thread_id:
                all_threads.add(thread_id)
    return list(all_threads)