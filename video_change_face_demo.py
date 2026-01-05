import time
import sys
from dotenv import load_dotenv
from runwayml import RunwayML
import os

load_dotenv()

def run_runway_task(character_url, video_url):
    print(f"Starting RunwayML task with:")
    print(f"  Character: {character_url}")
    print(f"  Video: {video_url}")
    
    client = RunwayML(api_key=os.getenv("RUNWAYML_API_KEY"))

    try:
        task = client.character_performance.create(
          model="act_two",
          character={
            "type": "image",
            "uri": character_url
          },
          reference={
            "type": "video",
            "uri": video_url
          },
          seed=3938610573,
        )
        
        print("Task created. Waiting for completion...")
        task = task.wait_for_task_output()
        print('Task complete:', task)
        return task
    except Exception as e:
        print(f"RunwayML task failed: {e}")
        raise e

if __name__ == "__main__":
    # Allow running from command line with arguments
    if len(sys.argv) >= 3:
        char_url = sys.argv[1]
        vid_url = sys.argv[2]
        run_runway_task(char_url, vid_url)
    else:
        # Use placeholders or prompt
        print("Usage: python video_change_face_demo.py <character_url> <video_url>")
        # Example/Placeholder for testing if needed
        # run_runway_task("https://example.com/char.png", "https://example.com/vid.mp4")