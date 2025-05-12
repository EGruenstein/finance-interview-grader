import streamlit as st
from openai import OpenAI
import os
import json

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("examples.json") as f:
    examples = json.load(f)

qa_list = examples[:3]

if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.answers = []
    st.session_state.feedback = []
    st.session_state.completed = False

st.title("Finance Interview Grader")
st.write("Answer 3 finance interview questions and receive feedback and an overall evaluation.")

# current question
idx = st.session_state.index

if idx < len(qa_list):
    q = qa_list[idx]
    question = q["question"]
    example = q["example"]

    st.subheader(f"Question {idx + 1}")
    st.write(question)

    with st.expander("Example Answer"):
        st.write(example)

    answer = st.text_area("Your Answer", key=f"answer_{idx}", height=150)

    if st.button("Submit Answer"):
        if not answer.strip():
            st.warning("Please enter an answer before submitting.")
        else:
            with st.spinner("Grading your answer..."):

                # Generate grading prompt
                grading_prompt = f"""
                Question: {question}
                Example Answer: {example}
                Candidate Answer: {answer}

                You are a senior finance interviewer. Compare the candidate’s answer to the example and assign a score from 1 to 10 based on accuracy, clarity, and completeness.

                Respond using the following format:
                Score: X/10  
                Justification: <your explanation here>

                If the answer is vague, incorrect, or incomplete (e.g., "I don't know"), explain what is missing and assign a low score.
                                """

                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are an expert investment banking interviewer. Grade answers strictly based on accuracy and completeness."},
                            {"role": "user", "content": grading_prompt}
                        ]
                    )
                    feedback = response.choices[0].message.content.strip()
                    st.session_state.answers.append(answer)
                    st.session_state.feedback.append(feedback)
                    st.session_state.index += 1
                    st.experimental_rerun()
                except Exception as e:
                    st.error("Failed to get feedback from OpenAI.")
                    st.text(str(e))

else:
    st.session_state.completed = True
    st.header("Interview Summary")

    for i in range(3):
        st.subheader(f"Q{i+1}: {qa_list[i]['question']}")
        st.markdown(f"**Your answer:** {st.session_state.answers[i]}")
        st.markdown(f"**Feedback:** {st.session_state.feedback[i]}")

    if st.button("Get Overall Evaluation", key="overall_button"):
        with st.spinner("Generating overall evaluation..."):

            summary_prompt = "You are a senior finance interviewer. Below is a summary of the candidate’s responses and the feedback they received:\n\n"
            for i in range(3):
                summary_prompt += f"Q{i+1}: {qa_list[i]['question']}\n"
                summary_prompt += f"A: {st.session_state.answers[i]}\n"
                summary_prompt += f"Feedback: {st.session_state.feedback[i]}\n\n"
            summary_prompt += "Provide an overall score (out of 10) and a short summary. Start with 'Overall Score: X/10'."

            try:
                overall_res = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a senior finance interviewer. Evaluate candidate performance holistically."},
                        {"role": "user", "content": summary_prompt}
                    ]
                )
                overall_feedback = overall_res.choices[0].message.content.strip()
                st.success("Overall Evaluation")
                st.markdown(overall_feedback)
            except Exception as e:
                st.error("Failed to generate overall evaluation.")
                st.text(str(e))
