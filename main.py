import os
from dotenv import load_dotenv

# Load environment variables BEFORE any imports
load_dotenv()

from src.utils.video_editor import process_video
from src.utils.transcript_parser import chunk_transcript
from src.graph import build_graph

if not os.getenv("PROVIDER_API_KEY"):
    print("❌ Error: PROVIDER_API_KEY not found. Check your .env file.")
    exit(1)
    
app = build_graph()

# 1. Point this to your Teams transcript file
transcript_file = "Time series session 01.vtt"  # Ensure this file is in the root directory
output_file_name = transcript_file.split('.')[0]

print(f"Parsing transcript from {transcript_file}...")

# 2. Get the sliding window chunks (10 min window, 2 min overlap)
try:
    chunks = chunk_transcript(transcript_file, window_minutes=10, overlap_minutes=2)
except FileNotFoundError:
    print(f"❌ Error: Could not find '{transcript_file}'. Please create it in the root directory.")
    exit(1)
    
if not chunks:
    print("No text found to process. Check the file format.")
    exit(0)
    
print(f"Found {len(chunks)} chunks to process. Starting the Parrot Agent...\n")

# 3. Initialize the base state
current_state = {
    "main_topic": "Time Series Analysis and Forecasting using statistical, machine learning and deep learning models", # Adjust based on the lecture
    "current_chunk": "", 
    "global_summary": [],
    "extracted_segments": []
}

# 4. The Streaming Loop
for i, chunk in enumerate(chunks):
        print(f"--- Processing Chunk {i + 1} of {len(chunks)} ---")
        
        current_state["current_chunk"] = chunk
        current_state = app.invoke(current_state)
        
        # ADD THIS LINE to watch the AI learn the topic:
        print(f"Current Optimized Topic: {current_state['main_topic']}")
        
        print(f"Current Memory Size: {len(current_state['global_summary'])} bullet points.")
        print(f"Total Segments Kept: {len(current_state['extracted_segments'])}\n")
    
# 5. Final Output & Video Processing
print("="*50)
print("🎉 LECTURE PROCESSING COMPLETE 🎉")
print("="*50)

# Save the summary to a text file for your notes
with open(f"{output_file_name}_summary.txt", "w", encoding="utf-8") as f:
    f.write("--- Final Parrot Memory (Course Summary) ---\n\n")
    for summary in current_state["global_summary"]:
        f.write(f"• {summary}\n")
    
    f.write("\n\n--- Final Parrot Segments (Extracted Segments) ---\n\n")

    for segment in current_state['extracted_segments']:
        f.write(f"• {segment}\n\n")

print(f"📝 Saved summary to {output_file_name}_summary.txt")

# Trigger the FFmpeg video editor
input_video = "Time Series Session 01.mp4"  # Make sure this matches your actual video file name
output_video = f"edited_{output_file_name}.mp4"

# Check if the video file actually exists before trying to cut it
if os.path.exists(input_video):
    process_video(input_video, output_video, current_state["extracted_segments"])
else:
    print(f"\n⚠️ Video file '{input_video}' not found. Place it in the root folder to process the video.")