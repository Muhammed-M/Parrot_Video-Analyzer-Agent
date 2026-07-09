import os
import subprocess
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_audio_sample(video_path: str, audio_path: str, duration_mins: int = 5):
    """
    Extracts a lightweight audio sample from the video using FFmpeg.
    We compress it to a 64k mono MP3 to keep the file size incredibly small.
    """
    print(f"🎵 Extracting the first {duration_mins} minutes of audio...")
    duration_secs = duration_mins * 60
    
    command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", video_path,
        "-t", str(duration_secs),    # Only take the first X minutes for testing
        "-vn",                       # No video, audio only
        "-acodec", "libmp3lame",     # MP3 codec
        "-ac", "1",                  # Mono channel
        "-ar", "16000",              # 16kHz sample rate (optimal for Whisper)
        "-b:a", "64k",               # 64 kbps bitrate
        audio_path
    ]
    
    subprocess.run(command, check=True)
    print(f"✅ Audio extracted to {audio_path}")

def transcribe_with_groq(audio_path: str, output_vtt_path: str):
    """
    Sends the audio file to Groq's Whisper Large V3 model 
    and requests the output directly in VTT format.
    """
    print("🎙️ Sending to Groq Whisper API (This takes a few seconds)...")
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # Check file size (Groq limit is 25MB)
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    print(f"📊 Audio file size: {file_size_mb:.2f} MB")
    
    with open(audio_path, "rb") as audio_file:
        # We can request 'vtt', 'srt', 'json', or 'text'
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model="whisper-large-v3",
            response_format="vtt", 
            temperature=0.0 # Keep it deterministic
        )
        
    # Save the VTT file
    with open(output_vtt_path, "w", encoding="utf-8") as f:
        f.write(transcription)
        
    print(f"✅ Transcription saved to {output_vtt_path}")

if __name__ == "__main__":
    # --- ISOLATED TEST BLOCK ---
    # Place a test video in your root directory
    TEST_VIDEO = "Time Series Session 01.mp4" 
    TEMP_AUDIO = "temp_audio.mp3"
    FINAL_VTT = "groq_test_transcript.vtt"
    
    if not os.path.exists(TEST_VIDEO):
        print(f"❌ Error: Please place '{TEST_VIDEO}' in the root directory to test.")
        exit(1)
        
    try:
        # Extract just 5 minutes to test quality without hitting the 7.2k ASH limit
        extract_audio_sample(TEST_VIDEO, TEMP_AUDIO, duration_mins=5)
        
        # Transcribe it
        transcribe_with_groq(TEMP_AUDIO, FINAL_VTT)
        
    finally:
        # Clean up the heavy MP3 file after testing
        if os.path.exists(TEMP_AUDIO):
            os.remove(TEMP_AUDIO)
            print("🧹 Cleaned up temporary audio file.")
            
    print("\n🎉 Test Complete! Open 'groq_test_transcript.vtt' to check the quality.")