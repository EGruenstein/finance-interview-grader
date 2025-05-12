from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Sample Q&A pairs (you’ll replace this with real ones later)
example_qa_pairs = [
    {
        "question": "Walk me through a DCF.",
        "answer": "A DCF values a company by projecting its free cash flows, discounting them using the WACC, and summing them with a terminal value to get enterprise value."
    },
    {
        "question": "Walk me through a DCF.",
        "answer": "In a DCF, you forecast the company's free cash flows over a 5-10 year period, then discount them using WACC and add a terminal value to estimate enterprise value."
    },
    {
        "question": "Walk me through a DCF.",
        "answer": "Discounted cash flow analysis estimates a firm's value based on projected future free cash flows and a terminal value, both discounted to present value using WACC."
    }
]

# Candidate answer (input from user)
candidate_answer = "A DCF projects future free cash flows, discounts them using WACC, and adds the terminal value to find enterprise value."

# Load embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Get example answer texts
example_answers = [qa["answer"] for qa in example_qa_pairs]

# Generate embeddings
example_embeddings = model.encode(example_answers)
candidate_embedding = model.encode([candidate_answer])

# Compute cosine similarity
similarities = cosine_similarity(candidate_embedding, example_embeddings)[0]

# Get top 2 most similar example answers
top_indices = similarities.argsort()[-2:][::-1]
top_examples = [example_answers[i] for i in top_indices]

# Print results
print("Most relevant examples to include in GPT prompt:\n")
for example in top_examples:
    print("-", example)