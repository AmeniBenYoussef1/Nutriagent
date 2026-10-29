import argparse
import csv

import chromadb

import config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to the recipes CSV")
    parser.add_argument("--persist-dir", default=config.VECTORSTORE_DIR)
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=args.persist_dir)
    collection = client.get_or_create_collection("recipes")

    with open(args.input, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ids, documents, metadatas = [], [], []
    for i, row in enumerate(rows):
        try:
            ids.append(str(i))
            documents.append(f"{row['name']}: {row.get('description', '')}")
            metadatas.append(
                {
                    "calories": float(row["calories"]),
                    "protein_g": float(row["protein_g"]),
                    "carbs_g": float(row["carbs_g"]),
                    "fat_g": float(row["fat_g"]),
                }
            )
        except (KeyError, ValueError):
            continue


    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Indexed {len(ids)} recipes into '{args.persist_dir}'")


if __name__ == "__main__":
    main()
