import json
import base64
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def analyze_medical_report_image(base64_image_data: str):
    """
    Sends an image as base64 to OpenAI's gpt-4o model to extract medical report details.
    Returns a dictionary containing disease_prediction, summary, and a list of abnormal_metrics.
    """
    prompt = """
    You are an expert medical AI assistant.
    The user has uploaded an image of a medical report (e.g., blood test).
    Please analyze it and extract the following information in strict JSON format:
    {
      "disease_prediction": "Name of the likely condition or disease based on abnormal values (e.g., Dengue, Anemia, Normal). If normal, say 'No specific disease detected'.",
      "summary": "A 2-3 sentence simple explanation for a layman.",
      "abnormal_metrics": [
        {
          "test_name": "e.g., Platelet Count",
          "value": "e.g., 90,000",
          "unit": "e.g., cells/mcL",
          "reference_range": "e.g., 150,000 - 450,000",
          "status": "Low or High"
        }
      ]
    }
    Only return the JSON. Do not return markdown tags or any other text.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image_data,
                            "detail": "high"
                        },
                    },
                ],
            }
        ],
        max_tokens=1000,
    )
    
    content = response.choices[0].message.content.strip()
    # Strip markdown if model returned it despite instructions
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
        
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        return {
            "disease_prediction": "Unable to parse report",
            "summary": "The AI could not read the report clearly.",
            "abnormal_metrics": []
        }

def analyze_medicine_image(base64_image_data: str):
    """
    Sends an image as base64 to OpenAI's gpt-4o model to extract medicine details.
    """
    prompt = """
    You are an expert medical AI assistant.
    The user has uploaded an image of a medicine (e.g., pill strip, bottle).
    Please analyze it and extract the following information in strict JSON format:
    {
      "name": "Name of the medicine",
      "primary_use": "What it is primarily used for (simple language)",
      "active_ingredients": ["Ingredient 1", "Ingredient 2"],
      "side_effects": ["Side effect 1", "Side effect 2"]
    }
    Only return the JSON. Do not return markdown tags or any other text.
    If you cannot identify the medicine, return placeholder text for the name and leave other fields empty.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": base64_image_data,
                            "detail": "high"
                        },
                    },
                ],
            }
        ],
        max_tokens=1000,
    )
    
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:-3]
    elif content.startswith("```"):
        content = content[3:-3]
        
    try:
        data = json.loads(content)
        return data
    except json.JSONDecodeError:
        return {
            "name": "Unable to identify",
            "primary_use": "The AI could not read the medicine label clearly.",
            "active_ingredients": [],
            "side_effects": []
        }

