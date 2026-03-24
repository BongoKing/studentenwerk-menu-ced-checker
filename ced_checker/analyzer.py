from ced_checker.models import Meal, MealRating


def analyze_meal(meal: Meal, allergen_config: dict, food_config: dict) -> MealRating:
    """Analyze a single meal for CED compatibility.

    allergen_config: code -> {"beschreibung": str, "bewertung": str}
    food_config: name_lower -> {"name": str, "bewertung": str}
    """
    score = 10.0
    warnings = []
    positives = []
    excluded = False

    # 1) Check allergen codes
    for code in meal.allergen_codes:
        if code not in allergen_config:
            continue
        entry = allergen_config[code]
        bewertung = entry["bewertung"]
        desc = entry["beschreibung"]

        if bewertung == "ausgeschlossen":
            excluded = True
            warnings.append(f"AUSGESCHLOSSEN: {desc} [{code}]")
        elif bewertung == "vermeiden":
            score -= 2
            warnings.append(f"Vermeiden: {desc} [{code}]")

    # 2) Check legend tags (Schwein, Vegan, etc.)
    for tag in meal.legend_tags:
        tag_lower = tag.lower()
        if tag_lower not in food_config:
            continue
        entry = food_config[tag_lower]
        bewertung = entry["bewertung"]

        if bewertung == "ausgeschlossen":
            excluded = True
            warnings.append(f"AUSGESCHLOSSEN: {entry['name']}")
        elif bewertung == "vermeiden":
            score -= 2
            warnings.append(f"Vermeiden: {entry['name']}")
        elif bewertung == "empfohlen":
            score += 1
            positives.append(entry["name"])

    # 3) Keyword matching in title
    title_lower = meal.title.lower()
    for key, entry in food_config.items():
        # Skip legend tags already checked above
        if any(key == tag.lower() for tag in meal.legend_tags):
            continue
        if key in title_lower:
            bewertung = entry["bewertung"]
            if bewertung == "ausgeschlossen":
                excluded = True
                warnings.append(f"AUSGESCHLOSSEN im Titel: {entry['name']}")
            elif bewertung == "vermeiden":
                score -= 2
                warnings.append(f"Vermeiden (Titel): {entry['name']}")
            elif bewertung == "empfohlen":
                score += 1
                positives.append(f"{entry['name']} (Titel)")

    # Clamp score
    score = max(0.0, min(10.0, score))

    grade = MealRating.score_to_grade(score, excluded)

    return MealRating(
        meal=meal,
        score=score if not excluded else 0,
        grade=grade,
        warnings=warnings,
        positives=positives,
        excluded=excluded,
    )


def analyze_and_rank(meals: list[Meal], allergen_config: dict,
                     food_config: dict) -> list[MealRating]:
    """Analyze all meals and return sorted by score (best first)."""
    ratings = [analyze_meal(m, allergen_config, food_config) for m in meals]
    ratings.sort(key=lambda r: (-r.score, r.meal.title))
    return ratings
