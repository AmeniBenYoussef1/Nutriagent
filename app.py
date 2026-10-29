import gradio as gr
import pandas as pd

from items import LoggedMeal, UserGoals
from memory import Memory
from agents import vision_agent, ensemble_agent, planning_agent, messaging_agent

memory = Memory()


def log_meal(image, text_description, label):
    if image is not None:
        items = vision_agent.identify_from_image(image)
    elif text_description and text_description.strip():
        items = vision_agent.identify_from_text(text_description)
    else:
        return "Please provide a photo or a text description.", None, None

    if not items:
        return "Couldn't identify any food items — try a clearer photo or description.", None, None

    estimate = ensemble_agent.estimate_meal(items)
    meal = LoggedMeal(items=items, estimate=estimate, label=label or "Meal")
    memory.add_meal(meal)

    items_text = "\n".join(f"• {i.name} ({i.estimated_portion})" for i in items)
    summary = (
        f"Identified:\n{items_text}\n\n"
        f"Estimated: {estimate.calories:.0f} kcal | "
        f"{estimate.protein_g:.0f}g protein | "
        f"{estimate.carbs_g:.0f}g carbs | {estimate.fat_g:.0f}g fat"
    )
    return summary, refresh_dashboard(), refresh_history_chart()


def refresh_dashboard():
    totals = memory.todays_totals()
    goals = memory.get_goals()
    return messaging_agent.build_digest_text(totals, goals)


def refresh_history_chart():
    history = memory.history()
    if not history:
        return None
    df = pd.DataFrame(history)
    return df[["date", "calories"]]


def save_goals(calories, protein, carbs, fat, goal_type):
    goals = UserGoals(
        daily_calories=calories,
        protein_g=protein,
        carbs_g=carbs,
        fat_g=fat,
        goal_type=goal_type,
    )
    memory.set_goals(goals)
    return "Goals saved.", refresh_dashboard()


with gr.Blocks(title="NutriAgent") as demo:
    gr.Markdown("# NutriAgent — your multi-agent nutrition coach")

    with gr.Tab("Log a meal"):
        with gr.Row():
            with gr.Column():
                image_input = gr.Image(type="filepath", label="Photo (fridge or plate)")
                text_input = gr.Textbox(
                    label="Or describe it", placeholder="e.g. grilled chicken, rice, broccoli"
                )
                label_input = gr.Textbox(label="Label (optional)", placeholder="Breakfast")
                log_btn = gr.Button("Log meal", variant="primary")
            with gr.Column():
                result_box = gr.Textbox(label="Result", lines=8)

    with gr.Tab("Today"):
        dashboard_box = gr.Textbox(label="Digest", lines=10, value=refresh_dashboard)
        refresh_btn = gr.Button("Refresh")

    with gr.Tab("History"):
        history_chart = gr.LinePlot(
            value=refresh_history_chart(),
            x="date",
            y="calories",
            title="Calories over time",
        )

    with gr.Tab("Goals"):
        goals = memory.get_goals()
        cal_input = gr.Number(label="Daily calories", value=goals.daily_calories)
        protein_input = gr.Number(label="Protein (g)", value=goals.protein_g)
        carbs_input = gr.Number(label="Carbs (g)", value=goals.carbs_g)
        fat_input = gr.Number(label="Fat (g)", value=goals.fat_g)
        goal_type_input = gr.Radio(["cut", "maintain", "bulk"], value=goals.goal_type, label="Goal")
        save_btn = gr.Button("Save goals")
        goals_status = gr.Textbox(label="Status")

    log_btn.click(
        log_meal,
        inputs=[image_input, text_input, label_input],
        outputs=[result_box, dashboard_box, history_chart],
    )
    refresh_btn.click(refresh_dashboard, outputs=dashboard_box)
    save_btn.click(
        save_goals,
        inputs=[cal_input, protein_input, carbs_input, fat_input, goal_type_input],
        outputs=[goals_status, dashboard_box],
    )

if __name__ == "__main__":
    demo.launch()