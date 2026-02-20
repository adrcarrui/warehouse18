from dotenv import load_dotenv
load_dotenv()

from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter


def main():
    cfg = MySimConfig.from_env()
    client = MySimClient(cfg)
    api = MySimAdapter(client)

    print("\n== USERS ==")
    users = api.get_all_users(limit=5)
    print(f"Users (5): {len(users)}")
    for u in users:
        print(" -", u.get("id"), u.get("fullName") or u.get("name"), u.get("email"))

    if users:
        uid = users[0].get("id")
        print("\nUser by id:", uid)
        print(api.get_user_by_id(uid))

    print("\n== LOCATIONS ==")
    # Si no existe 'locations', aquí petará y ya sabes que hay que ajustar el entity.
    locs = api.get_all_locations(entity="locations", limit=5)
    print(f"Locations (5): {len(locs)}")
    for l in locs:
        print(" -", l.get("id"), l.get("name") or l.get("locationName") or l)

    print("\n== PART -> MOVEMENTS ==")
    part_code = "GEN-010838"
    part_db_id = api.get_part_id_by_part_code(part_code)
    print("Part code:", part_code, "-> id:", part_db_id)

    if part_db_id is not None:
        moves = api.get_item_movements(item_id=part_db_id, item_entity="Parts", limit=5, newest_first=True)
        print(f"Movements (5): {len(moves)}")
        for m in moves:
            print(" -", m.get("movementId") or m.get("id"), m.get("date"), m.get("type") or m.get("movementType"))

        last = api.get_last_item_movement(item_id=part_db_id, item_entity="Parts")
        print("\nLast movement:")
        print(last)


if __name__ == "__main__":
    main()
