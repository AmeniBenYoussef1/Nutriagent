import argparse
import csv
import json
import random


def build_examples(rows: list[dict]) -> list[dict]:
    examples = []
    for row in rows:
        try:
            name = row["description"].strip()
            calories = float(row["calories"])
            protein = float(row["protein_g"])
            carbs = float(row["carbs_g"])
            fat = float(row["fat_g"])
        except (KeyError, ValueError):
            continue

        prompt = f"Estimate the nutrition for: {name}, portion: 100g"
        completion = json.dumps(
            {
                "calories": calories,
                "protein_g": protein,
                "carbs_g": carbs,
                "fat_g": fat,
            }
        )
        examples.append({"prompt": prompt, "completion": completion})
    return examples


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the USDA CSV export")
    parser.add_argument("--output", default="train.jsonl")
    parser.add_argument("--val-split", type=float, default=0.1)
    args = parser.parse_args()

    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    examples = build_examples(rows)
    random.shuffle(examples)

    n_val = int(len(examples) * args.val_split)
    val, train = examples[:n_val], examples[n_val:]

    with open(args.output, "w") as f:
        for ex in train:
            f.write(json.dumps(ex) + "\n")

    val_path = args.output.replace(".jsonl", "_val.jsonl")
    with open(val_path, "w") as f:
        for ex in val:
            f.write(json.dumps(ex) + "\n")

    print(f"Wrote {len(train)} training examples to {args.output}")
    print(f"Wrote {len(val)} validation examples to {val_path}")


if __name__ == "__main__":
    main()
