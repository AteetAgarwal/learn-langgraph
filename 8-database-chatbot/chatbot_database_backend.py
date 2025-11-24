import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool
import requests

load_dotenv()
llm = AzureChatOpenAI(model="gpt-4o-mini")

#Tools
search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def calculator(first_number: float, second_number: float, operation: str) -> dict:
    """
    A simple calculator tool that can perform basic arithmetic operations.
    Args:
        first_number (float): The first number.
        second_number (float): The second number.
        operation (str): The operation to perform: add, subtract, multiply, divide.
    """
    if operation == "add":
        return {"result": first_number + second_number}
    elif operation == "subtract":
        return {"result": first_number - second_number}
    elif operation == "multiply":
        return {"result": first_number * second_number}
    elif operation == "divide":
        if second_number == 0:
            raise ValueError("Cannot divide by zero.")
        return {"result": first_number / second_number}
    else:
        raise ValueError("Unsupported operation. Use add, subtract, multiply, or divide.")
    
@tool
def get_stock_price(symbol: str) -> dict:
    """
    A tool to get the current stock price for a given symbol using Alpha Vantage API.
    Args:
        symbol (str): The stock symbol to look up.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    return r.json

#Make tool list
tool_list = [search_tool, calculator, get_stock_price]

#Make LLM tool aware
llm_with_tools = llm.bind_tools(tool_list)

#Make tools node
tool_node = ToolNode(tool_list)

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
def chat_node(state: ChatState) -> ChatState:
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}  # LangGraph will append automatically

conn=sqlite3.connect('chatbot_conversations.db', check_same_thread=False)
#checkpointer
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
#add nodes
graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

#add edges
graph.add_edge(START, 'chat_node')
#If the LLM asked for a tool, go to the tools node else go to the end
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools','chat_node')

print(graph.compile(checkpointer=checkpointer))

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