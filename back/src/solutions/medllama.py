import datetime
import json
import os
import ollama

def generate_skin_plan(
    disease: str,
    severity_score: int,
    sex: str,
    age: int,
    weight: float,
    previous_treatment: str,
    diet: str,
    actual_date: str,
    model_name: str = 'medllama2'
) -> str:
    """
    Generates a treatment plan and lifestyle advice using Ollama's model.

    Returns a JSON-formatted string with keys:
    - treatment_plan: list of {date: str, treatment: str}
    - lifestyle_advice: list of advice strings
    """
    prompt = (
        f"You are a knowledgeable medical assistant specializing in dermatology. Given the patient data below, provide:\n"
        f"1. A detailed day-by-day medical treatment schedule (dates and treatments) to improve skin health.\n"
        f"2. Targeted lifestyle improvement advice to support skin recovery.\n\n"
        f"Patient Data:\n"
        f"- Skin disease: {disease}\n"
        f"- Severity score (1-100): {severity_score}\n"
        f"- Sex: {sex}\n"
        f"- Age: {age}\n"
        f"- Weight (kg): {weight}\n"
        f"- Previous treatment: {previous_treatment or 'None'}\n"
        f"- Diet: {diet or 'Not specified'}\n"
        f"- Current date: {actual_date}\n\n"
        f"Respond in JSON format with keys 'treatment_plan' and 'lifestyle_advice'."
    )

    response = ollama.chat(
        model=model_name,
        messages=[
            {'role': 'user', 'content': prompt}
        ],
        options={
            'temperature': 0.7,
            'top_p': 0.9,
            'max_tokens': 512
        }
    )
    
    return response['message']['content']


def generate_skin_plan_from_json(input_json: dict) -> str:
    """
    Wrapper: Parses a JSON dict and generates the skin plan using Ollama.
    """
    required_keys = [
        "disease", "severity_score", "sex", "age",
        "weight", "previous_treatment", "diet", "actual_date"
    ]
    missing = [k for k in required_keys if k not in input_json]
    if missing:
        raise ValueError(f"Missing keys in input JSON: {missing}")

    model_name = input_json.get("model_name", 'medllama2')

    return generate_skin_plan(
        disease=input_json["disease"],
        severity_score=int(input_json["severity_score"]),
        sex=input_json["sex"],
        age=int(input_json["age"]),
        weight=float(input_json["weight"]),
        previous_treatment=input_json.get("previous_treatment", ""),
        diet=input_json.get("diet", ""),
        actual_date=input_json["actual_date"],
        model_name=model_name
    )


def test_generate_skin_plan():
    """
    Test using sample JSON, prints input and generated output.
    """
    sample_input = {
        "disease": "acne",
        "severity_score": 75,
        "sex": "female",
        "age": 28,
        "weight": 65.0,
        "previous_treatment": "topical retinoids",
        "diet": "high glycemic load diet",
        "actual_date": datetime.date.today().isoformat(),
        "model_name": "medllama2"
    }

    print("Input JSON:")
    print(json.dumps(sample_input, indent=2))
    print("\nGenerated Plan:")
    plan = generate_skin_plan_from_json(sample_input)
    print(plan)


if __name__ == "__main__":
    test_generate_skin_plan()