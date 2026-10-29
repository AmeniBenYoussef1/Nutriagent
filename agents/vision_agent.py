import base64
import json
import re

from items import FoodItem
import config

SYSTEM_PROMPT = """You are a food identification assistant. Given an image of \
food (a fridge, a plate, or a receipt) or a text description of a meal, \
identify each distinct food item and estimate its portion size.

Respond with ONLY a JSON array, no other text, no markdown fences. Each \
element must have exactly these keys: "name" (string), "estimated_portion" \
(string, e.g. "1 cup", "150g", "2 slices"), "confidence" (float 0-1).

Example response:
[{"name": "grilled chicken breast", "estimated_portion": "150g", "confidence": 0.8}, \
{"name": "steamed broccoli", "estimated_portion": "1 cup", "confidence": 0.7}]
"""


def _parse_response(text: str) -> list[FoodItem]:
    # Strip markdown fences if the model added them despite instructions
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        raw_items = json.loads(cleaned)
    except json.JSONDecodeError:
        return []
    items = []
    for r in raw_items:
        try:
            items.append(
                FoodItem(
                    name=r["name"],
                    estimated_portion=r["estimated_portion"],
                    confidence=float(r.get("confidence", 0.6)),
                )
            )
        except (KeyError, ValueError, TypeError):
            continue
    return items


def _identify_from_image_anthropic(client, image_path: str) -> list[FoodItem]:
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    media_type = "image/jpeg"
    if image_path.lower().endswith(".png"):
        media_type = "image/png"

    response = client.messages.create(
        model=config.VISION_MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {"type": "text", "text": "Identify the food items in this image."},
                ],
            }
        ],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_response(text)


def _identify_from_image_gemini(model, image_path: str) -> list[FoodItem]:
    from PIL import Image

    image = Image.open(image_path)
    response = model.generate_content(
        [SYSTEM_PROMPT, "Identify the food items in this image.", image]
    )
    return _parse_response(response.text)


def identify_from_image(image_path: str) -> list[FoodItem]:
    client = config.get_anthropic_client()
    if client is not None:
        return _identify_from_image_anthropic(client, image_path)

    gemini_model = config.get_gemini_model()
    if gemini_model is not None:
        return _identify_from_image_gemini(gemini_model, image_path)

    return []


def _identify_from_text_anthropic(client, description: str) -> list[FoodItem]:
    response = client.messages.create(
        model=config.VISION_MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": description}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_response(text)


def _identify_from_text_gemini(model, description: str) -> list[FoodItem]:
    response = model.generate_content([SYSTEM_PROMPT, description])
    return _parse_response(response.text)


def identify_from_text(description: str) -> list[FoodItem]:
    client = config.get_anthropic_client()
    if client is not None:
        items = _identify_from_text_anthropic(client, description)
        return items or _naive_text_split(description)

    gemini_model = config.get_gemini_model()
    if gemini_model is not None:
        items = _identify_from_text_gemini(gemini_model, description)
        return items or _naive_text_split(description)

    return _naive_text_split(description)


def _naive_text_split(description: str) -> list[FoodItem]:
    parts = [p.strip() for p in re.split(r",| and ", description) if p.strip()]
    return [FoodItem(name=p, estimated_portion="1 serving", confidence=0.3) for p in parts]