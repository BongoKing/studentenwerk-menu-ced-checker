"""Generate a static HTML page for GitHub Pages deployment.

Embeds raw meal data and both config files as JSON. The page uses
client-side JavaScript for analysis, rendering, and user customization.

Usage:
    python generate_page.py [--date YYYY-MM-DD] [--output-dir public]
"""

import argparse
import json
from datetime import date
from pathlib import Path

from ced_checker.api import fetch_meals
from ced_checker.config_loader import (
    load_settings,
    load_allergen_config_both,
    load_food_config_both,
)
from ced_checker.html_generator import generate_html_dual


def main():
    config_dir = Path(__file__).parent / "config"
    settings = load_settings(config_dir / "settings.json")
    default_mode = settings.get("disease_mode", "crohn")

    parser = argparse.ArgumentParser(description="Generate CED Mensa-Checker HTML page")
    parser.add_argument("--date", "-d", default=date.today().isoformat())
    parser.add_argument("--output-dir", "-o", default="public")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date)
    locations = settings["locations"]
    base_url = settings["base_url"]
    api_path = settings["api_path"]

    # Load configs with both modes combined
    allergen_defaults = load_allergen_config_both(config_dir / "allergene_zusatzstoffe.xlsx")
    food_defaults = load_food_config_both(config_dir / "nahrungsmittel.xlsx")

    print(f"  Configs: {len(allergen_defaults)} Allergene, {len(food_defaults)} Nahrungsmittel")

    # Fetch meals once, serialize to JSON-friendly dicts
    meals_data = []
    for loc in locations:
        meals = fetch_meals(base_url, api_path, loc["name"], args.date, loc["categories"])
        print(f"  {loc['label']}: {len(meals)} Gerichte geladen")
        meals_data.append({
            "label": loc["label"],
            "web_url": loc["web_url"],
            "meals": [m.to_dict() for m in meals],
        })

    output_dir = Path(args.output_dir)
    output_path = output_dir / "index.html"

    generate_html_dual(
        target_date=target_date,
        meals_json=json.dumps(meals_data, ensure_ascii=False),
        allergens_json=json.dumps(allergen_defaults, ensure_ascii=False),
        foods_json=json.dumps(food_defaults, ensure_ascii=False),
        default_mode=default_mode,
        output_path=output_path,
    )

    print(f"\n  HTML generiert: {output_path.resolve()}")
    print(f"  Beide Modi + Einstellungs-Panel enthalten.")


if __name__ == "__main__":
    main()
