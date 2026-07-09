import re
from datetime import datetime, timedelta

def parse_time(time_str: str) -> datetime:
    """Parses timestamp strings, stripping milliseconds from Teams VTT files."""
    # Split off the milliseconds (e.g., 00:23:05.759 -> 00:23:05)
    time_str = time_str.split('.')[0].strip()
    
    if len(time_str.split(':')) == 2:
        time_str = "00:" + time_str  # Convert MM:SS to HH:MM:SS
        
    return datetime.strptime(time_str, "%H:%M:%S")

def clean_teams_text(text: str) -> str:
    """Converts Teams <v Speaker>text</v> tags into readable 'Speaker: Text' format."""
    # Matches <v Speaker Name>The actual text</v>
    speaker_pattern = re.compile(r'<v\s+([^>]+)>(.*?)</v>')
    match = speaker_pattern.search(text)
    
    if match:
        speaker_name = match.group(1).strip()
        spoken_text = match.group(2).strip()
        return f"{speaker_name}: {spoken_text}"
        
    return text.strip()

def chunk_transcript(file_path: str, window_minutes: int = 5, overlap_minutes: int = 1) -> list:
    """
    Parses a Microsoft Teams VTT file and returns a list of text chunks 
    grouped into sliding windows.
    """
    segments = []
    
    # Matches the start time of the Teams format: 00:23:05.759 --> 00:23:07.039
    timestamp_pattern = re.compile(r'^(\d{2}:\d{2}:\d{2}(?:\.\d{3})?)\s*-->')
    
    # Matches the useless Teams UUID lines (e.g., 76208cd8-883a-4d04-bac9-4244b700cd39/189-0)
    uuid_pattern = re.compile(r'^[a-f0-9\-]+/\d+-\d+$')

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_timestamp = None
    
    # Step 1: Parse file into clean tuples of (timestamp_str, text_line)
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and Teams UUID metadata lines
        if not line or uuid_pattern.match(line):
            continue
            
        # Check if the line is a timestamp line
        ts_match = timestamp_pattern.search(line)
        if ts_match:
            current_timestamp = ts_match.group(1)
            continue
            
        # If we have an active timestamp and it's not metadata/time, it must be the spoken text
        if current_timestamp:
            cleaned_line = clean_teams_text(line)
            segments.append((current_timestamp, cleaned_line))
            current_timestamp = None # Reset to avoid attaching next line to old timestamp if format breaks

    if not segments:
        return []

    # Step 2: Group segments into sliding windows
    chunks = []
    start_anchor = parse_time(segments[0][0])
    end_anchor = start_anchor + timedelta(minutes=window_minutes)
    
    current_chunk_data = []
    
    for timestamp_str, text in segments:
        line_time = parse_time(timestamp_str)
        formatted_ts = timestamp_str.split('.')[0] # Clean timestamp for the LLM prompt
        
        if line_time < end_anchor:
            current_chunk_data.append(f"[{formatted_ts}] {text}")
        else:
            chunks.append("\n".join(current_chunk_data))
            
            # Slide the window forward
            start_anchor = start_anchor + timedelta(minutes=window_minutes - overlap_minutes)
            end_anchor = start_anchor + timedelta(minutes=window_minutes)
            
            # Re-evaluate overlapping lines
            current_chunk_data = [
                f"[{ts.split('.')[0]}] {txt}" for ts, txt in segments 
                if start_anchor <= parse_time(ts) < end_anchor
            ]
            
            if f"[{formatted_ts}] {text}" not in current_chunk_data:
                current_chunk_data.append(f"[{formatted_ts}] {text}")

    if current_chunk_data:
        chunks.append("\n".join(current_chunk_data))

    return chunks