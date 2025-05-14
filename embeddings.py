import json
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load the file
input_file = "enterpriseval.json"

with open(input_file) as f:
    questions = json.load(f)

# Add embedding to each entry
for q in questions:
    if "embedding" not in q:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=[q["question"]]
        )
        q["embedding"] = response.data[0].embedding
        print(f"✅ Embedded: {q['question'][:50]}...")
        time.sleep(1)  # Optional: avoid hitting rate limits

# Save back
with open(input_file, "w") as f:
    json.dump(questions, f, indent=2)