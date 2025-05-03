import os
import datetime
import json

# pip install --upgrade google-genai
from google import genai
from google.genai import types

def configure_gemini(api_key_env: str = "GOOGLE_API_KEY", use_vertex: bool = True) -> genai.Client:
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"Set {api_key_env} to your Google API key.")
    return genai.Client(api_key=api_key, vertexai=use_vertex)

def generate_skin_plan_gemini(
    client: genai.Client,
    disease: str,
    severity_score: int,
    sex: str,
    age: int,
    weight: float,
    previous_treatment: str,
    diet: str,
    actual_date: str,
    model: str = "gemini-1.5-turbo",
) -> dict:
    prompt = (
        "You are a knowledgeable medical assistant specializing in dermatology. "
        "Given the patient data below, provide:\n"
        "1. A detailed day‑by‑day medical treatment schedule (dates and treatments) to improve skin health.\n"
        "2. Targeted lifestyle improvement advice to support skin recovery.\n\n"
        f"Patient Data:\n"
        f"- Skin disease: {disease}\n"
        f"- Severity score (1‑100): {severity_score}\n"
        f"- Sex: {sex}\n"
        f"- Age: {age}\n"
        f"- Weight (kg): {weight}\n"
        f"- Previous treatment: {previous_treatment or 'None'}\n"
        f"- Diet: {diet or 'Not specified'}\n"
        f"- Current date: {actual_date}\n\n"
        "Please respond strictly in JSON format, with keys 'treatment_plan' and 'lifestyle_advice'."
    )

    # Bundle generation params in a GenerateContentConfig and pass via `config`
    config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.9,
        max_output_tokens=512,
    )

    response = client.models.generate_content(
        model=model,
        contents=prompt,        # str or list/Content both work
        config=config           # <- correct keyword
    )
    return json.loads(response.text)

def generate_skin_plan_from_json(input_json: dict, client: genai.Client) -> dict:
    required = [
        "disease", "severity_score", "sex", "age",
        "weight", "previous_treatment", "diet", "actual_date"
    ]
    missing = [k for k in required if k not in input_json]
    if missing:
        raise ValueError(f"Missing keys in input JSON: {missing}")

    return generate_skin_plan_gemini(
        client=client,
        disease=input_json["disease"],
        severity_score=int(input_json["severity_score"]),
        sex=input_json["sex"],
        age=int(input_json["age"]),
        weight=float(input_json["weight"]),
        previous_treatment=input_json.get("previous_treatment", ""),
        diet=input_json.get("diet", ""),
        actual_date=input_json["actual_date"],
    )

def test_generate_skin_plan():
    client = configure_gemini()  # reads GOOGLE_API_KEY
    sample = {
        "disease": "acne",
        "severity_score": 75,
        "sex": "female",
        "age": 28,
        "weight": 65.0,
        "previous_treatment": "topical retinoids",
        "diet": "high glycemic load diet",
        "actual_date": datetime.date.today().isoformat(),
    }
    plan = generate_skin_plan_from_json(sample, client)
    print(json.dumps(plan, indent=2))

if __name__ == "__main__":
    test_generate_skin_plan()
