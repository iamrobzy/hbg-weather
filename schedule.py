import modal
import requests
import os
import sys

image = (
    modal.Image.debian_slim(python_version="3.10")
    .pip_install("requests","python-dotenv")
)

app = modal.App("build-scheduler",image=image)
SPACE_ID = "Robzy/hbg-weather"  # Replace with your Space ID

# Define a Modal function
@app.function(schedule=modal.Period(hours=0, minutes=2),
              secrets=[modal.Secret.from_dotenv()])  # Run every 2 minutes
def trigger_rebuild():
    import os
    import requests

    token = os.environ['HF_TOKEN']  # Your Hugging Face token
    repo_id = "Robzy/hbg-weather"  # Replace with your Space's repo ID

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"https://api.huggingface.co/spaces/{repo_id}/rebuild"

    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        print("Space rebuild triggered successfully!")
    else:
        print(f"Failed to trigger rebuild: {response.status_code}, {response.text}")

if __name__ == "__main__":
    trigger_rebuild()