import time
from dotenv import load_dotenv
from runwayml import RunwayML
import os

load_dotenv()

client = RunwayML(api_key=os.getenv("RUNWAYML_API_KEY"))

task = client.character_performance.create(
  model="act_two",
  character={
    "type": "image",
    "uri": "https://lh3.googleusercontent.com/d/1Xy_QyXz_Xy_QyXz_Xy_QyXz_Xy_QyXz" # Replace with your actual Google Drive direct link for character.png
  },
  reference={
    "type": "video",
    "uri": "https://lh3.googleusercontent.com/d/1Xy_QyXz_Xy_QyXz_Xy_QyXz_Xy_QyXz" # Replace with your actual Google Drive direct link for reference.mp4
  },
  seed=3938610573,
  # bodyControl might not be a valid kwarg if it expects snake_case, 
  # but let's try passing it as is or check if we should use a dict.
  # If the user copied from JS, it was likely a dict.
  # Let's try passing as kwargs which is standard for Python SDKs.
).wait_for_task_output()

print('Task complete:', task)