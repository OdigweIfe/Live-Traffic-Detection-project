import os
import uuid
import subprocess

try:
    from moviepy.editor import VideoFileClip
    HAS_MOVIEPY = True
except ImportError:
    HAS_MOVIEPY = False

def extract_clip(source_path, output_folder, violation_time_seconds, duration=5.0):
    """
    Extracts a clip around the violation time.
    Tries moviepy first, falls back to system ffmpeg.
    
    Args:
        source_path (str): Path to the full source video.
        output_folder (str): Folder to save the clip.
        violation_time_seconds (float): Time of violation in seconds.
        duration (float): Total duration of the clip (default 5s).
        
    Returns:
        str: Filename of the generated clip, or None if failed.
    """
    try:
        # Calculate start and end times
        half_duration = duration / 2
        start_time = max(0, violation_time_seconds - half_duration)
        
        # Generate unique filename
        filename = f"clip_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(output_folder, filename)

        if HAS_MOVIEPY:
            print("Using moviepy for clipping...")
            with VideoFileClip(source_path) as video:
                # Ensure we don't go past end
                end_time = min(video.duration, start_time + duration)
                clip = video.subclip(start_time, end_time)
                
                clip.write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    temp_audiofile=f'temp-audio-{uuid.uuid4().hex[:8]}.m4a',
                    remove_temp=True,
                    logger=None
                )
                return filename
        else:
            print("Using system ffmpeg for clipping...")
            # Fallback to subprocess
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-i', source_path,
                '-t', str(duration),
                '-c:v', 'libx264',
                '-c:a', 'aac',
                output_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"Clip created successfully: {output_path}")
                return filename
            else:
                print("ffmpeg command failed to create output file.")
                return None
            
    except Exception as e:
        print(f"Error extracting clip: {e}")
        return None
