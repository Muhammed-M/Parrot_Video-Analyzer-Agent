import os
from dotenv import load_dotenv

# Load environment variables BEFORE any imports
load_dotenv()

from src.utils.video_editor import process_video
from src.utils.transcript_parser import chunk_transcript
from src.graph import build_graph
from src.utils.summary_writer import generate_summary

if not os.getenv("PROVIDER_API_KEY"):
    print("❌ Error: PROVIDER_API_KEY not found. Check your .env file.")
    exit(1)
    
app = build_graph()


TRANSCRIPT_FILE = input("Enter the transcript file path (with extension, e.g., 'Time series session 01.vtt'): ").strip()
print("Preparing the File...")
INPUT_VIDEO_FILE = input("Enter the input video file path (with extension, e.g., 'Time Series Session 01.mp4'): ").strip()
print("Preparing the Video...")
INPUT_PROMPT = input("Enter the initial Main Topic of the lecture: ").strip()
print("Analyzing the Prompt...")

# 1. Point this to your Teams transcript file
output_file_name = TRANSCRIPT_FILE.split('.')[0]

print(f"Parsing transcript from {TRANSCRIPT_FILE}...")

# 2. Get the sliding window chunks (10 min window, 2 min overlap)
try:
    chunks = chunk_transcript(TRANSCRIPT_FILE, window_minutes=10, overlap_minutes=2)
except FileNotFoundError:
    print(f"❌ Error: Could not find '{TRANSCRIPT_FILE}'. Please create it in the root directory.")
    exit(1)
    
if not chunks:
    print("No text found to process. Check the file format.")
    exit(0)
    
print(f"Found {len(chunks)} chunks to process. Starting the Parrot Agent...\n")

# 3. Initialize the base state
current_state = {
    "main_topic": INPUT_PROMPT, # Adjust based on the lecture
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

# generate final lecture summary here
print("📝 Generating final lecture summary...")
final_summary = generate_summary(
    current_state["main_topic"],
    current_state["global_summary"]
)

with open(f"{output_file_name}_summary.txt", "w", encoding="utf-8") as f:
    f.write(f"Lecture Summary: {current_state['main_topic']}\n")
    f.write("=" * 50 + "\n\n")
    f.write(final_summary)

print(f"📝 Saved summary to {output_file_name}_summary.txt")



# Trigger the FFmpeg video editor
input_video = INPUT_VIDEO_FILE  # Make sure this matches your actual video file name
output_video = f"{output_file_name}_EditedClean.mp4"

# Check if the video file actually exists before trying to cut it
if os.path.exists(input_video):
    process_video(input_video, output_video, current_state["extracted_segments"])
else:
    print(f"\n⚠️ Video file '{input_video}' not found. Place it in the root folder to process the video.")