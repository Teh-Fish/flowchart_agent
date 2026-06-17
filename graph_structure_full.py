from langgraph.graph import StateGraph, END, MessagesState
from langchain_core.messages import HumanMessage
from draw_utils import Node, recursive_draw, draw_end_node
from openai import OpenAI
import drawpyo as pyo
from dotenv import load_dotenv
import json
import os

load_dotenv('api.env')


class DiagramState(MessagesState):
    nodes: list[Node]
    global_size: int


def create_node_list(state: DiagramState) -> DiagramState:
    """
    LLM agent that reads the last HumanMessage in state['messages'],
    interprets it as a procedure description, and returns a list of
    Node objects indexed in DFS order (yes-first traversal).
    """
    client = OpenAI(
        api_key= os.environ.get('deepseek_api_key'),
        base_url= 'https://api.deepseek.com'
    )

    messages = state.get("messages", [])
    procedure_text = next(
        (
            msg.content
            for msg in reversed(messages)
            if hasattr(msg, "type") and msg.type == "human"
        ),
        None,
    )
    if not procedure_text:
        raise ValueError(
            "No procedure description found. "
            "Pass a HumanMessage with the procedure text when invoking the graph."
        )

    SYSTEM_PROMPT = """\
You are a flowchart node builder. Given a plain-text procedure description, \
produce a JSON object {"nodes": [...]} where each node represents one step, \
ordered strictly by Depth-First Search (DFS) — always follow the YES branch \
to its terminal end before assigning any index to nodes on the NO branch. \
ALWAYS begins with a start_1 node. If the user ask for a specific size, set \
that as the size for the json output, else default to 100. \
DO NOT add an end node to the JSON object, leave the final step as a leave \
with no child index

Node schema:
  label   : concise step name (string)
  type    : "process"  — single outgoing path
          | "start_1" - mark the start of the flowchart
          | "decision" — yes/no branch
  contain : list of child node indices (0-based integers)
            • process with a successor  → [next_index]
            • terminal process node     → []
            • decision node             → [yes_index, no_index]

DFS indexing rules:
  • Index 0 is always the entry point.
  • Fully number every node reachable via the YES branch before numbering
    any node that is only reachable via a NO branch.
  • If a branch leads to a shared merge node, assign the merge node the
    index it would get when first encountered in DFS order.

────────────────────────────────────────────
EXAMPLE
Procedure: "Check stock. If available, pack the item then ship it. \
If unavailable, notify the customer. Each node size should be 100"

DFS walk:
  0 → Start
        → 1 → Check stock (decision)
                YES → 2 → Pack item (process)
                            → 3 → Ship it (process, terminal YES path)
                NO  → 4 → Notify customer (process, terminal NO path)

Output:
{
  "nodes": [
    {"label": "Start",              "type": "start_1",  "contain": [1]}
    {"label": "Check stock",        "type": "decision", "contain": [2, 4]},
    {"label": "Pack item",          "type": "process",  "contain": [3]},
    {"label": "Ship it",            "type": "process",  "contain": []},
    {"label": "Notify customer",    "type": "process",  "contain": []}
  ],
  "size": 100
}
────────────────────────────────────────────
Return ONLY the JSON object. No markdown fences, no explanation."""

    response = client.chat.completions.create(
        model="deepseek-v4-flash",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": procedure_text},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    nodes = [
        Node(label=n["label"], type=n["type"], contain=n["contain"])
        for n in data["nodes"]
    ]
    size = data["size"]

    return {**state, "nodes": nodes, "global_size": size}

def create_diagram(state: DiagramState) -> DiagramState:
    file = pyo.File()
    file.file_path = "./outputs"
    file.file_name = "diagram.drawio"
    page = pyo.Page(file=file)
    nodes = state["nodes"]
    size = state["global_size"]
    recursive_draw(
        node_index=0,
        node_list=nodes,
        page=page,
        size=size,
        x_coord=None,
        y_coord=None,
    )
    draw_end_node(page= page,
                  node_list= nodes,
                  size= size)
    file.write()
    return state


workflow = StateGraph(DiagramState)
workflow.add_node("create_node_list", create_node_list)
workflow.add_node("create_diagram", create_diagram)

workflow.set_entry_point("create_node_list")
workflow.add_edge("create_node_list", "create_diagram")

app = workflow.compile()


if __name__ == '__main__':
    # procedure = (
    #     "First we send a request to update the information, then we check the status, if the status is ok, we update the information"
    #     "Else, check if deletion is possible, if yes, check for reliant data, if yes don't delete, else delete"
    #     "if deletion is not possible, try and update the special code, if yes allow update, else don't"
    # )

    procedure = (
        "First create a new category code, then we check for duplicate, if there's a duplicate,"
        "notify the user then loop back to create a new category code, else create a new category code then end"
    )

    test_state = DiagramState(
        messages=[HumanMessage(content=procedure)],
    )

    result = app.invoke(test_state)
    print("Generated nodes:")
    for i, node in enumerate(result["nodes"]):
        print(f"  [{i}] {node}")