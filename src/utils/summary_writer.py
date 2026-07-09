import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"),
    api_key=os.getenv("PROVIDER_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0
)

def generate_summary(main_topic: str, global_summary: list) -> str:
    """
    Takes the final optimized topic and the full list of accumulated 
    bullet points, and produces a cohesive prose summary of the lecture.
    """
    bullet_text = "\n".join([f"- {b}" for b in global_summary])
    if not bullet_text:
        bullet_text = "No content was captured."

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are writing a final study summary for a video lecture.

        Lecture Topic: {topic}

        Below are bullet-point notes captured chunk-by-chunk while processing the lecture.
        Some points may be redundant or overlap across chunks since they were captured
        incrementally — merge and de-duplicate as needed.

        Write a cohesive, well-organized paragraph-form summary (not a bullet list) that
        gives a student a clear understanding of everything taught in this lecture, in the
        order the concepts were introduced."""),
        ("user", "Notes:\n\n{bullets}")
    ])

    chain = prompt | llm
    result = chain.invoke({"topic": main_topic, "bullets": bullet_text})
    return result.content