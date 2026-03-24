from dataclasses import dataclass, field


ESSENSSYMBOLE_MAP = {
    "51": "Hausgemacht",
    "52": "Regional",
    "53": "Vegetarisch",
    "54": "Vegan",
    "55": "Wild",
    "56": "Schwein",
    "57": "Rind",
    "58": "Schaf",
    "59": "Geflügel",
    "60": "Fisch",
    "61": "Nachhaltiger Fang",
    "62": "Meeresfrüchte",
    "63": "Mensa Vital",
    "64": "Kräuterküche",
    "65": "Tier. Lab/Gelatine/Honig",
    "66": "BIO",
    "67": "Länderküche",
}


@dataclass
class Meal:
    title: str
    allergen_codes: list[str]
    legend_tags: list[str]
    price: float
    calories: int = 0
    fat: float = 0.0
    fiber: float = 0.0
    protein: float = 0.0
    salt: float = 0.0
    location: str = ""
    klimateller: bool = False
    kraeuterkueche: bool = False

    @classmethod
    def from_api(cls, data: dict) -> "Meal":
        allergens_raw = data.get("allergens", "")
        allergen_codes = [c.strip() for c in allergens_raw.split(",") if c.strip()]

        symbole_raw = str(data.get("essenssymbole", ""))
        legend_tags = []
        for code in symbole_raw.split(","):
            code = code.strip()
            if code in ESSENSSYMBOLE_MAP:
                legend_tags.append(ESSENSSYMBOLE_MAP[code])

        is_klimateller = bool(data.get("klimateller", 0))
        if is_klimateller:
            legend_tags.append("Klimateller")

        is_kraeuterkueche = bool(data.get("kraeuterkueche", 0))
        if is_kraeuterkueche and "Kräuterküche" not in legend_tags:
            legend_tags.append("Kräuterküche")

        # Check for AOK in title
        title = data.get("title", "")
        if title.upper().startswith("AOK"):
            legend_tags.append("AOK")

        return cls(
            title=title,
            allergen_codes=allergen_codes,
            legend_tags=legend_tags,
            price=float(data.get("student", 0)),
            calories=int(data.get("calorific", 0)),
            fat=float(data.get("fat", 0)),
            fiber=float(data.get("fiber", 0)),
            protein=float(data.get("protein", 0)),
            salt=float(data.get("salt", 0)),
            location=data.get("location_name", ""),
            klimateller=is_klimateller,
            kraeuterkueche=is_kraeuterkueche,
        )

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict for embedding in HTML."""
        return {
            "title": self.title,
            "allergen_codes": self.allergen_codes,
            "legend_tags": self.legend_tags,
            "price": self.price,
            "calories": self.calories,
            "fat": self.fat,
            "fiber": self.fiber,
            "protein": self.protein,
            "salt": self.salt,
        }


@dataclass
class MealRating:
    meal: Meal
    score: float
    grade: str
    warnings: list[str] = field(default_factory=list)
    positives: list[str] = field(default_factory=list)
    excluded: bool = False

    @staticmethod
    def score_to_grade(score: float, excluded: bool) -> str:
        if excluded or score <= 0:
            return "F"
        if score >= 9:
            return "A"
        if score >= 7:
            return "B"
        if score >= 5:
            return "C"
        if score >= 3:
            return "D"
        return "E"

    GRADE_LABELS = {
        "A": "sehr gut verträglich",
        "B": "gut verträglich",
        "C": "bedingt verträglich",
        "D": "schlecht verträglich",
        "E": "sehr schlecht verträglich",
        "F": "ausgeschlossen",
    }
