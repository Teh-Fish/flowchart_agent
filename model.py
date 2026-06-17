from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from graph_structure_full import app, DiagramState
from dotenv import load_dotenv
import os

load_dotenv('config.env')
# Load config
model = os.environ.get('model')
reasoning_effort = os.environ.get('reasoning_effort')
thinking = os.environ.get('thinking')

llm = ChatOpenAI(
    api_key= os.environ.get('deepseek_api_key'),
    base_url= 'https://api.deepseek.com',
    model= model,
    reasoning_effort= reasoning_effort,
    extra_body= {'thinking': {'type': thinking}}
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

system_message = SystemMessage(content=
""" You are a helpful office assistant, if the user demands a flowchart,
only use the provided create_flowchart_tool and nothing else.
Parse exactly the user's description of the process to the tool.
If the user demands any changes, refernce the full "nodes" object returned
from the create_flowchart_tool to make changes. ALWAYS use the create_flowchart_tool
to update the file for any changes.
DO NOT manually add an end node to the description parse to the tool.

""")

def main():
    history = []
    print("Type '/new' to start a fresh session, '/quit' to exit.\n")
 
    while True:
        try:
            user_input = input("You: ").strip()
            human_message = HumanMessage(user_input)
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
 
        if not user_input:
            continue
 
        if user_input == "/quit":
            print("Goodbye!")
            break
 
        if user_input == "/new":
            history.clear()
            print("--- New session ---\n")
            continue
        
        history.append(human_message)
        response = llm.invoke({'messages':history})
        reply = response['messages'][-1].content
        ai_message = AIMessage(content= reply)
        history.append(ai_message)
        print(f"\nAssistant: {reply}\n")
 
 
if __name__ == "__main__":
    main()

