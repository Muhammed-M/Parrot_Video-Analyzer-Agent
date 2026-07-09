import os
import subprocess
from groq import Groq
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def extract_one_hour_audio(video_path: str, audio_path: str):
    """
    Extracts exactly 60 minutes of audio.
    Compresses to 32kbps mono to ensure the 1-hour file stays well under Groq's 25MB limit.
    """
    print("🎵 Extracting the first 60 minutes of audio...")
    start_time = time.time()
    
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", video_path,
        "-t", "3600",                # Exactly 3600 seconds (1 hour)
        "-vn",                       # No video
        "-acodec", "libmp3lame",     # MP3 codec
        "-ac", "1",                  # Mono channel
        "-ar", "16000",              # 16kHz sample rate
        "-b:a", "32k",               # 32 kbps bitrate (crucial for file size)
        audio_path
    ]
    
    subprocess.run(command, check=True)
    
    # Verify file size
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"✅ Audio extracted in {time.time() - start_time:.1f} seconds.")
    print(f"📊 Compressed File Size: {file_size_mb:.2f} MB (Must be under 25.00 MB)")

def format_vtt_time(seconds: float) -> str:
    """Helper to convert raw seconds into VTT format (HH:MM:SS.mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def transcribe_hour_with_groq(audio_path: str, output_vtt_path: str):
    """
    Sends the 1-hour audio file to Groq, requests verbose JSON, 
    and manually constructs the VTT file.
    """
    print("\n🎙️ Sending 1 hour of audio to Groq Whisper API...")
    print("⏳ Waiting for API response (This may take 30 to 90 seconds)...")
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"), timeout=300.0)
    start_time = time.time()
    
    with open(audio_path, "rb") as audio_file:
        # Request verbose_json to get the segment timestamps
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model="whisper-large-v3",
            response_format="verbose_json", 
            temperature=0.0,
            language="ar"
        )
        
    print(f"✅ Transcription received from API in {time.time() - start_time:.1f} seconds!")
    print("📝 Formatting data into VTT file...")
    
    # Manually construct the VTT file from the JSON segments
    with open(output_vtt_path, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        
        # Groq returns an object with a 'segments' attribute
        segments = getattr(transcription, 'segments', [])
        
        # Fallback if it returns a dictionary instead of an object
        if not segments and isinstance(transcription, dict):
            segments = transcription.get('segments', [])
            
        for segment in segments:
            # Handle both dictionary and object access gracefully
            start = segment['start'] if isinstance(segment, dict) else segment.start
            end = segment['end'] if isinstance(segment, dict) else segment.end
            text = segment['text'] if isinstance(segment, dict) else segment.text
            
            start_fmt = format_vtt_time(start)
            end_fmt = format_vtt_time(end)
            
            # Write the VTT block
            f.write(f"{start_fmt} --> {end_fmt}\n")
            f.write(f"{text.strip()}\n\n")
            
    print(f"✅ Saved perfectly to: {output_vtt_path}")

if __name__ == "__main__":
    # Ensure your video file is named correctly and placed in the root folder
    TEST_VIDEO = "Time Series Session 01.mp4" 
    TEMP_AUDIO = "temp_1hour_audio.mp3"
    FINAL_VTT = "groq_1hour_test.vtt"
    
    if not os.path.exists(TEST_VIDEO):
        print(f"❌ Error: Could not find '{TEST_VIDEO}'. Check the file name and location.")
        exit(1)
        
    try:
        extract_one_hour_audio(TEST_VIDEO, TEMP_AUDIO)
        transcribe_hour_with_groq(TEMP_AUDIO, FINAL_VTT)
    finally:
        # Clean up the compressed audio file to save disk space
        if os.path.exists(TEMP_AUDIO):
            os.remove(TEMP_AUDIO)