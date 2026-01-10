import comfy_utils
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Use the client from comfy_utils (auto-discovers server)
client = comfy_utils.client

print(f"Connected to: {client.server_address}")

# Fetch the queue
queue = client.get_queue()
print("Queue Data:")
print(json.dumps(queue, indent=2))

# Test is_task_running logic
pending = queue.get('queue_pending', [])
running = queue.get('queue_running', [])

print(f"Pending tasks count: {len(pending)}")
print(f"Running tasks count: {len(running)}")

# List pending task IDs
for task in pending:
    # task format is typically [prompt_id, prompt_id, workflow, client_id, ...]
    # wait, comfy_utils expects task[1] == prompt_id
    print(f"Pending Task: {task}")

for task in running:
    print(f"Running Task: {task}")
