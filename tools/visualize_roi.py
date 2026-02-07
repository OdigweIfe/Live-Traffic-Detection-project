"""
Visualize ROI configuration on the first frame of a video.
"""
import cv2
import json
import argparse
import os
import sys

def visualize_roi(video_path, config_path, output_path):
    # Load config
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {video_path}")
        return
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Could not read frame")
        return

    # Draw elements
    vis_frame = frame.copy()
    
    # Draw Stop Lines
    for sl in config.get('stop_lines', []):
        pts = sl['points']
        p1 = tuple(pts[0])
        p2 = tuple(pts[1])
        cv2.line(vis_frame, p1, p2, (0, 0, 255), 4)
        cv2.putText(vis_frame, sl['name'], (p1[0], p1[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,0,255), 2)
        
    # Draw Speed Zones
    for sz in config.get('speed_zones', []):
        # Entry
        p1 = tuple(sz['entry_line'][0])
        p2 = tuple(sz['entry_line'][1])
        cv2.line(vis_frame, p1, p2, (0, 255, 0), 2)
        # Exit
        p3 = tuple(sz['exit_line'][0])
        p4 = tuple(sz['exit_line'][1])
        cv2.line(vis_frame, p3, p4, (0, 255, 0), 2)
        
        cv2.putText(vis_frame, sz['name'], (p1[0], p1[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    # Draw Lanes
    for lane in config.get('lane_boundaries', []):
        p1 = tuple(lane['left_boundary'][0])
        p2 = tuple(lane['left_boundary'][1])
        cv2.line(vis_frame, p1, p2, (0, 255, 255), 2)
        
        # Right boundary might be shared, but draw for completeness
        p3 = tuple(lane['right_boundary'][0])
        p4 = tuple(lane['right_boundary'][1])
        cv2.line(vis_frame, p3, p4, (0, 255, 255), 2)
        
        # Label
        cx = (p1[0] + p3[0]) // 2
        cy = (p1[1] + p2[1]) // 2
        cv2.putText(vis_frame, f"L{lane['lane_number']}", (cx, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)

    # Draw Traffic Signal ROI
    roi = config.get('traffic_signal_roi')
    if roi:
        p1 = tuple(roi[0])
        p2 = tuple(roi[1])
        cv2.rectangle(vis_frame, p1, p2, (255, 0, 0), 2)
        cv2.putText(vis_frame, "SIGNAL", (p1[0], p1[1]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
    
    cv2.imwrite(output_path, vis_frame)
    print(f"✅ Saved visualization to: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    visualize_roi(args.video, args.config, args.output)
