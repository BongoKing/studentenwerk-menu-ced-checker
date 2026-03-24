"""Generate a static HTML page for GitHub Pages deployment.

Usage:
    python generate_page.py [--mode crohn|colitis] [--date YYYY-MM-DD] [--output-dir docs]
"""

import argparse
from datetime import date
from pathlib import Path

from ced_checker.api import fetch_meals
from ced_checker.config_loader import load_settings, load_allergen_config, load_food_config
from ced_checker.analyzer import analyze_and_rank
from ced_checker.html_generator import generate_html


def main():
    config_dir = Path(__file__).parent / "config"
    settings = load_settings(config_dir / "settings.json")
    default_mode = settings.get("disease_mode", "crohn")

    parser = argparse.ArgumentParser(description="Generate CED Mensa-Checker HTML page")
    parser.add_argument("--mode", "-m", choices=["crohn", "colitis"], default=default_mode)
    parser.add_argument("--date", "-d", default=date.today().isoformat())
    parser.add_argument("--output-dir", "-o", default="public")
    args = parser.parse_args()

    allergen_config = load_allergen_config(config_dir / "allergene_zusatzstoffe.xlsx", args.mode)
    food_config = load_food_config(config_dir / "nahrungsmittel.xlsx", args.mode)

    target_date = date.fromisoformat(args.date)
    locations = settings["locations"]
    base_url = settings["base_url"]
    api_path = settings["api_path"]

    all_ratings = []
    for loc in locations:
        meals = fetch_meals(base_url, api_path, loc["name"], args.date, loc["categories"])
        ratings = analyze_and_rank(meals, allergen_config, food_config) if meals else []
        all_ratings.append((loc["label"], loc["web_url"], ratings))
        print(f"  {loc['label']}: {len(meals)} Gerichte, {len(ratings)} bewertet")

    output_dir = Path(args.output_dir)
    output_path = output_dir / "index.html"

    generate_html(
        target_date=target_date,
        mode=args.mode,
        all_ratings=all_ratings,
        output_path=output_path,
    )

    print(f"\n  HTML generiert: {output_path.resolve()}")


if __name__ == "__main__":
    main()
