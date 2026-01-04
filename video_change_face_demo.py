import time
from dotenv import load_dotenv
from runwayml import RunwayML

load_dotenv()

client = RunwayML()

task = client.character_performance.create(
  model="act_two",
  character={
    "type": "image",
    "uri": "https://obs.dimond.top/character.png"
  },
  reference={
    "type": "video",
    "uri": "https://obs.dimond.top/reference.mp4"
  },
  seed=3938610573,
  # bodyControl might not be a valid kwarg if it expects snake_case, 
  # but let's try passing it as is or check if we should use a dict.
  # If the user copied from JS, it was likely a dict.
  # Let's try passing as kwargs which is standard for Python SDKs.
).wait_for_task_output()

print('Task complete:', task)