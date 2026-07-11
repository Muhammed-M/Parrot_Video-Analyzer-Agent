import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from src.state import AgentState
from src.utils.video_editor import time_to_seconds

class KeptSegment(BaseModel):
    start_time: str = Field(description="Start timestamp in MM:SS or HH:MM:SS format")
    end_time: str = Field(description="End timestamp in MM:SS or HH:MM:SS format")
    reason: str = Field(description="Brief reason why this educational content is important")

class ChunkExtraction(BaseModel):
    extracted_segments: List[KeptSegment] = Field(
        description="List of all important segments to keep. Leave empty if the whole chunk is irrelevant."
    )

llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME"), # Extractor LLM
    api_key=os.getenv("PROVIDER_API_KEY"),
    base_url=os.getenv("BASE_URL"),
    temperature=0
)

structured_llm = llm.with_structured_output(ChunkExtraction)

def extract_segments(state: AgentState) -> dict:
    """
    Evaluates the chunk against the topic and memory, 
    and outputs the specific timestamps to keep.
    """
    current_chunk = state["current_chunk"]
    main_topic = state["main_topic"]
    
    # Format the Parrot memory into a readable string
    memory_string = "\n".join([f"- {m}" for m in state["global_summary"]])
    if not memory_string:
        memory_string = "No previous context yet."

    speaker_note = ""
    if state.get("instructor_name"):
        speaker_note = f"The instructor is {state['instructor_name']}. Every other named speaker in this transcript is a student. If {state['instructor_name']} does not appear as a speaker in this chunk, fall back to identifying the instructor by behavior instead."
    else:
        speaker_note = """IDENTIFYING SPEAKERS: The transcript lines are labeled "Speaker Name: text" from the raw Teams
        captions — there is no explicit "instructor" or "student" tag. Infer the role from behavior, not
        from the name alone:
        - The INSTRUCTOR is the speaker who leads the session: they talk in long, continuous stretches,
        introduce and explain concepts, walk through material in a structured way, and drive the pace of
        the lecture. If a teaching assistant or guest also teaches in this way, treat them as instructor
        for this rule set too.
        - STUDENTS are speakers who appear briefly and reactively: short interjections, questions, "can you
        repeat that," acknowledgments, or side comments — even if the same person's name reappears
        multiple times across the chunk.
        - Do not assume role from name formatting or position in the transcript — judge from what the
        speaker is actually doing in the text."""



    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are editing a raw lecture recording into a study video for a student who wants to fully understand the lecture while skipping only the parts that waste their time.

            Analyze the chunk and extract the start and end timestamps to KEEP.
         
            {speaker_note}

            YOUR DEFAULT IS TO KEEP. Only cut a timestamp range if it clearly falls into one of these categories:

            1. STUDENT SPEECH: 
                Any time a student has the mic open (questions, comments, chatter). Cut the student's speech itself.
            2. LOGISTICS / DEAD AIR: 
                The instructor handling tech issues ("can you hear me", "let me share my screen"), 
                announcing or sitting through a break ("let's take 10 minutes", "we're back"), 
                attendance, or similar non-content admin.
            3. PERSONAL / OFF-TOPIC CHATTER: 
                The instructor having a personal conversation or discussing something with no educational value (e.g. grading logistics, small talk unrelated to the course).

            CRITICAL EXCEPTION - PROTECT RE-EXPLANATIONS: If a student asks a question, asks the instructor to
            repeat something, or asks for clarification, you MUST cut the student's speech but KEEP the
            instructor's entire response. This includes cases where the instructor repeats or rephrases
            something they already said — repetition triggered by a student is valuable for a viewer who is
            studying, not filler. Never let a student's question cause you to cut the instructor's answer.

            EVERYTHING ELSE THE INSTRUCTOR SAYS IS KEPT BY DEFAULT. This includes tangents, real-world
            examples, analogies, side-notes, and context-setting, even if they are not a tight match for the
            Main Topic — they still come from the instructor teaching and may help the student understand the
            material. Do not cut instructor speech just because it isn't a perfect topical match; only cut it
            if it clearly matches categories 2 or 3 above.

            WHEN UNCERTAIN, KEEP THE SEGMENT. This video will be a student's primary way of reviewing the
            lecture, so missing real content is a much worse outcome than including a few extra seconds of
            borderline material. Only cut when you are confident the timestamp range matches one of the three
            cut categories.
         
            OUTPUT CONTRACT: The output list must contain ONLY the timestamp ranges you are KEEPING. If you
            decide a stretch of transcript matches a cut category (student speech, logistics/dead air, personal
            chatter), do NOT add it to the output — simply omit those timestamps entirely. Never include an
            entry whose reason explains why something was cut, excluded, or is not useful; every entry's reason
            must justify why that specific range is valuable content worth watching. If you find yourself
            writing a reason like "this is not relevant" or "this is filler," that is a signal you should leave
            that stretch out of the output completely, not add it.

            Give the cuts a little bit of breathing room so the video doesn't feel like a glitchy mess. Do not
            make tiny 5-second cuts if it ruins the instructor's sentence, and never cut mid-sentence."""),
        ("user", """Evolving Main Topic: {topic}
        Previously Discussed (Memory): {memory}
        
        Transcript Chunk with Timestamps: {chunk}""")
    ])
    
    chain = prompt | structured_llm
    
    # Run the model
    result = chain.invoke({
        "topic": main_topic,
        "memory": memory_string,
        "chunk": current_chunk,
        "speaker_note": speaker_note
    })
    
    # Convert the Pydantic objects to dictionaries, dropping any malformed or
    # degenerate ranges (start >= end) before they ever enter state.
    segments_dict = []
    for segment in result.extracted_segments:
        try:
            start_sec = time_to_seconds(segment.start_time)
            end_sec = time_to_seconds(segment.end_time)
        except ValueError:
            print(f"⚠️ Skipping segment with unparseable timestamp: {segment}")
            continue
        if start_sec >= end_sec:
            print(f"⚠️ Skipping degenerate/invalid segment: {segment}")
            continue
        segments_dict.append(segment.model_dump())
    
    # This appends the new segments to the master list in our LangGraph state
    return {"extracted_segments": segments_dict}
