
from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.parrot_memory import extract_parrot_memory
from src.nodes.segment_extractor import extract_segments

def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("parrot_memory", extract_parrot_memory)
    workflow.add_node("segment_extractor", extract_segments)
    
    workflow.set_entry_point("parrot_memory")
    workflow.add_edge("parrot_memory", "segment_extractor")
    workflow.add_edge("segment_extractor", END)
    
    return workflow.compile()