import modal

app = modal.App("nutriagent-specialist")

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
FINE_TUNED_REPO = "your-hf-username/nutriagent-lora"  

image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch",
        "transformers",
        "peft",
        "accelerate",
        "bitsandbytes",
        "fastapi",
    )
)

GPU_CONFIG = "T4"


@app.cls(image=image, gpu=GPU_CONFIG, secrets=[modal.Secret.from_name("huggingface-secret")])
class NutritionSpecialist:
    @modal.enter()
    def load_model(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel
        import torch

        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
        base = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL, torch_dtype=torch.bfloat16, device_map="auto"
        )
        self.model = PeftModel.from_pretrained(base, FINE_TUNED_REPO)
        self.model.eval()

    @modal.method()
    def predict(self, name: str, portion: str) -> dict:
        import torch
        import json
        import re

        prompt = f"Estimate the nutrition for: {name}, portion: {portion}"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            output = self.model.generate(**inputs, max_new_tokens=100)
        text = self.tokenizer.decode(output[0], skip_special_tokens=True)

        # Expect the model to have learned to output JSON (see
        # data/usda_data_prep.py's completion format); fall back to a
        # zeroed response if parsing fails so the caller can retry/fallback.
        match = re.search(r"\{.*\}", text)
        if not match:
            return {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}


@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def predict_endpoint(item: dict):
    """HTTP entrypoint — POST {"name": ..., "portion": ...} -> macros JSON.
    This is the URL you put in MODAL_SPECIALIST_URL in .env."""
    specialist = NutritionSpecialist()
    return specialist.predict.remote(item["name"], item["portion"])
