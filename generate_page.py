"""Generate a static HTML page for GitHub Pages deployment.

Builds both Crohn and Colitis assessments into a single page with toggle.

Usage:
    python generate_page.py [--date YYYY-MM-DD] [--output-dir public]
"""

import argparse
from datetime import date
from pathlib import Path

from ced_checker.api import fetch_meals
from ced_checker.config_loader import load_settings, load_allergen_config, load_food_config
from ced_checker.analyzer import analyze_and_rank
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

    # Load configs for BOTH modes
    allergen_crohn = load_allergen_config(config_dir / "allergene_zusatzstoffe.xlsx", "crohn")
    food_crohn = load_food_config(config_dir / "nahrungsmittel.xlsx", "crohn")
    allergen_colitis = load_allergen_config(config_dir / "allergene_zusatzstoffe.xlsx", "colitis")
    food_colitis = load_food_config(config_dir / "nahrungsmittel.xlsx", "colitis")

    # Fetch meals once, analyze for both modes
    ratings_crohn = []
    ratings_colitis = []

    for loc in locations:
        meals = fetch_meals(base_url, api_path, loc["name"], args.date, loc["categories"])
        print(f"  {loc['label']}: {len(meals)} Gerichte geladen")

        r_crohn = analyze_and_rank(meals, allergen_crohn, food_crohn) if meals else []
        r_colitis = analyze_and_rank(meals, allergen_colitis, food_colitis) if meals else []

        ratings_crohn.append((loc["label"], loc["web_url"], r_crohn))
        ratings_colitis.append((loc["label"], loc["web_url"], r_colitis))

    output_dir = Path(args.output_dir)
    output_path = output_dir / "index.html"

    generate_html_dual(
        target_date=target_date,
        ratings_crohn=ratings_crohn,
        ratings_colitis=ratings_colitis,
        output_path=output_path,
        default_mode=default_mode,
    )

    print(f"\n  HTML generiert: {output_path.resolve()}")
    print(f"  Beide Modi (Crohn + Colitis) enthalten, umschaltbar per Toggle.")


if __name__ == "__main__":
    main()
