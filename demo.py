import random
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

INTERVIEW_TEMPLATES = {
    "Bulge Bracket (7 easy, 7 medium)": {"easy": 7, "medium": 7, "hard": 0},
    "Boutique (7 medium, 7 hard)": {"easy": 0, "medium": 7, "hard": 7},
    "Buy-Side/Evercore (4 easy, 10 hard)": {"easy": 4, "medium": 0, "hard": 10}
}

if "used_questions" not in st.session_state:
    st.session_state.used_questions = set()

# -------- Step 2: Load questions grouped by section --------
@st.cache_data
def load_question_bank_by_section(folder="questions"):
    section_data = {}
    for file in os.listdir(folder):
        if file.endswith(".json"):
            section = file.replace(".json", "")
            with open(os.path.join(folder, file)) as f:
                data = json.load(f)
                section_data[section] = data
    return section_data

import random
from collections import defaultdict

def generate_interview(template_name, section_data):
    template = INTERVIEW_TEMPLATES[template_name]
    used_hashes = st.session_state.used_questions
    section_counts = defaultdict(int)
    quotas = template.copy()
    final_questions = []

    # Build difficulty pools
    pools = {level: [] for level in quotas}
    for difficulty in quotas:
        for section, questions in section_data.items():
            for q in questions:
                if q.get("difficulty") == difficulty and hash(q["question"]) not in used_hashes:
                    question = q.copy()
                    question["section"] = section
                    pools[difficulty].append(question)
        random.shuffle(pools[difficulty])  # Shuffle within each difficulty

    while sum(quotas.values()) > 0:
        # Make weighted list of difficulties that still have quota left
        available_difficulties = [
            d for d in quotas for _ in range(quotas[d]) if pools[d]
        ]
        if not available_difficulties:
            break  # No more questions to pick

        chosen_diff = random.choice(available_difficulties)
        # Try to find a question with < 2 in that section
        picked = None
        for idx, q in enumerate(pools[chosen_diff]):
            if section_counts[q["section"]] < 2:
                picked = q
                del pools[chosen_diff][idx]
                break

        if picked:
            final_questions.append(picked)
            used_hashes.add(hash(picked["question"]))
            section_counts[picked["section"]] += 1
            quotas[chosen_diff] -= 1
        else:
            # Couldn't find one with valid section limit; mark as skipped
            quotas[chosen_diff] -= 1  # Drop quota to avoid infinite loop

    if sum(template.values()) != len(final_questions):
        st.warning(f"⚠️ Only generated {len(final_questions)} of {sum(template.values())} questions.")

    return final_questions




def grade_answer(question, example, answer, client):
    if len(answer.strip().split()) < 5:
        return "Score: 0/10\nJustification: The answer is too short."

    grading_prompt = f"""
You are a senior finance interviewer evaluating a candidate's answer.

Rules:
- If the answer is under 5 words, give 0/10.
- Otherwise, grade from 1 to 10 based on accuracy, clarity, and completeness.

Respond using:
Score: X/10  
Justification: <your explanation>

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

st.title("Finance Interview Builder")

section_data = load_question_bank_by_section()

interview_type = st.selectbox("Choose interview type", list(INTERVIEW_TEMPLATES.keys()))

if st.button("Generate Interview"):
    questions = generate_interview(interview_type, section_data)

    if not questions:
        st.error("No questions could be generated.")
    else:
        st.session_state.questions = questions
        st.session_state.answers = [""] * len(questions)
        st.session_state.feedback = []
        st.session_state.submitted = False
        st.rerun()

if "questions" in st.session_state:
    st.title("Mock Interview")

    for i, q in enumerate(st.session_state.questions):
        # st.markdown(f"### Q{i+1}: ({q['section'].capitalize()} — {q['difficulty'].capitalize()})")
        st.markdown(f"### Q{i+1}:")
        st.write(q["question"])
        st.session_state.answers[i] = st.text_area(
            f"Your Answer to Q{i+1}", 
            value=st.session_state.answers[i],
            key=f"answer_{i}"
        )
        # with st.expander("💡 Example Answer"):
        #     st.write(q["example"])

    if st.button("Submit Interview for Grading"):
        st.session_state.submitted = True
        st.rerun()


if st.session_state.get("submitted"):
    st.title("✅ Interview Feedback")

    if not st.session_state.feedback:
        st.session_state.feedback = []

        for i, q in enumerate(st.session_state.questions):
            user_ans = st.session_state.answers[i]
            fb = grade_answer(q["question"], q["example"], user_ans, client)
            st.session_state.feedback.append(fb)

    for i, q in enumerate(st.session_state.questions):
        st.markdown(f"### Q{i+1}: ({section.capitalize()} — {q['difficulty'].capitalize()})")
        st.markdown(f"**Your Answer:** {st.session_state.answers[i]}")
        st.markdown(f"**Feedback:** {st.session_state.feedback[i]}")

if st.button("Create New Interview"):
    st.session_state.questions = []
    st.session_state.answers = []
    st.session_state.feedback = []
    st.session_state.submitted = False
    st.rerun()

if st.button("Reset Previously Answered Questions"):
    st.session_state.clear()
    st.rerun()