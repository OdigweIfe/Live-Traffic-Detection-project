import cv2
import numpy as np

def extract_frames(video_path, every_n_frames=5):
    """
    Extract frames from a video file.
    
    Args:
        video_path (str): Path to video file.
        every_n_frames (int): Extract every Nth frame to save callbacks.
        
    Returns:
        tuple: (list of frames [numpy array], total_frames_processed)
    """
    frames = []
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    frame_count = 0
    total_processed = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % every_n_frames == 0:
            frames.append(frame)
            total_processed += 1
            
        frame_count += 1
        
    cap.release()
    return frames, total_processed

def save_frame(frame, path):
    """Save a frame to disk."""
    cv2.imwrite(path, frame)
