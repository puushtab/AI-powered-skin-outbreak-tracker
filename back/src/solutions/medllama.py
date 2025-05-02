import datetime
from transformers import LlamaForCausalLM, LlamaTokenizer
import torch
import json


def load_skin_model(
    model_name: str = 'chaoyi-wu/PMC_LLAMA_7B',
    device: str = None,
):
    """
    Loads and returns the tokenizer, model, and device for the skin treatment planner.
    """
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

    tokenizer = LlamaTokenizer.from_pretrained(model_name)
    model = LlamaForCausalLM.from_pretrained(model_name)
    model.to(device)
    model.eval()

    return tokenizer, model, device


def generate_skin_plan(
    tokenizer,
    model,
    device,
    disease: str,
    severity_score: int,
    sex: str,
    age: int,
    weight: float,
    previous_treatment: str,
    diet: str,
    actual_date: str,
) -> str:
    """
    Generates a treatment plan and lifestyle advice given a pretrained model setup.

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

    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=512,
            temperature=0.7,
            top_p=0.9,
            num_return_sequences=1,
        )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response


def generate_skin_plan_from_json(input_json: dict) -> str:
    """
    Wrapper: Parses a JSON dict, loads model, and generates the skin plan.
    """
    required_keys = [
        "disease", "severity_score", "sex", "age",
        "weight", "previous_treatment", "diet", "actual_date"
    ]
    missing = [k for k in required_keys if k not in input_json]
    if missing:
        raise ValueError(f"Missing keys in input JSON: {missing}")

    model_name = input_json.get("model_name", 'chaoyi-wu/PMC_LLAMA_7B')
    device_opt = input_json.get("device", None)
    tokenizer, model, device = load_skin_model(model_name, device_opt)

    return generate_skin_plan(
        tokenizer,
        model,
        device,
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
        # optional
        "model_name": 'chaoyi-wu/PMC_LLAMA_7B',
        "device": None
    }

    print("Input JSON:")
    print(json.dumps(sample_input, indent=2))
    print("\nGenerated Plan:")
    plan = generate_skin_plan_from_json(sample_input)
    print(plan)


if __name__ == "__main__":
    test_generate_skin_plan()
