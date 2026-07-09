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
    """Renders the final edited (KEPT) video from the extracted segments."""
    merged_intervals = merge_intervals(extracted_segments)
    
    if not merged_intervals:
        print("No valid segments to process.")
        return


    # 1. Render the main edited video (The Gold)
    print(f"\n🎬 Rendering Output video ({len(merged_intervals)} clips) -> {output_video_path}")
    render_clips(input_video_path, output_video_path, merged_intervals, "temp_kept")
    
    print("\n✅ Edited video generated successfully!")