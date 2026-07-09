from typing import Annotated, TypedDict, List, Dict, Any
import operator

class AgentState(TypedDict):
    # The user's main topic constraint
    main_topic: str
    
    # The current 5-minute chunk being processed
    current_chunk: str
    
    # THE PARROT MEMORY: Annotated with operator.add means new items 
    # returned by a node are appended to the existing list.
    global_summary: Annotated[List[str], operator.add]
    
    # The final list of extracted timestamps (start_time, end_time, reason)
    extracted_segments: Annotated[List[Dict[str, Any]], operator.add]

    instructor_name: str