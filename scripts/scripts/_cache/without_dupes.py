import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "mysim_locations_code_to_id.json"
OUTPUT_FILE = BASE_DIR / "mysim_locations_code_to_single_id.json"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el fichero de entrada:\n{path}\n\n"
            f"Coloca mysim_locations_code_to_id.json en esta carpeta:\n{BASE_DIR}"
        )

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, data: dict) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def pick_single_id(value: object) -> int | None:
    """
    Si el valor es:
    - int -> devuelve ese int
    - list[int] -> devuelve el ID más bajo
    - otro formato -> lo ignora
    """
    if isinstance(value, int):
        return value

    if isinstance(value, list):
        valid_ids = []

        for item in value:
            try:
                valid_ids.append(int(item))
            except (TypeError, ValueError):
                continue

        if not valid_ids:
            return None

        return min(valid_ids)

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_single_code_to_id(code_to_id: dict) -> tuple[dict, dict]:
    result = {}
    removed_duplicates = {}

    for location_code in sorted(code_to_id.keys()):
        value = code_to_id[location_code]
        selected_id = pick_single_id(value)

        if selected_id is None:
            continue

        result[location_code] = selected_id

        if isinstance(value, list) and len(value) > 1:
            removed_duplicates[location_code] = {
                "kept": selected_id,
                "original_ids": sorted([int(item) for item in value]),
            }

    return result, removed_duplicates


def main() -> None:
    code_to_id = load_json(INPUT_FILE)
    single_code_to_id, removed_duplicates = build_single_code_to_id(code_to_id)

    save_json(OUTPUT_FILE, single_code_to_id)

    print(f"Entrada: {INPUT_FILE}")
    print(f"Salida: {OUTPUT_FILE}")
    print(f"Total localizaciones: {len(single_code_to_id)}")
    print(f"Duplicados resueltos: {len(removed_duplicates)}")

    if removed_duplicates:
        print("\nDuplicados resueltos:")
        for location_code, info in removed_duplicates.items():
            print(
                f"{location_code}: mantenido {info['kept']} "
                f"de {info['original_ids']}"
            )


if __name__ == "__main__":
    main()