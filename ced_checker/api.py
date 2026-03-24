import requests
from ced_checker.models import Meal


def fetch_meals(base_url: str, api_path: str, location_name: str,
                date: str, categories: list[str]) -> list[Meal]:
    url = f"{base_url}{api_path}"
    payload = {
        "date": date,
        "location_name": location_name,
        "categories": categories,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.ConnectionError:
        print(f"  [!] Verbindungsfehler: {url}")
        return []
    except requests.Timeout:
        print(f"  [!] Zeitüberschreitung: {url}")
        return []
    except requests.HTTPError as e:
        print(f"  [!] HTTP-Fehler {resp.status_code}: {url}")
        return []

    data = resp.json()
    if not isinstance(data, list):
        return []

    return [Meal.from_api(item) for item in data]
