import json
import os
import comfy_utils

# This will auto-discover the server
client = comfy_utils.client 
TASK_ID = "7136715d-cdbd-40e5-b598-696dec7e11d8"

print(f"Using server: {client.server_address}")

history = client.get_history(TASK_ID)
print(json.dumps(history, indent=2))
