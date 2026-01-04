import time
from dotenv import load_dotenv
from runwayml import RunwayML

load_dotenv()

client = RunwayML()

task = client.character_performance.create({
  model: "act_two",
  character: {
    type: "image",
    uri: "https://obs.dimond.top/character.png"
  },
  reference: {
    type: "video",
    uri: "https://obs.dimond.top/reference.mp4"
  },
  seed: 3938610573,
  bodyControl: "False"
}).wait_for_task_output()

print('Task complete:', task)