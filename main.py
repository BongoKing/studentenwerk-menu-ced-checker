import argparse
from datetime import date, timedelta
from pathlib import Path

from ced_checker.api import fetch_meals
from ced_checker.config_loader import load_settings, load_allergen_config, load_food_config
from ced_checker.analyzer import analyze_and_rank
from ced_checker.output import print_header, print_location, print_ratings, print_summary


def main():
    config_dir = Path(__file__).parent / "config"

    # Load settings for default mode
    settings = load_settings(config_dir / "settings.json")
    default_mode = settings.get("disease_mode", "crohn")

    parser = argparse.ArgumentParser(
        description="CED Mensa-Checker: Verträglichkeitsprüfung für den Speiseplan"
    )
    parser.add_argument(
        "--date", "-d",
        default=None,
        help="Datum im Format YYYY-MM-DD (Standard: heute). "
             "Wird ignoriert wenn --from/--to gesetzt sind.",
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["crohn", "colitis"],
        default=default_mode,
        help=f"Krankheitsmodus (Standard: {default_mode})",
    )
    parser.add_argument(
        "--from", dest="date_from",
        default=None,
        help="Startdatum für Zeitraum-Report (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--to", dest="date_to",
        default=None,
        help="Enddatum für Zeitraum-Report (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Ausgabedatei für xlsx-Report (Standard: report_<von>_<bis>.xlsx)",
    )
    args = parser.parse_args()

    # Load configs
    allergen_config = load_allergen_config(config_dir / "allergene_zusatzstoffe.xlsx", args.mode)
    food_config = load_food_config(config_dir / "nahrungsmittel.xlsx", args.mode)

    # --- Period report mode ---
    if args.date_from or args.date_to:
        _run_report(args, settings, allergen_config, food_config)
        return

    # --- Single day mode (original behavior) ---
    target_date = args.date or date.today().isoformat()

    base_url = settings["base_url"]
    api_path = settings["api_path"]
    locations = settings["locations"]

    print_header(target_date, args.mode)

    all_ratings = []

    for loc in locations:
        print_location(loc["label"], loc["web_url"], target_date)

        meals = fetch_meals(base_url, api_path, loc["name"], target_date, loc["categories"])

        if not meals:
            print("  Keine Gerichte gefunden.")
            all_ratings.append((loc["label"], []))
            continue

        ratings = analyze_and_rank(meals, allergen_config, food_config)
        print_ratings(ratings)
        all_ratings.append((loc["label"], ratings))

    print_summary(all_ratings)


def _run_report(args, settings, allergen_config, food_config):
    """Run the period report and generate an xlsx file."""
    from ced_checker.report import generate_report

    today = date.today()

    # Parse dates, default --from to today, default --to to today+6
    if args.date_from:
        d_from = date.fromisoformat(args.date_from)
    else:
        d_from = today

    if args.date_to:
        d_to = date.fromisoformat(args.date_to)
    else:
        d_to = d_from + timedelta(days=6)

    if d_from > d_to:
        print(f"[!] Startdatum ({d_from}) liegt nach Enddatum ({d_to}). Tausche Daten.")
        d_from, d_to = d_to, d_from

    day_count = (d_to - d_from).days + 1
    mode_label = "Morbus Crohn" if args.mode == "crohn" else "Colitis ulcerosa"

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path(f"report_{d_from.isoformat()}_{d_to.isoformat()}_{args.mode}.xlsx")

    print(f"\n{'=' * 70}")
    print(f"  CED Mensa-Checker — Zeitraum-Report")
    print(f"  Modus: {mode_label}")
    print(f"  Zeitraum: {d_from.isoformat()} bis {d_to.isoformat()} ({day_count} Tage)")
    print(f"  Ausgabe: {output_path}")
    print(f"{'=' * 70}\n")

    print(f"  Lade Speisepläne für {day_count} Tage ...")

    result_path = generate_report(
        date_from=d_from,
        date_to=d_to,
        mode=args.mode,
        settings=settings,
        allergen_config=allergen_config,
        food_config=food_config,
        output_path=output_path,
    )

    print(f"\n  Report gespeichert: {result_path.resolve()}")
    print(f"  Blätter: Detailübersicht | Tagesübersicht | Statistik\n")


if __name__ == "__main__":
    main()
