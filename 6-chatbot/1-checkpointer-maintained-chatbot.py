from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import TypedDict, Literal, Annotated
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, BaseMessage
from langgraph.checkpoint.memory import MemorySaver

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

load_dotenv()
llm=AzureChatOpenAI(model="gpt-4o-mini")  
    
def chat_node(state: ChatState) -> ChatState:
    #Take user query from state
    messages=state['messages']
    response=llm.invoke(messages)
    return {'messages': [response]} # LangGraph will append automatically
 
 
checkpointer = MemorySaver()  

 
graph = StateGraph(ChatState)

#add nodes
graph.add_node('chat_node', chat_node)

#add edges
graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)

thread_id = '1'
# Initialize only once checkpointer for the thread
config = {"configurable": {"thread_id": thread_id}}

initial_state={
    "messages": [
        SystemMessage(content="You are a helpful chatbot.")
    ]
}
response=chatbot.invoke(initial_state, config=config)
print(f"Chatbot: {response['messages'][-1].content}")


while True:
    user_input = input("User: ")
    if user_input.strip().lower() in ['exit', 'quit', 'bye']:
        print("Exiting chat.")
        break
    
    response = chatbot.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    
    chatbot_response = response['messages'][-1]
    print(f"Chatbot: {chatbot_response.content}")