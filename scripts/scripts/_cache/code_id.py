from pathlib import Path
import json
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "mysim_locations_by_id.json"
OUTPUT_FILE = BASE_DIR / "mysim_locations_code_to_id.json"


def normalize_location(value: object) -> str:
    return str(value).strip().upper()


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el fichero de entrada:\n{path}\n\n"
            f"Coloca mysim_locations_by_id.json en esta carpeta:\n{BASE_DIR}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def build_code_to_id(data: dict) -> dict:
    grouped = defaultdict(list)

    for raw_key, raw_value in data.items():
        if isinstance(raw_value, dict):
            location_code = raw_value.get("code")
            location_id = raw_value.get("id", raw_key)
        else:
            location_code = raw_key
            location_id = raw_value

        if location_code is None or str(location_code).strip() == "":
            continue

        try:
            location_id = int(location_id)
        except (TypeError, ValueError):
            continue

        location_code = normalize_location(location_code)

        if location_id not in grouped[location_code]:
            grouped[location_code].append(location_id)

    result = {}

    for location_code in sorted(grouped.keys()):
        ids = sorted(grouped[location_code])

        if len(ids) == 1:
            result[location_code] = ids[0]
        else:
            result[location_code] = ids

    return result


def main() -> None:
    data = load_json(INPUT_FILE)
    code_to_id = build_code_to_id(data)

    save_json(OUTPUT_FILE, code_to_id)

    duplicated = {
        location: ids
        for location, ids in code_to_id.items()
        if isinstance(ids, list)
    }

    print(f"Entrada: {INPUT_FILE}")
    print(f"Salida: {OUTPUT_FILE}")
    print(f"Total localizaciones: {len(code_to_id)}")
    print(f"Localizaciones duplicadas: {len(duplicated)}")

    if duplicated:
        print("\nDuplicadas encontradas:")
        for location, ids in duplicated.items():
            print(f"{location}: {ids}")


if __name__ == "__main__":
    main()