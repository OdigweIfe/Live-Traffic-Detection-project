from app import create_app
from app.utils.video_clip import extract_clip
import os

app = create_app()

def test_clipping():
    # Use one of the existing processed videos
    source_dir = os.path.join(app.root_path, 'static', 'processed')
    output_dir = os.path.join(app.root_path, 'static', 'violations')
    
    # Use specific large video
    source_video = os.path.join(source_dir, 'processed_3367b2fa-98ee-4fa6-9fe3-ae279e24dea3_traffic_cam_01.mp4')
            
    if not os.path.exists(source_video):
        print(f"Source video not found: {source_video}")
        return

    print(f"Testing clip extraction from: {source_video}")
    
    # Extract clip at 10 seconds
    clip_name = extract_clip(source_video, output_dir, 10.0, duration=5.0)
    
    if clip_name:
        clip_path = os.path.join(output_dir, clip_name)
        print(f"Clip generated: {clip_path}")
        print(f"Size: {os.path.getsize(clip_path)} bytes")
    else:
        print("Clip generation failed.")

if __name__ == "__main__":
    test_clipping()
