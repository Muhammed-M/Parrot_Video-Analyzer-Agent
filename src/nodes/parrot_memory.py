import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from src.state import AgentState

# 1. Define the exact JSON structure we need
class ChunkMemory(BaseModel):
    optimized_topic: str = Field(
        description="The refined, evolving main topic/title of the lecture. Make it more specific based on this new chunk."
    )
    bullet_points: List[str] = Field(
        description="Core concepts explained in this chunk. Leave empty if no actual teaching occurred."
    )
    instructor_name: str = Field(
        description="Best guess at the instructor's name from this chunk, based on who is leading/teaching. Leave empty if unclear."
    )

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"), # Parrot LLM
    api_key=os.getenv("PROVIDER_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0
)

structured_llm = llm.with_structured_output(ChunkMemory)

def extract_parrot_memory(state: AgentState) -> dict:
    current_chunk = state["current_chunk"]
    current_topic = state["main_topic"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI taking notes for a university lecture.
        
        Current Working Topic: {topic}
        
        TASK 1: Optimize the Topic. 
        Based on what is being discussed in this chunk, expand or refine the 'Current Working Topic' so it becomes a more accurate, comprehensive title for the lecture.
        
        TASK 2: Extract Bullet Points.
        Extract 1 to 6 brief bullet points capturing the core educational facts taught in this chunk. 
        Ignore student questions and casual chatter."""),
        ("user", "Transcript Chunk:\n\n{chunk}")
    ])
    
    chain = prompt | structured_llm
    result = chain.invoke({
        "topic": current_topic,
        "chunk": current_chunk
    })
    
    # In LangGraph, returning a non-Annotated key overwrites it. 
    # This replaces the old topic with the newly optimized one!
    update = {
        "main_topic": result.optimized_topic,
        "global_summary": result.bullet_points
    }
    
    # Only set instructor_name if we don't already have one and this chunk found one
    if not state.get("instructor_name") and result.instructor_name:
        update["instructor_name"] = result.instructor_name
    
    return update