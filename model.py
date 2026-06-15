from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage
from graph_structure_full import app, DiagramState
from dotenv import load_dotenv
import os


load_dotenv('api.env')
llm = ChatOpenAI(
    api_key= os.environ.get('deepseek_api_key'),
    base_url= 'https://api.deepseek.com',
    model= "deepseek-v4-flash"
)

@tool
def create_flowchart_tool(procedure: str) -> str:
    """Creates a .drawio flowchart file from a plain-text procedure description."""
    state = DiagramState(messages=[HumanMessage(content=procedure)])
    app.invoke(state)
    return "Flowchart created successfully at ./outputs/diagram.drawio"

tools = [create_flowchart_tool]
llm = create_agent(llm, tools)

chat_history = []
message = [
    SystemMessage(content= "You are a helpful office assistant, if the user demands a flowchart, only use the provided create_flowchart_tool" \
    "parse exactly the user's description of the process to the tool"),
    HumanMessage(content= "First we send a request to update the information, then we check the status, if the status is ok, we update the information"
        "Else, check if deletion is possible, if yes, check for reliant data, if yes don't delete, else delete"
        "if deletion is not possible, try and update the special code, if yes allow update, else don't")
]

response = llm.invoke({"messages":message})
print(response['messages'][-1].content)

