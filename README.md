# NutriAgent — Multi-Agent Nutrition Coach

Most nutrition apps (MyFitnessPal, Cronometer, Noom) still require you to
manually search for and log every single food item — which is exactly why
most people stop using them within a few weeks. NutriAgent removes that
friction: take a photo of your plate or fridge, and a pipeline of
cooperating AI agents identifies what you're eating, estimates the
nutrition, tracks it against your goals, and tells you what to eat next.

## Why a multi-agent design

A single LLM call ("just ask GPT what's in this photo and how many
calories it is") is unreliable and gives you no way to improve accuracy
over time. NutriAgent instead splits the problem into specialized
stages, each independently testable and improvable:

```
                       ┌─────────────────┐
   photo / text  ───▶  │  Vision Agent    │  identifies food items + portions
                       └────────┬─────────┘
                                │ List[FoodItem]
                                ▼
        ┌───────────────────────────────────────┐
        │              Ensemble Agent            │
        │  ┌─────────────────┐ ┌───────────────┐ │
        │  │ Specialist Agent │ │ Frontier Agent│ │
        │  │ (fine-tuned LLM  │ │ (RAG over     │ │
        │  │  or heuristic    │ │  nutrition +  │ │
        │  │  fallback)       │ │  recipe data) │ │
        │  └─────────────────┘ └───────────────┘ │
        └──────────────────┬──────────────────────┘
                            │ NutritionEstimate
                            ▼
                  ┌───────────────────┐
                  │   Memory (log)     │  today's totals, history, goals
                  └─────────┬─────────┘
                            ▼
                  ┌───────────────────┐
                  │  Planning Agent    │  gaps vs. goals, next-meal plan
                  └─────────┬─────────┘
                            ▼
                  ┌───────────────────┐
                  │  Messaging Agent   │  daily digest text
                  └───────────────────┘
```

| Agent | Role |
|---|---|
| `vision_agent.py` | Identifies food items + estimated portions from a photo or typed description. Supports Claude or Gemini vision, with a rule-based fallback so the app runs with zero API keys. |
| `specialist_agent.py` | A fine-tuned macro/calorie estimator, deployable as a Modal endpoint, with a built-in heuristic estimator as a working default before you've trained anything. |
| `frontier_agent.py` | Retrieval-augmented estimator and recipe-suggestion engine, backed by a Chroma vector store of nutrition/recipe data. |
| `ensemble_agent.py` | Blends the specialist and frontier estimates into a single, more robust number. |
| `planning_agent.py` | Compares today's intake to your goals and decides what's missing. |
| `messaging_agent.py` | Builds a daily digest summarizing progress and next steps. |

## Project layout

```
nutriagent/
├── app.py                     # Gradio UI — entry point
├── config.py                  # env vars, client setup, default goals
├── items.py                   # FoodItem, LoggedMeal, UserGoals dataclasses
├── memory.py                  # JSON-backed persistence for logs + goals
├── agents/
│   ├── vision_agent.py
│   ├── specialist_agent.py
│   ├── frontier_agent.py
│   ├── ensemble_agent.py
│   ├── planning_agent.py
│   └── messaging_agent.py
├── data/
│   ├── usda_data_prep.py      # builds a fine-tuning dataset from USDA FoodData Central
│   └── build_vectorstore.py   # builds the recipe/nutrition vector store
├── modal_services/
│   └── nutrition_specialist.py  # Modal deployment of the fine-tuned model
├── tests/
│   └── test_agents.py
├── requirements.txt
└── .env.example
```

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env   # add a Gemini or Anthropic API key
python app.py
```

The app runs out of the box with no fine-tuned model and no vector
store built — `specialist_agent.py` falls back to a heuristic estimate
and `frontier_agent.py` degrades gracefully, so you have a working,
demoable product from the very first run.

## Roadmap

1. **Vision + heuristic estimate** — food identification and a naive
   lookup-table estimate flowing end-to-end through the Gradio UI. ✅
2. **Retrieval-augmented estimation** — build the recipe/nutrition
   vector store and wire up grounded estimates and recipe suggestions.
3. **Fine-tuning** — curate a prompt/completion dataset from USDA
   FoodData Central, fine-tune a small open model (e.g. Llama 3.1 8B via
   LoRA), and deploy it on Modal as the specialist agent's backend.
4. **Smarter ensembling & planning** — learn the blend weight between
   specialist and frontier estimates from real correction data; make
   meal planning genuinely goal-aware.
5. **Polish** — trend charts, per-meal delete/edit, scheduled digests,
   and a short demo video.

## Design notes

- **Provider-agnostic vision**: `vision_agent.py` tries Claude first,
  falls back to Gemini, and finally to a naive text parser — so the app
  degrades gracefully rather than breaking when a key is missing.
- **Staged reliability**: every agent has a safe fallback (heuristic
  table, naive parser, empty-but-valid response) so the pipeline never
  hard-fails, it just gets less accurate.
- **Separation of estimation strategies**: the specialist (learned) and
  frontier (retrieval) agents solve the same sub-problem two different
  ways, which is what makes the ensemble step meaningful rather than
  decorative.