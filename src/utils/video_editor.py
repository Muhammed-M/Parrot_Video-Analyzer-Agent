import os
import subprocess
from datetime import datetime

def time_to_seconds(time_str: str) -> int:
    """Converts HH:MM:SS or MM:SS format to total seconds."""
    time_str = time_str.strip()
    if time_str.count(':') == 1:
        time_str = "00:" + time_str
        
    pt = datetime.strptime(time_str, '%H:%M:%S')
    return pt.second + pt.minute * 60 + pt.hour * 3600

def merge_intervals(segments: list) -> list:
    """Merges overlapping or adjacent timestamp intervals."""
    if not segments:
        return []

    intervals = []
    for seg in segments:
        start = time_to_seconds(seg['start_time'])
        end = time_to_seconds(seg['end_time'])
        if start < end:
            intervals.append([start, end])

    intervals.sort(key=lambda x: x[0])

    merged = [intervals[0]]
    for current in intervals[1:]:
        previous = merged[-1]
        
        # THE SMOOTHING FILTER: 
        # If the next clip starts within 25 seconds of the previous clip ending, 
        # just merge them together. This prevents jarring micro-cuts in the final video.
        if current[0] <= previous[1] + 25: 
            previous[1] = max(previous[1], current[1])
        else:
            merged.append(current)

    return merged

def get_video_duration(video_path: str) -> int:
    """Uses ffprobe to get the total duration of the video in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True
        )
        return int(float(result.stdout.strip()))
    except Exception as e:
        print(f"⚠️ Could not get video duration via ffprobe. Error: {e}")
        return None

def invert_intervals(merged_intervals: list, total_duration: int) -> list:
    """Calculates the 'negative space' gaps between the kept intervals."""
    discarded = []
    current_time = 0
    
    for start, end in merged_intervals:
        if start > current_time:
            # Only keep the gap if it's longer than 1 second
            if (start - current_time) >= 1:
                discarded.append([current_time, start])
        # Move our tracker to the end of the kept clip
        current_time = max(current_time, end)
        
    # Catch any remaining discarded footage at the end of the video
    if total_duration and current_time < total_duration:
         if (total_duration - current_time) >= 1:
            discarded.append([current_time, total_duration])
        
    return discarded

def render_clips(input_video_path: str, output_video_path: str, intervals: list, temp_folder: str):
    """Helper function that executes the FFmpeg cutting and concatenation."""
    if not intervals:
        return
        
    os.makedirs(temp_folder, exist_ok=True)
    concat_list_path = os.path.join(temp_folder, "concat_list.txt")
    clip_files = []

    for i, (start_sec, end_sec) in enumerate(intervals):
        clip_name = f"clip_{i:03d}.mp4"
        clip_path = os.path.join(temp_folder, clip_name)
        clip_files.append(clip_path)
        
        command = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", str(start_sec),
            "-to", str(end_sec),
            "-i", input_video_path,
            "-c", "copy",
            clip_path
        ]
        subprocess.run(command, check=True)

    with open(concat_list_path, 'w') as f:
        for clip in clip_files:
            abs_path = os.path.abspath(clip).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")

    concat_command = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_list_path,
        "-c", "copy",
        output_video_path
    ]
    subprocess.run(concat_command, check=True)

    # Clean up temp files for this specific render batch
    for clip in clip_files:
        if os.path.exists(clip):
            os.remove(clip)
    if os.path.exists(concat_list_path):
        os.remove(concat_list_path)
    os.rmdir(temp_folder)

def process_video(input_video_path: str, output_video_path: str, extracted_segments: list):
    """Orchestrates creating both the KEPT and DISCARDED final videos."""
    merged_intervals = merge_intervals(extracted_segments)
    
    if not merged_intervals:
        print("No valid segments to process.")
        return

    print("\n🎥 Analyzing video duration to calculate discarded gaps...")
    total_duration = get_video_duration(input_video_path)
    
    if not total_duration:
        # Fallback if ffprobe fails: assume video ends right after the last kept clip
        total_duration = merged_intervals[-1][1] 

    discarded_intervals = invert_intervals(merged_intervals, total_duration)

    # 1. Render the main edited video (The Gold)
    print(f"\n🎬 Rendering KEPT video ({len(merged_intervals)} clips) -> {output_video_path}")
    render_clips(input_video_path, output_video_path, merged_intervals, "temp_kept")

    # 2. Setup output name and render the garbage video (The QA Test)
    dir_name, file_name = os.path.split(output_video_path)
    name, ext = os.path.splitext(file_name)
    discarded_output_path = os.path.join(dir_name, f"{name}_DISCARDED{ext}")

    print(f"\n🗑️ Rendering DISCARDED video ({len(discarded_intervals)} clips) -> {discarded_output_path}")
    render_clips(input_video_path, discarded_output_path, discarded_intervals, "temp_discarded")
    
    print("\n✅ Both videos generated successfully!")