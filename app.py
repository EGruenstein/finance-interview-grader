from flask import Flask, request, jsonify
from openai import OpenAI
import json
import pprint

app = Flask(__name__)
client = OpenAI(api_key="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") 

with open("examples.json", "r") as f:
    qa_data = json.load(f)

qa_lookup = {entry["question"]: entry["example"] for entry in qa_data}


@app.route('/grade_answer', methods=['POST'])
def grade_answer():
    print("🔔 /grade_answer endpoint hit")
    try:
        question = request.json['question']
        answer = request.json['answer']
        example = qa_lookup.get(question)
        grading_prompt = f"""
        Question: {question}
        Example Answer: {example}
        Candidate Answer: {answer}

        You are a senior finance interviewer. Compare the candidate’s answer to the example and assign a score from 1 to 10 based on accuracy, clarity, and completeness. If the answer is blank, give it a score of 0. If the answer is fewer than five words long, give it a score of 1.

        Respond using the following format exactly:
        Score: X/10  
        Justification: <your explanation here>
        """

        print("Grading prompt:", grading_prompt)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages = [
            {"role": "system", "content": "You are an expert investment banking interviewer. Grade answers strictly based on accuracy and completeness."},
            {"role": "user", "content": grading_prompt}
        ]
        )

        print("Grading response:", response)
        return jsonify({'feedback': response.choices[0].message.content})
    
    except Exception as e:
        print("Error occurred:", repr(e))
        return jsonify({"error": str(e)}), 500
    
@app.route('/grade_overall', methods=['POST'])
def grade_overall():
    print("🔔 /grade_overall endpoint hit")
    try:
        qa_pairs = request.json.get('qa_feedback', [])
        if not qa_pairs or not isinstance(qa_pairs, list):
            print("❌ Invalid or missing qa_feedback.")
            return jsonify({"error": "Missing or malformed qa_feedback payload."}), 400

        print("📦 Received QA feedback:")
        for i, qa in enumerate(qa_pairs):
            print(f"Q{i+1}: {qa.get('question')}")
            print(f"A: {qa.get('answer')}")
            print(f"Feedback: {qa.get('feedback')}\n")

        summary_prompt = "You are a senior finance interviewer. Below is a summary of the candidate’s responses and the feedback they received:\n\n"
        for i, qa in enumerate(qa_pairs):
            summary_prompt += f"Q{i+1}: {qa['question']}\n"
            summary_prompt += f"A: {qa['answer']}\n"
            summary_prompt += f"Feedback: {qa['feedback']}\n\n"

        summary_prompt += (
            "Based on the above responses and feedback, provide an overall score (out of 10) and a short summary of the candidate’s interview performance. "
            "Start your response with 'Overall Score: X/10'."
        )

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a senior finance interviewer. Evaluate candidate performance holistically."},
                {"role": "user", "content": summary_prompt}
            ]
        )

        overall_feedback = response.choices[0].message.content.strip() if response.choices else "No overall feedback returned."
        print("🧠 Overall Evaluation Generated:\n", overall_feedback)
        return jsonify({'overall_feedback': overall_feedback})

    except Exception as e:
        print("❌ Error occurred in /grade_overall:", repr(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)