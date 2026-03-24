"""Generate a static HTML page with client-side CED meal analysis.

Embeds raw meal data and config defaults as JSON. JavaScript handles
analysis, rendering, and user customization with localStorage persistence.
"""

from datetime import date
from pathlib import Path


WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag",
               "Freitag", "Samstag", "Sonntag"]


def generate_html_dual(
    target_date: date,
    meals_json: str,
    allergens_json: str,
    foods_json: str,
    default_mode: str,
    output_path: Path,
) -> Path:
    """Generate a self-contained HTML page with JS-based analysis and settings panel."""
    weekday = WEEKDAYS_DE[target_date.weekday()]
    date_str = target_date.strftime("%d.%m.%Y")
    date_iso = target_date.isoformat()

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
      color: white; padding: 24px; border-radius: 12px; margin-bottom: 16px;
      text-align: center;
    }}
    header h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
    header .subtitle {{ opacity: 0.9; font-size: 0.95rem; }}
    header .date {{ font-size: 1.1rem; font-weight: 600; margin-top: 8px; }}
    .mode-toggle {{
      display: flex; justify-content: center; gap: 0;
      margin-bottom: 16px; background: #e2e8f0; border-radius: 10px;
      padding: 4px; max-width: 420px; margin-left: auto; margin-right: auto;
    }}
    .mode-btn {{
      flex: 1; padding: 10px 16px; border: none; background: transparent;
      font-size: 0.95rem; font-weight: 600; color: #64748b;
      cursor: pointer; border-radius: 8px; transition: all 0.2s;
    }}
    .mode-btn:hover {{ color: #1e293b; }}
    .mode-btn.active {{
      background: white; color: #1e40af;
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }}
    .disclaimer {{
      background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px;
      padding: 12px 16px; margin-bottom: 20px; text-align: center;
      font-size: 0.9rem; color: #92400e; font-weight: 500;
    }}
    .summary {{
      background: white; border-radius: 12px; padding: 20px;
      margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    .summary h2 {{ font-size: 1.1rem; margin-bottom: 12px; color: #1e40af; }}
    .top-pick {{
      display: flex; align-items: center; gap: 10px; padding: 10px 12px;
      background: #f8fafc; border-radius: 8px; margin-bottom: 8px; flex-wrap: wrap;
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
    .card-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
    .rank {{ font-weight: 700; color: #64748b; font-size: 0.9rem; min-width: 28px; }}
    .grade {{
      color: white; font-weight: 700; padding: 2px 10px; border-radius: 6px; font-size: 0.9rem;
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
    .positive {{ color: #16a34a; font-size: 0.85rem; font-weight: 500; }}
    .warning {{ color: #d97706; font-size: 0.82rem; display: block; }}
    .warning-excluded {{ color: #dc2626; font-weight: 600; font-size: 0.82rem; display: block; }}
    .no-meals {{ color: #94a3b8; font-style: italic; padding: 12px 0; }}
    footer {{
      text-align: center; color: #94a3b8; font-size: 0.8rem;
      padding: 20px 0; border-top: 1px solid #e2e8f0; margin-top: 20px;
    }}
    footer a {{ color: #3b82f6; text-decoration: none; }}

    /* Settings panel */
    .settings-panel {{
      background: white; border-radius: 12px; margin-top: 24px; margin-bottom: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden;
    }}
    .settings-panel summary {{
      padding: 16px 20px; cursor: pointer; font-weight: 600; font-size: 1rem;
      color: #1e40af; list-style: none; display: flex; align-items: center; gap: 8px;
      user-select: none;
    }}
    .settings-panel summary::-webkit-details-marker {{ display: none; }}
    .settings-panel summary::before {{ content: "\\2699"; font-size: 1.2rem; }}
    .settings-panel[open] summary {{ border-bottom: 1px solid #e2e8f0; }}
    .settings-inner {{ padding: 16px 20px; }}
    .settings-tabs {{
      display: flex; gap: 0; background: #e2e8f0; border-radius: 8px;
      padding: 3px; margin-bottom: 12px;
    }}
    .settings-tab-btn {{
      flex: 1; padding: 8px 12px; border: none; background: transparent;
      font-size: 0.85rem; font-weight: 600; color: #64748b;
      cursor: pointer; border-radius: 6px; transition: all 0.2s;
    }}
    .settings-tab-btn.active {{
      background: white; color: #1e40af; box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }}
    .settings-actions {{
      display: flex; justify-content: space-between; align-items: center;
      margin-bottom: 12px; flex-wrap: wrap; gap: 8px;
    }}
    .settings-reset {{
      padding: 6px 14px; border: 1px solid #e2e8f0; border-radius: 6px;
      background: white; color: #64748b; font-size: 0.82rem; cursor: pointer;
      transition: all 0.2s;
    }}
    .settings-reset:hover {{ background: #fee2e2; color: #dc2626; border-color: #fca5a5; }}
    .settings-count {{ font-size: 0.8rem; color: #94a3b8; }}
    .settings-list {{
      max-height: 420px; overflow-y: auto; border: 1px solid #e2e8f0;
      border-radius: 8px;
    }}
    .settings-row {{
      display: flex; align-items: center; padding: 8px 12px;
      border-bottom: 1px solid #f1f5f9; gap: 12px;
    }}
    .settings-row:last-child {{ border-bottom: none; }}
    .settings-row:nth-child(odd) {{ background: #f8fafc; }}
    .settings-code {{ font-weight: 600; color: #64748b; min-width: 32px; font-size: 0.82rem; }}
    .settings-desc {{ flex: 1; font-size: 0.85rem; min-width: 120px; }}
    .settings-select {{
      padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 6px;
      font-size: 0.82rem; background: white; cursor: pointer; min-width: 130px;
    }}
    .settings-select.modified {{
      background: #fef3c7; border-color: #f59e0b; font-weight: 600;
    }}
    .settings-tab-content {{ display: none; }}
    .settings-tab-content.visible {{ display: block; }}

    @media (max-width: 600px) {{
      body {{ padding: 8px; }}
      header {{ padding: 16px; }}
      .card {{ padding: 12px; }}
      .meta {{ gap: 8px; }}
      .top-pick {{ flex-direction: column; align-items: flex-start; gap: 4px; }}
      .mode-btn {{ padding: 8px 10px; font-size: 0.85rem; }}
      .settings-row {{ flex-wrap: wrap; }}
      .settings-select {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>CED Mensa-Checker</h1>
    <div class="subtitle">Uni Bayreuth</div>
    <div class="date">{weekday}, {date_str}</div>
  </header>

  <div class="mode-toggle">
    <button class="mode-btn" data-mode="crohn" onclick="switchMode('crohn')">Morbus Crohn</button>
    <button class="mode-btn" data-mode="colitis" onclick="switchMode('colitis')">Colitis ulcerosa</button>
  </div>

  <div class="disclaimer">
    Keine &auml;rztliche oder di&auml;tologische Beratung! Bewertungen individuell anpassen!
  </div>

  <div id="content"></div>

  <details class="settings-panel">
    <summary>Bewertungen anpassen</summary>
    <div class="settings-inner">
      <div class="settings-tabs">
        <button class="settings-tab-btn active" onclick="switchSettingsTab('allergens')">Allergene / Zusatzstoffe</button>
        <button class="settings-tab-btn" onclick="switchSettingsTab('foods')">Nahrungsmittel</button>
      </div>
      <div class="settings-actions">
        <button class="settings-reset" onclick="resetToDefaults()">Auf Standard zur&uuml;cksetzen</button>
        <span class="settings-count" id="settings-count"></span>
      </div>
      <div id="settings-tab-allergens" class="settings-tab-content visible"></div>
      <div id="settings-tab-foods" class="settings-tab-content"></div>
    </div>
  </details>

  <footer>
    CED Mensa-Checker &middot;
    Datenquelle: <a href="https://sls.swo.bayern">Studierendenwerk Oberfranken</a><br>
    Keine &auml;rztliche oder di&auml;tologische Beratung. Bewertungen individuell anpassen.
  </footer>

  <!-- Embedded data -->
  <script>
    window.CED_MEALS = {meals_json};
    window.CED_DEFAULTS_ALLERGENS = {allergens_json};
    window.CED_DEFAULTS_FOODS = {foods_json};
    window.CED_META = {{"dateIso": "{date_iso}", "defaultMode": "{default_mode}"}};
  </script>

  <script>
    "use strict";

    // ===== Grade constants =====
    const GRADE_COLORS = {{A:"#22c55e",B:"#86efac",C:"#eab308",D:"#f97316",E:"#ef4444",F:"#dc2626"}};
    const GRADE_BG = {{A:"#f0fdf4",B:"#f0fdf4",C:"#fefce8",D:"#fff7ed",E:"#fef2f2",F:"#fef2f2"}};
    const GRADE_LABELS = {{
      A:"sehr gut vertr\\u00e4glich", B:"gut vertr\\u00e4glich",
      C:"bedingt vertr\\u00e4glich", D:"schlecht vertr\\u00e4glich",
      E:"sehr schlecht vertr\\u00e4glich", F:"ausgeschlossen"
    }};

    let currentMode = window.CED_META.defaultMode;

    // ===== Analyzer (port of analyzer.py) =====

    function scoreToGrade(score, excluded) {{
      if (excluded || score <= 0) return "F";
      if (score >= 9) return "A";
      if (score >= 7) return "B";
      if (score >= 5) return "C";
      if (score >= 3) return "D";
      return "E";
    }}

    function analyzeMeal(meal, allergenCfg, foodCfg) {{
      let score = 10;
      const warnings = [];
      const positives = [];
      let excluded = false;

      // 1) Check allergen codes
      for (const code of meal.allergen_codes) {{
        const entry = allergenCfg[code];
        if (!entry) continue;
        if (entry.bewertung === "ausgeschlossen") {{
          excluded = true;
          warnings.push("AUSGESCHLOSSEN: " + entry.beschreibung + " [" + code + "]");
        }} else if (entry.bewertung === "vermeiden") {{
          score -= 2;
          warnings.push("Vermeiden: " + entry.beschreibung + " [" + code + "]");
        }}
      }}

      // 2) Check legend tags
      for (const tag of meal.legend_tags) {{
        const key = tag.toLowerCase();
        const entry = foodCfg[key];
        if (!entry) continue;
        if (entry.bewertung === "ausgeschlossen") {{
          excluded = true;
          warnings.push("AUSGESCHLOSSEN: " + entry.name);
        }} else if (entry.bewertung === "vermeiden") {{
          score -= 2;
          warnings.push("Vermeiden: " + entry.name);
        }} else if (entry.bewertung === "empfohlen") {{
          score += 1;
          positives.push(entry.name);
        }}
      }}

      // 3) Keyword matching in title
      const titleLower = meal.title.toLowerCase();
      const legendLower = new Set(meal.legend_tags.map(t => t.toLowerCase()));
      for (const [key, entry] of Object.entries(foodCfg)) {{
        if (legendLower.has(key)) continue;
        if (titleLower.includes(key)) {{
          if (entry.bewertung === "ausgeschlossen") {{
            excluded = true;
            warnings.push("AUSGESCHLOSSEN im Titel: " + entry.name);
          }} else if (entry.bewertung === "vermeiden") {{
            score -= 2;
            warnings.push("Vermeiden (Titel): " + entry.name);
          }} else if (entry.bewertung === "empfohlen") {{
            score += 1;
            positives.push(entry.name + " (Titel)");
          }}
        }}
      }}

      score = Math.max(0, Math.min(10, score));
      const grade = scoreToGrade(score, excluded);

      return {{
        meal, score: excluded ? 0 : score, grade, warnings, positives, excluded
      }};
    }}

    function analyzeAndRank(meals, allergenCfg, foodCfg) {{
      const ratings = meals.map(m => analyzeMeal(m, allergenCfg, foodCfg));
      ratings.sort((a, b) => b.score - a.score || a.meal.title.localeCompare(b.meal.title));
      return ratings;
    }}

    // ===== Config resolution =====

    function getActiveConfig(mode) {{
      // Allergens
      const customAllergens = loadJson("ced-custom-allergens") || {{}};
      const modeOverrides = (customAllergens[mode]) || {{}};
      const allergenCfg = {{}};
      for (const [code, entry] of Object.entries(window.CED_DEFAULTS_ALLERGENS)) {{
        allergenCfg[code] = {{
          beschreibung: entry.beschreibung,
          bewertung: modeOverrides[code] || entry[mode]
        }};
      }}

      // Foods
      const customFoods = loadJson("ced-custom-foods") || {{}};
      const foodOverrides = (customFoods[mode]) || {{}};
      const foodCfg = {{}};
      for (const [key, entry] of Object.entries(window.CED_DEFAULTS_FOODS)) {{
        foodCfg[key] = {{
          name: entry.name,
          bewertung: foodOverrides[key] || entry[mode]
        }};
      }}

      return {{ allergenCfg, foodCfg }};
    }}

    // ===== localStorage helpers =====

    function loadJson(key) {{
      try {{ const v = localStorage.getItem(key); return v ? JSON.parse(v) : null; }}
      catch(e) {{ return null; }}
    }}

    function saveJson(key, obj) {{
      try {{ localStorage.setItem(key, JSON.stringify(obj)); }} catch(e) {{}}
    }}

    // ===== HTML helpers =====

    function esc(text) {{
      const d = document.createElement("div");
      d.textContent = text;
      return d.innerHTML;
    }}

    // ===== Renderer =====

    function renderAll() {{
      const {{ allergenCfg, foodCfg }} = getActiveConfig(currentMode);
      const dateIso = window.CED_META.dateIso;

      // Analyze all locations
      const allResults = [];
      for (const loc of window.CED_MEALS) {{
        const ratings = analyzeAndRank(loc.meals, allergenCfg, foodCfg);
        allResults.push({{ label: loc.label, webUrl: loc.web_url, ratings }});
      }}

      // Top picks
      const combined = [];
      for (const loc of allResults) {{
        for (const r of loc.ratings) {{
          if (!r.excluded) combined.push({{ loc: loc.label, r }});
        }}
      }}
      combined.sort((a, b) => b.r.score - a.r.score);
      const top3 = combined.slice(0, 3);

      const modeLabel = currentMode === "crohn" ? "Morbus Crohn" : "Colitis ulcerosa";
      let topHtml = "";
      if (top3.length === 0) {{
        topHtml = '<p class="no-meals">Keine vertr&auml;glichen Gerichte gefunden.</p>';
      }} else {{
        for (let i = 0; i < top3.length; i++) {{
          const {{ loc, r }} = top3[i];
          const c = GRADE_COLORS[r.grade] || "#888";
          topHtml += `
            <div class="top-pick" style="border-left:4px solid ${{c}}">
              <span class="top-rank">#${{i+1}}</span>
              <span class="grade" style="background:${{c}}">${{r.grade}}</span>
              <span class="top-score">${{r.score}}/10</span>
              <span class="top-title">${{esc(r.meal.title)}}</span>
              <span class="top-loc">${{esc(loc)}} &middot; ${{r.meal.price.toFixed(2)}} &euro;</span>
            </div>`;
        }}
      }}

      // Location sections
      let locsHtml = "";
      for (const loc of allResults) {{
        const displayUrl = `${{loc.webUrl}}#/${{dateIso}}/student`;
        let cardsHtml = "";
        if (loc.ratings.length === 0) {{
          cardsHtml = '<p class="no-meals">Keine Gerichte verf&uuml;gbar.</p>';
        }} else {{
          for (let rank = 0; rank < loc.ratings.length; rank++) {{
            const r = loc.ratings[rank];
            const c = GRADE_COLORS[r.grade] || "#888";
            const bg = GRADE_BG[r.grade] || "#fff";
            const gl = GRADE_LABELS[r.grade] || "";

            const tagsH = r.meal.legend_tags.map(t => `<span class="tag">${{esc(t)}}</span>`).join("");
            const posH = r.positives.length ? `<span class="positive">+ ${{esc(r.positives.join(", "))}}</span>` : "";
            let warnH = "";
            for (const w of r.warnings) {{
              const cls = w.startsWith("AUSGESCHLOSSEN") ? "warning-excluded" : "warning";
              warnH += `<span class="${{cls}}">${{esc(w)}}</span>`;
            }}

            cardsHtml += `
              <div class="card" style="border-left:4px solid ${{c}};background:${{bg}}">
                <div class="card-header">
                  <div class="rank">#${{rank+1}}</div>
                  <div class="grade" style="background:${{c}}">${{r.grade}}</div>
                  <div class="score">${{r.score}}/10</div>
                  <div class="grade-label">${{gl}}</div>
                </div>
                <div class="card-body">
                  <h3>${{esc(r.meal.title)}}</h3>
                  <div class="meta">
                    <span>${{r.meal.price.toFixed(2)}} &euro;</span>
                    <span>${{r.meal.calories}} kcal</span>
                    <span>Protein: ${{r.meal.protein}}g</span>
                    <span>Fett: ${{r.meal.fat}}g</span>
                    <span>Ballaststoffe: ${{r.meal.fiber}}g</span>
                  </div>
                  <div class="tags">${{tagsH}}</div>
                  <div class="feedback">${{posH}}${{warnH}}</div>
                </div>
              </div>`;
          }}
        }}

        locsHtml += `
          <section class="location">
            <h2>${{esc(loc.label)}}</h2>
            <a href="${{displayUrl}}" target="_blank" class="location-link">${{displayUrl}}</a>
            <div class="cards">${{cardsHtml}}</div>
          </section>`;
      }}

      document.getElementById("content").innerHTML = `
        <div class="summary">
          <h2>Tagesempfehlung &mdash; ${{esc(modeLabel)}}</h2>
          ${{topHtml}}
        </div>
        ${{locsHtml}}`;
    }}

    // ===== Settings panel =====

    function renderSettingsPanel() {{
      renderAllergenSettings();
      renderFoodSettings();
      updateSettingsCount();
    }}

    function renderAllergenSettings() {{
      const container = document.getElementById("settings-tab-allergens");
      const customAll = loadJson("ced-custom-allergens") || {{}};
      const overrides = customAll[currentMode] || {{}};
      const options = ["akzeptabel", "vermeiden", "ausgeschlossen"];

      let rows = "";
      for (const [code, entry] of Object.entries(window.CED_DEFAULTS_ALLERGENS)) {{
        const defaultVal = entry[currentMode];
        const currentVal = overrides[code] || defaultVal;
        const modified = overrides[code] ? "modified" : "";
        const opts = options.map(o =>
          `<option value="${{o}}" ${{o === currentVal ? "selected" : ""}}>${{o}}</option>`
        ).join("");

        rows += `
          <div class="settings-row">
            <span class="settings-code">${{esc(code)}}</span>
            <span class="settings-desc">${{esc(entry.beschreibung)}}</span>
            <select class="settings-select ${{modified}}"
                    data-type="allergens" data-key="${{esc(code)}}" data-default="${{defaultVal}}"
                    onchange="onSettingChange(this)">
              ${{opts}}
            </select>
          </div>`;
      }}
      container.innerHTML = `<div class="settings-list">${{rows}}</div>`;
    }}

    function renderFoodSettings() {{
      const container = document.getElementById("settings-tab-foods");
      const customAll = loadJson("ced-custom-foods") || {{}};
      const overrides = customAll[currentMode] || {{}};
      const options = ["empfohlen", "akzeptabel", "vermeiden", "ausgeschlossen"];

      let rows = "";
      for (const [key, entry] of Object.entries(window.CED_DEFAULTS_FOODS)) {{
        const defaultVal = entry[currentMode];
        const currentVal = overrides[key] || defaultVal;
        const modified = overrides[key] ? "modified" : "";
        const opts = options.map(o =>
          `<option value="${{o}}" ${{o === currentVal ? "selected" : ""}}>${{o}}</option>`
        ).join("");

        rows += `
          <div class="settings-row">
            <span class="settings-code"></span>
            <span class="settings-desc">${{esc(entry.name)}}</span>
            <select class="settings-select ${{modified}}"
                    data-type="foods" data-key="${{esc(key)}}" data-default="${{defaultVal}}"
                    onchange="onSettingChange(this)">
              ${{opts}}
            </select>
          </div>`;
      }}
      container.innerHTML = `<div class="settings-list">${{rows}}</div>`;
    }}

    function onSettingChange(el) {{
      const type = el.dataset.type;
      const key = el.dataset.key;
      const defaultVal = el.dataset.default;
      const newVal = el.value;

      const storageKey = type === "allergens" ? "ced-custom-allergens" : "ced-custom-foods";
      const custom = loadJson(storageKey) || {{}};
      if (!custom[currentMode]) custom[currentMode] = {{}};

      if (newVal === defaultVal) {{
        delete custom[currentMode][key];
        if (Object.keys(custom[currentMode]).length === 0) delete custom[currentMode];
        el.classList.remove("modified");
      }} else {{
        custom[currentMode][key] = newVal;
        el.classList.add("modified");
      }}

      saveJson(storageKey, custom);
      updateSettingsCount();
      renderAll();
    }}

    function updateSettingsCount() {{
      const ca = loadJson("ced-custom-allergens") || {{}};
      const cf = loadJson("ced-custom-foods") || {{}};
      const countA = Object.keys(ca[currentMode] || {{}}).length;
      const countF = Object.keys(cf[currentMode] || {{}}).length;
      const total = countA + countF;
      const el = document.getElementById("settings-count");
      el.textContent = total > 0 ? total + " Anpassung" + (total > 1 ? "en" : "") : "";
    }}

    function resetToDefaults() {{
      const ca = loadJson("ced-custom-allergens") || {{}};
      const cf = loadJson("ced-custom-foods") || {{}};
      delete ca[currentMode];
      delete cf[currentMode];
      saveJson("ced-custom-allergens", ca);
      saveJson("ced-custom-foods", cf);
      renderSettingsPanel();
      renderAll();
    }}

    function switchSettingsTab(tab) {{
      document.getElementById("settings-tab-allergens").classList.toggle("visible", tab === "allergens");
      document.getElementById("settings-tab-foods").classList.toggle("visible", tab === "foods");
      document.querySelectorAll(".settings-tab-btn").forEach((btn, i) => {{
        btn.classList.toggle("active", (i === 0 && tab === "allergens") || (i === 1 && tab === "foods"));
      }});
    }}

    // ===== Mode toggle =====

    function switchMode(mode) {{
      currentMode = mode;
      document.querySelectorAll(".mode-btn").forEach(btn => {{
        btn.classList.toggle("active", btn.dataset.mode === mode);
      }});
      try {{ localStorage.setItem("ced-mode", mode); }} catch(e) {{}}
      renderAll();
      renderSettingsPanel();
    }}

    // ===== Init =====

    (function init() {{
      const saved = loadJson("ced-mode") || localStorage.getItem("ced-mode");
      const mode = (saved === "crohn" || saved === "colitis") ? saved : window.CED_META.defaultMode;
      switchMode(mode);
    }})();
  </script>
</body>
</html>'''

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
