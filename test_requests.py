import requests
import re

# Predefined finance interview questions
questions = [
    "Why do companies exist?",
    "What does the income statement represent?",
    "What is GAAP accounting and why is it used?"
]

answers = []
feedback = []
scores = []

# Loop through the questions
for i, question in enumerate(questions):
    print(f"\nQuestion {i+1}: {question}")
    answer = input("Your Answer:\n")
    answers.append(answer)

    # Grade answer
    grade_response = requests.post("http://127.0.0.1:5000/grade_answer", json={
        "question": question,
        "answer": answer
    })

    feedback_text = grade_response.json().get("feedback", "No feedback.")
    feedback.append(feedback_text)


# Summary Output
print("\nInterview Summary:")

for i in range(len(questions)):
    print(f"\nQ{i+1}: {questions[i]}")
    print(f"\nA{i+1}: {answers[i]}")
    print(f"Feedback: {feedback[i]}")

#Grade the overall interview
print("\nGenerating overall interview evaluation...")

overall_prompt = "You are an expert finance interviewer. Below are a candidate’s answers and the individual feedback they received:\n\n"

for i in range(3):
    overall_prompt += f"Q{i+1}: {questions[i]}\n"
    overall_prompt += f"A: {answers[i]}\n"
    overall_prompt += f"Feedback: {feedback[i]}\n\n"

overall_prompt += "Based on these responses and feedback, provide an overall score (out of 10) and a concise summary of the candidate’s performance."

overall_response = requests.post("http://127.0.0.1:5000/grade_answer", json={
    "question": "Overall Interview Evaluation",
    "answer": overall_prompt
})

overall_feedback = overall_response.json().get("feedback", "No summary available.")
print("\nOverall Evaluation:\n", overall_feedback)