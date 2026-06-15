from langgraph.graph import StateGraph, END
import drawpyo as pyo
from typing import TypedDict, List

class Node(TypedDict):
    label: str
    type: str
    contain: list[int]

def draw_node(node: Node, page: pyo.Page, position: tuple, size: int):
    return pyo.diagram.object_from_library(
                                        page= page,
                                        library= 'flowchart',
                                        obj_name= node['type'],
                                        value= node['label'],
                                        position= position,
                                        height= size,
                                        width= size)

def recursive_draw(node_index: int, node_list: List[Node], page: pyo.Page, size: int, x_coord: int, y_coord: int):
    node = node_list[node_index]
    # Initialize a coord if not exist
    if x_coord == None or y_coord == None:
        x_coord = 0
        y_coord = 0
    position = (x_coord, y_coord)
    node['obj'] = draw_node(node, page= page, position= position, size= size)

    num_decision = 0
    if node['type'] == 'decision':
        num_decision += 1

    # Recursive call to next step, increment x_coord by default, increment y_coord for decision block
    for i, child_index in enumerate(node['contain']):
        if child_index <= node_index:
            return 0
        if i == 0:
            num_decision += recursive_draw(child_index, node_list, page, size, x_coord + size * 1.5, y_coord)
        else:
            recursive_draw(child_index, node_list, page, size, x_coord + size * 1.5, y_coord + size * 1.5 * num_decision)

    # Connect the drawn block to its children
    for i, child_index in enumerate(node['contain']):
        if node['type'] == 'decision':
            if i == 0:
                pyo.diagram.Edge(
                    page= page,
                    source= node_list[node_index]['obj'],
                    target= node_list[child_index]['obj'],
                    label= 'Yes'
                )
            else:
                pyo.diagram.Edge(
                    page= page,
                    source= node_list[node_index]['obj'],
                    target= node_list[child_index]['obj'],
                    label= 'No',
                    label_position= 0.5,
                    label_offset= 10,
                    exitX= 0.5, exitY= 1,
                    entryX= 0, entryY = 0.5
                )
        else:
            if i == 0:
                pyo.diagram.Edge(
                    page= page,
                    source= node_list[node_index]['obj'],
                    target= node_list[child_index]['obj'],
                )
    # Return num_decision for higher recursion
    return num_decision

def draw_end_node(page: pyo.page, node_list: List[Node], size: int):
    x_coords = []
    for node in node_list:
        x_coords.append(node['obj'].position[0])
    x_coord =  max(x_coords) + size * 1.5
    end = pyo.diagram.object_from_library(page= page,
                                          library= 'flowchart',
                                          obj_name= 'start_1',
                                          value= 'End',
                                          position= (x_coord, 0),
                                          height= size,
                                          width= size)
    
    for node in node_list:
        if node['contain'] == []:
            pyo.diagram.Edge(page= page,
                             source= node['obj'],
                             target= end,
                             exitX= 1, exitY= 0.5)

