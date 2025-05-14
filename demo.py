import streamlit as st
from openai import OpenAI
import os
import json
import numpy as np
# from dotenv import load_dotenv


# load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
with open("qa_with_embeddings.json") as f:
    qa_data = json.load(f)

for q in qa_data:
    q["embedding"] = np.array(q["embedding"])

if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = set()


def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text]
    )
    return response.data[0].embedding

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def get_best_question(user_query):
    try:
        query_vec = np.array(get_embedding(user_query))

        # Filter out already asked questions
        unseen = [q for i, q in enumerate(qa_data) if i not in st.session_state.asked_questions]
        if not unseen:
            return None

        best_idx, best_q = max(
            enumerate(unseen),
            key=lambda pair: cosine_similarity(query_vec, pair[1]["embedding"])
        )

        # Find the index in the original qa_data so we can track it
        real_index = qa_data.index(unseen[best_idx])
        st.session_state.asked_questions.add(real_index)

        return unseen[best_idx]
    except Exception as e:
        print("Error in get_best_question:", e)
        return None


# st.title("📊 Finance Interview Question Bot")

# user_query = st.text_input("What type of finance question would you like?")

# if user_query:
#     question, example = get_best_question(user_query)
#     st.subheader("🧠 Suggested Question:")
#     st.write(question)
#     with st.expander("💡 Example Answer"):
#         st.write(example)



def grade_answer(question, example, answer):
    if len(answer.strip().split()) < 3:
        return "Score: 0/10\nJustification: The answer is too short (fewer than 3 words)."

    grading_prompt = f"""
        You are a senior finance interviewer evaluating a candidate's answer. Compare it to the example and score from 1 to 10 based on accuracy, clarity, and completeness.

        Respond using this format exactly:
        Score: X/10  
        Justification: <your reasoning>

        ---

        Question: {question}

        Example Answer: {example}

        Candidate Answer: {answer}
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a strict but fair finance interviewer."},
            {"role": "user", "content": grading_prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# Streamlit UI
# 🧠 Initialize session state
if "stage" not in st.session_state:
    st.session_state.stage = "ask"  # stages: ask, answer, feedback
    st.session_state.selected = None
    st.session_state.feedback = ""

st.title("Finance Interview")

# 🎯 Stage: Ask
if st.session_state.stage == "ask":
    user_query = st.text_input("Enter a topic or type of question:")

    if user_query:
        with st.spinner("Finding the best question..."):
            selected = get_best_question(user_query)

        if selected:
            st.session_state.selected = selected
            st.session_state.stage = "answer"
            st.rerun()
        else:
            st.error("❌ Could not find a matching question. Try a different topic.")

# 📝 Stage: Answer
elif st.session_state.stage == "answer":
    selected = st.session_state.selected

    st.subheader("Suggested Question:")
    st.write(selected["question"])
    # with st.expander("Example Answer"):
    #     st.write(selected[1])

    user_answer = st.text_area("Your Answer:")

    if st.button("Submit Answer for Grading"):
        with st.spinner("Grading your answer..."):
            feedback = grade_answer(selected["question"], selected["example"], user_answer)
            st.session_state.feedback = feedback
            st.session_state.user_answer = user_answer
            st.session_state.stage = "feedback"
            st.rerun()

    if st.button("🔁 Ask Another Question"):
        st.session_state.stage = "ask"
        st.session_state.selected = None
        st.session_state.feedback = ""
        st.rerun()

# ✅ Stage: Feedback
elif st.session_state.stage == "feedback":
    st.subheader("Question")
    st.write(st.session_state.selected["question"])

    st.subheader("Your Answer")
    st.write(st.session_state.user_answer)

    st.subheader("Grading Feedback")
    st.markdown(st.session_state.feedback)

    if st.button("🔁 Ask Another Question"):
        st.session_state.stage = "ask"
        st.session_state.selected = None
        st.session_state.feedback = ""
        st.rerun()
