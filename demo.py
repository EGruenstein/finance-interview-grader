import streamlit as st
from openai import OpenAI
import os
import json
import time

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
with open("examples.json") as f:
    examples = json.load(f)

time_limit = 120

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

def grade_answer(question, example, answer, client):
    if len(answer.strip().split()) == 0:
        return "Score: 0/10\nJustification: No answer given"
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

def generate_interview(template_name, section_data):
    template = INTERVIEW_TEMPLATES[template_name]
    used_hashes = st.session_state.used_questions
    section_counts = {sec: 0 for sec in section_data.keys()}
    quotas = template.copy()
    final_questions = []

    # Create pools by difficulty
    pools = {level: [] for level in quotas}
    for difficulty in quotas:
        for section, questions in section_data.items():
            for q in questions:
                if q.get("difficulty") == difficulty and hash(q["question"]) not in used_hashes:
                    q = q.copy()
                    q["section"] = section
                    pools[difficulty].append(q)
        random.shuffle(pools[difficulty])

    max_per_section = 2
    fallback_used = False

    while sum(quotas.values()) > 0:
        available_difficulties = [
            d for d in quotas for _ in range(quotas[d]) if pools[d]
        ]
        if not available_difficulties:
            break

        chosen_diff = random.choice(available_difficulties)

        picked = None
        for idx, q in enumerate(pools[chosen_diff]):
            sec = q["section"]
            if section_counts[sec] < max_per_section:
                picked = q
                del pools[chosen_diff][idx]
                break

        # If we couldn't find one with section room, relax the rule
        if not picked and not fallback_used:
            fallback_used = True
            max_per_section = 3  # Loosen cap
            continue

        if picked:
            final_questions.append(picked)
            section_counts[picked["section"]] += 1
            quotas[chosen_diff] -= 1
            used_hashes.add(hash(picked["question"]))

    if sum(template.values()) != len(final_questions):
        st.warning(f"⚠️ Only generated {len(final_questions)} of {sum(template.values())} questions. Check question pool balance.")

    return final_questions



if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.answers = []
    st.session_state.feedback = []
    st.session_state.completed = False


st.title("Finance Interview Grader")
st.write("Answer 3 finance interview questions and receive feedback and an overall evaluation.")

section_data = load_question_bank_by_section()

interview_type = st.selectbox("Choose interview type", list(INTERVIEW_TEMPLATES.keys()))

if st.button("Generate Interview"):
    qa_list = generate_interview(interview_type, section_data)

    if not qa_list:
        st.error("No questions could be generated.")
    else:
        st.session_state.last_check = time.time()
        st.session_state.start_time = time.time()
        st.session_state.timeout = time_limit  # seconds
        st.session_state.questions = qa_list
        st.session_state.answers = [""] * len(qa_list)
        st.session_state.feedback = [""] * len(qa_list) 
        st.session_state.index = 0
        st.session_state.completed = False
        st.session_state.submitted_current = False
        st.session_state.waiting_next = False
        st.session_state.disabled_input = False
        st.session_state.timer_expired = False
        st.rerun()

if "questions" in st.session_state and st.session_state.questions:
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "submitted_current" not in st.session_state:
        st.session_state.submitted_current = False
    if "waiting_next" not in st.session_state:
        st.session_state.waiting_next = False
    if "disabled_input" not in st.session_state:
        st.session_state.disabled_input = False
    
    questions = st.session_state.questions
    idx = st.session_state.index


    if idx < len(questions):
        q = questions[idx]
        question = q["question"]
        example = q["example"]

        if not st.session_state.submitted:
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, time_limit - int(elapsed))
            if remaining <= 0 and not st.session_state.timer_expired:
                st.session_state.timer_expired = True
        else:
            remaining = 0  # Freeze timer after submission

      

        st.subheader(f"Question {idx + 1} of {len(questions)}")
     
        st.markdown(f"### {question}")
        st.write(f"Time remaining: **{remaining} seconds**")

        # # Show text input
        # disabled = False
        st.session_state.answers[idx] = st.text_area(
            "Your Answer", 
            value=st.session_state.answers[idx], 
            key=f"answer_{idx}", 
            disabled=st.session_state.disabled_input
        )


        if st.session_state.timer_expired and not st.session_state.submitted_current:
            st.warning("⏱️ Time's up! Submitting your answer...")
            
            feedback = grade_answer(question, example, st.session_state.answers[idx], client)
            st.session_state.feedback[idx] = feedback
            st.session_state.submitted_current = True
            st.session_state.waiting_next = True
            st.session_state.disabled_input = True
            st.session_state.timer_expired = False  # Reset for next question
            st.experimental_rerun()

        if not st.session_state.submitted_current:
            submit = st.button("Submit Answer")

            if submit or remaining<=0:
                with st.spinner("Grading..."):
                    latest_answer = st.session_state.get(f"answer_{idx}", "").strip()
                    st.session_state.answers[idx] = latest_answer
                    feedback = grade_answer(question, example, latest_answer, client)
                    st.session_state.feedback[idx] = feedback
                    st.session_state.submitted_current = True
                    st.session_state.waiting_next = True
                    st.session_state.disabled_input = True
                    st.rerun()
        else:
            st.info("Answer submitted")

        if st.session_state.waiting_next:
            with st.container():
                if st.button("Next Question"):
                    st.session_state.index += 1
                    st.session_state.start_time = time.time()
                    st.session_state.submitted_current = False
                    st.session_state.waiting_next = False
                    st.session_state.disabled_input = False
                    st.rerun()

        if not st.session_state.submitted_current:
            time.sleep(1)
            st.rerun()

    else:
        st.session_state.completed = True
        st.header("📋 Interview Summary")

        for i, q in enumerate(questions):
            st.subheader(f"Q{i+1}: {q['question']}")
            st.markdown(f"**Your Answer:** {st.session_state.answers[i]}")
            st.markdown(f"**Feedback:** {st.session_state.feedback[i]}")

        if st.button("Get Overall Evaluation"):
            with st.spinner("Generating overall evaluation..."):
                summary_prompt = "You are a senior finance interviewer. Below is a summary of the candidate’s responses and feedback:\n\n"
                for i, q in enumerate(questions):
                    summary_prompt += f"Q{i+1}: {q['question']}\n"
                    summary_prompt += f"A: {st.session_state.answers[i]}\n"
                    summary_prompt += f"Feedback: {st.session_state.feedback[i]}\n\n"
                summary_prompt += "Provide an overall score (out of 10) and a short summary. Start with 'Overall Score: X/10'."

                try:
                    overall_res = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a senior finance interviewer."},
                            {"role": "user", "content": summary_prompt}
                        ]
                    )
                    overall_feedback = overall_res.choices[0].message.content.strip()
                    st.success("🧾 Overall Evaluation")
                    st.markdown(overall_feedback)
                except Exception as e:
                    st.error("Failed to generate overall evaluation.")
                    st.text(str(e))
        if st.button("Create New Interview"):
            st.session_state.questions = []
            st.session_state.answers = []
            st.session_state.feedback = []
            st.session_state.submitted = False
            st.rerun()

        if st.button("Reset Previously Answered Questions"):
            st.session_state.clear()
            st.rerun()