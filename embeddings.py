from openai import OpenAI
import json
import numpy as np
import os
import time
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text]
    )
    return response.data[0].embedding

# Load your question data
with open("finance_interview_cleaned_qa.json") as f:
    qa_data = json.load(f)

# Add embeddings (if not already there)
for i, q in enumerate(qa_data):
    if "embedding" not in q:
        q["embedding"] = get_embedding(q["question"])
        print(f"Embedded {i + 1}/{len(qa_data)}")
        time.sleep(1)  # optional: slow down to avoid rate limit

# Save to a new file
with open("qa_with_embeddings.json", "w") as f:
    json.dump(qa_data, f)