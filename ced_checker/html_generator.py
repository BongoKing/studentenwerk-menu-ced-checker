"""Generate a static HTML page with the daily CED meal assessment."""

from datetime import date
from pathlib import Path

from ced_checker.models import MealRating


GRADE_COLORS = {
    "A": "#22c55e",  # green
    "B": "#86efac",  # light green
    "C": "#eab308",  # yellow
    "D": "#f97316",  # orange
    "E": "#ef4444",  # red
    "F": "#dc2626",  # dark red
}

GRADE_BG = {
    "A": "#f0fdf4",
    "B": "#f0fdf4",
    "C": "#fefce8",
    "D": "#fff7ed",
    "E": "#fef2f2",
    "F": "#fef2f2",
}

WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
               "Freitag", "Samstag", "Sonntag"]


def generate_html(
    target_date: date,
    mode: str,
    all_ratings: list[tuple[str, str, list[MealRating]]],
    output_path: Path,
) -> Path:
    """Generate a self-contained HTML page.

    all_ratings: list of (location_label, web_url, [MealRating, ...])
    """
    mode_label = "Morbus Crohn" if mode == "crohn" else "Colitis ulcerosa"
    weekday = WEEKDAYS_DE[target_date.weekday()]
    date_str = target_date.strftime("%d.%m.%Y")
    date_iso = target_date.isoformat()

    # Collect best overall picks
    combined = []
    for loc_label, _, ratings in all_ratings:
        for r in ratings:
            if not r.excluded:
                combined.append((loc_label, r))
    combined.sort(key=lambda x: -x[1].score)
    top3 = combined[:3]

    # Build location sections
    location_sections = ""
    for loc_label, web_url, ratings in all_ratings:
        display_url = f"{web_url}#/{date_iso}/student"
        cards = ""
        if not ratings:
            cards = '<p class="no-meals">Keine Gerichte verfügbar.</p>'
        else:
            for rank, r in enumerate(ratings, 1):
                color = GRADE_COLORS.get(r.grade, "#888")
                bg = GRADE_BG.get(r.grade, "#fff")
                grade_label = MealRating.GRADE_LABELS.get(r.grade, "")

                warnings_html = ""
                for w in r.warnings:
                    css_class = "warning-excluded" if w.startswith("AUSGESCHLOSSEN") else "warning"
                    warnings_html += f'<span class="{css_class}">{_esc(w)}</span>'

                positives_html = ""
                if r.positives:
                    pos_str = ", ".join(r.positives)
                    positives_html = f'<span class="positive">+ {_esc(pos_str)}</span>'

                tags_html = ""
                if r.meal.legend_tags:
                    for tag in r.meal.legend_tags:
                        tags_html += f'<span class="tag">{_esc(tag)}</span>'

                cards += f'''
                <div class="card" style="border-left: 4px solid {color}; background: {bg};">
                  <div class="card-header">
                    <div class="rank">#{rank}</div>
                    <div class="grade" style="background: {color};">{r.grade}</div>
                    <div class="score">{r.score:.0f}/10</div>
                    <div class="grade-label">{grade_label}</div>
                  </div>
                  <div class="card-body">
                    <h3>{_esc(r.meal.title)}</h3>
                    <div class="meta">
                      <span>{r.meal.price:.2f} &euro;</span>
                      <span>{r.meal.calories} kcal</span>
                      <span>Protein: {r.meal.protein}g</span>
                      <span>Fett: {r.meal.fat}g</span>
                      <span>Ballaststoffe: {r.meal.fiber}g</span>
                    </div>
                    <div class="tags">{tags_html}</div>
                    <div class="feedback">
                      {positives_html}
                      {warnings_html}
                    </div>
                  </div>
                </div>'''

        location_sections += f'''
        <section class="location">
          <h2>{_esc(loc_label)}</h2>
          <a href="{display_url}" target="_blank" class="location-link">{display_url}</a>
          <div class="cards">{cards}</div>
        </section>'''

    # Top picks
    top_html = ""
    if top3:
        for i, (loc, r) in enumerate(top3, 1):
            color = GRADE_COLORS.get(r.grade, "#888")
            top_html += f'''
            <div class="top-pick" style="border-left: 4px solid {color};">
              <span class="top-rank">#{i}</span>
              <span class="grade" style="background: {color};">{r.grade}</span>
              <span class="top-score">{r.score:.0f}/10</span>
              <span class="top-title">{_esc(r.meal.title)}</span>
              <span class="top-loc">{_esc(loc)} &middot; {r.meal.price:.2f} &euro;</span>
            </div>'''
    else:
        top_html = '<p class="no-meals">Keine verträglichen Gerichte gefunden.</p>'

    html = f'''<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CED Mensa-Checker | {date_str}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f8fafc; color: #1e293b; line-height: 1.5;
      max-width: 900px; margin: 0 auto; padding: 16px;
    }}
    header {{
      background: linear-gradient(135deg, #1e40af, #3b82f6);
      color: white; padding: 24px; border-radius: 12px; margin-bottom: 24px;
      text-align: center;
    }}
    header h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
    header .subtitle {{ opacity: 0.9; font-size: 0.95rem; }}
    header .date {{ font-size: 1.1rem; font-weight: 600; margin-top: 8px; }}

    .summary {{
      background: white; border-radius: 12px; padding: 20px;
      margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .summary h2 {{ font-size: 1.1rem; margin-bottom: 12px; color: #1e40af; }}
    .top-pick {{
      display: flex; align-items: center; gap: 10px; padding: 10px 12px;
      background: #f8fafc; border-radius: 8px; margin-bottom: 8px;
      flex-wrap: wrap;
    }}
    .top-rank {{ font-weight: 700; font-size: 1rem; color: #64748b; min-width: 28px; }}
    .top-score {{ font-weight: 600; min-width: 45px; }}
    .top-title {{ font-weight: 600; flex: 1; min-width: 200px; }}
    .top-loc {{ color: #64748b; font-size: 0.85rem; }}

    .location {{ margin-bottom: 28px; }}
    .location h2 {{
      font-size: 1.2rem; color: #1e40af; margin-bottom: 4px;
      padding-bottom: 8px; border-bottom: 2px solid #e2e8f0;
    }}
    .location-link {{
      color: #3b82f6; font-size: 0.8rem; text-decoration: none;
      display: block; margin-bottom: 12px;
    }}
    .location-link:hover {{ text-decoration: underline; }}

    .cards {{ display: flex; flex-direction: column; gap: 12px; }}
    .card {{
      border-radius: 10px; padding: 16px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08); transition: transform 0.1s;
    }}
    .card:hover {{ transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.12); }}
    .card-header {{
      display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
    }}
    .rank {{ font-weight: 700; color: #64748b; font-size: 0.9rem; min-width: 28px; }}
    .grade {{
      color: white; font-weight: 700; padding: 2px 10px; border-radius: 6px;
      font-size: 0.9rem;
    }}
    .score {{ font-weight: 600; font-size: 0.95rem; }}
    .grade-label {{ color: #64748b; font-size: 0.85rem; }}
    .card-body h3 {{ font-size: 1rem; margin-bottom: 6px; }}
    .meta {{
      display: flex; flex-wrap: wrap; gap: 12px; font-size: 0.8rem;
      color: #64748b; margin-bottom: 8px;
    }}
    .tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px; }}
    .tag {{
      background: #e2e8f0; color: #475569; padding: 2px 8px;
      border-radius: 4px; font-size: 0.75rem;
    }}
    .feedback {{ display: flex; flex-direction: column; gap: 4px; }}
    .positive {{
      color: #16a34a; font-size: 0.85rem; font-weight: 500;
    }}
    .warning {{
      color: #d97706; font-size: 0.82rem; display: block;
    }}
    .warning-excluded {{
      color: #dc2626; font-weight: 600; font-size: 0.82rem; display: block;
    }}
    .no-meals {{ color: #94a3b8; font-style: italic; padding: 12px 0; }}

    footer {{
      text-align: center; color: #94a3b8; font-size: 0.8rem;
      padding: 20px 0; border-top: 1px solid #e2e8f0; margin-top: 20px;
    }}
    footer a {{ color: #3b82f6; text-decoration: none; }}

    @media (max-width: 600px) {{
      body {{ padding: 8px; }}
      header {{ padding: 16px; }}
      .card {{ padding: 12px; }}
      .meta {{ gap: 8px; }}
      .top-pick {{ flex-direction: column; align-items: flex-start; gap: 4px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>CED Mensa-Checker</h1>
    <div class="subtitle">Uni Bayreuth &middot; {_esc(mode_label)}</div>
    <div class="date">{weekday}, {date_str}</div>
  </header>

  <div class="summary">
    <h2>Tagesempfehlung</h2>
    {top_html}
  </div>

  {location_sections}

  <footer>
    CED Mensa-Checker &middot;
    Datenquelle: <a href="https://sls.swo.bayern">Studierendenwerk Oberfranken</a><br>
    Keine ärztliche Beratung. Bewertungen individuell anpassen.
  </footer>
</body>
</html>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _esc(text: str) -> str:
    """Escape HTML entities."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
