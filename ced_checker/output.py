from colorama import Fore, Style, init as colorama_init
from ced_checker.models import MealRating

colorama_init()

GRADE_COLORS = {
    "A": Fore.GREEN,
    "B": Fore.LIGHTGREEN_EX,
    "C": Fore.YELLOW,
    "D": Fore.LIGHTYELLOW_EX,
    "E": Fore.RED,
    "F": Fore.LIGHTRED_EX,
}


def print_header(date: str, mode: str):
    mode_label = "Morbus Crohn" if mode == "crohn" else "Colitis ulcerosa"
    print()
    print(f"{Style.BRIGHT}{'=' * 70}")
    print(f"  CED Mensa-Checker | {date} | Modus: {mode_label}")
    print(f"{'=' * 70}{Style.RESET_ALL}")


def print_location(label: str, web_url: str, date: str):
    # Build user-facing URL with date and student category
    display_url = f"{web_url}#/{date}/student"
    print()
    print(f"{Style.BRIGHT}{Fore.CYAN}--- {label} ---{Style.RESET_ALL}")
    print(f"    {Fore.BLUE}{display_url}{Style.RESET_ALL}")


def print_ratings(ratings: list[MealRating]):
    if not ratings:
        print(f"  {Fore.YELLOW}Keine Gerichte verfügbar.{Style.RESET_ALL}")
        return

    for rank, r in enumerate(ratings, 1):
        color = GRADE_COLORS.get(r.grade, "")
        grade_label = MealRating.GRADE_LABELS.get(r.grade, "")

        # Grade + rank
        grade_str = f"{color}{Style.BRIGHT}[{r.grade}]{Style.RESET_ALL}"
        score_str = f"{color}{r.score:.0f}/10{Style.RESET_ALL}"

        print()
        print(f"  {rank}. {grade_str} {score_str}  {Style.BRIGHT}{r.meal.title}{Style.RESET_ALL}")
        print(f"     {Fore.WHITE}{grade_label} | {r.meal.price:.2f} EUR | {r.meal.calories} kcal{Style.RESET_ALL}")

        # Legend tags
        if r.meal.legend_tags:
            tags = ", ".join(r.meal.legend_tags)
            print(f"     Tags: {tags}")

        # Positives
        if r.positives:
            pos_str = ", ".join(r.positives)
            print(f"     {Fore.GREEN}+ {pos_str}{Style.RESET_ALL}")

        # Warnings
        for w in r.warnings:
            if w.startswith("AUSGESCHLOSSEN"):
                print(f"     {Fore.RED}{Style.BRIGHT}! {w}{Style.RESET_ALL}")
            else:
                print(f"     {Fore.YELLOW}- {w}{Style.RESET_ALL}")


def print_summary(all_ratings: list[tuple[str, list[MealRating]]]):
    """Print overall best picks across all locations."""
    combined = []
    for loc_label, ratings in all_ratings:
        for r in ratings:
            if not r.excluded:
                combined.append((loc_label, r))

    combined.sort(key=lambda x: -x[1].score)

    print()
    print(f"{Style.BRIGHT}{'=' * 70}")
    print(f"  GESAMTEMPFEHLUNG")
    print(f"{'=' * 70}{Style.RESET_ALL}")

    if not combined:
        print(f"  {Fore.RED}Keine verträglichen Gerichte gefunden.{Style.RESET_ALL}")
        return

    top = combined[:3]
    for i, (loc, r) in enumerate(top, 1):
        color = GRADE_COLORS.get(r.grade, "")
        print(f"  {i}. {color}[{r.grade}] {r.score:.0f}/10{Style.RESET_ALL}"
              f"  {r.meal.title} ({loc}, {r.meal.price:.2f} EUR)")

    print()
