import streamlit as st
import requests
import json

# Load example Q&A pairs
with open("examples.json") as f:
    examples = json.load(f)

qa_list = examples[:3]  # Pick any 3 questions for demo

# Session state to store progress
if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.answers = []
    st.session_state.feedback = []

st.title("Finance Interview Grader Demo")
st.write("Answer the following 3 interview questions. You'll receive feedback after each, and a summary at the end.")

# Current question
idx = st.session_state.index

if idx < len(qa_list):
    question = qa_list[idx]["question"]
    example = qa_list[idx]["example"]

    st.subheader(f"Question {idx+1}")
    st.write(question)

    with st.expander("See an example answer"):
        st.write(example)

    user_answer = st.text_area("Your Answer:", key=f"answer_{idx}", height=150)

    if st.button("Submit Answer"):
        if user_answer.strip() == "":
            st.warning("Please enter an answer before submitting.")
        else:
            with st.spinner("Grading..."):
                res = requests.post("http://127.0.0.1:5000/grade_answer", json={
                    "question": question,
                    "answer": user_answer,
                    "example": example
                })

                if res.status_code == 200:
                    feedback = res.json().get("feedback", "")
                    st.success("Feedback:")
                    st.markdown(feedback)

                    # Save progress
                    st.session_state.answers.append(user_answer)
                    st.session_state.feedback.append(feedback)
                    # st.session_state.answers.append(user_answer)
                    # st.session_state.feedback.append(feedback)

                    # Advance to next question before rerunning
                    st.session_state.index += 1

                    # Avoid rerunning immediately; just let Streamlit naturally refresh
                    st.success("Answer submitted. Scroll down or click 'Submit Answer' again to continue.")
                else:
                    st.error("Error from backend")
                    st.text(res.text)
else:
    # Interview complete — show summary
    st.header("Interview Summary")

    for i in range(len(qa_list)):
        st.subheader(f"Q{i+1}: {qa_list[i]['question']}")
        st.write(f"**Your answer:** {st.session_state.answers[i]}")
        st.write(f"**Feedback:** {st.session_state.feedback[i]}")

    # Call overall grader
    if st.button("Get Overall Evaluation"):
        with st.spinner("Generating overall feedback..."):
            qa_feedback = [
                    {
                        "question": qa_list[i]["question"],
                        "answer": st.session_state.answers[i],
                        "feedback": st.session_state.feedback[i]
                    }
                    for i in range(3)
            ]

        res = requests.post("http://127.0.0.1:5000/grade_overall", json={"qa_feedback": qa_feedback})

        if res.status_code == 200:
                overall = res.json().get("overall_feedback", "")
                st.success("Overall Evaluation")
                st.markdown(overall)
        else:
                st.error("❌ Failed to generate overall evaluation.")
                st.text(f"Status: {res.status_code}")
                st.text(res.text)