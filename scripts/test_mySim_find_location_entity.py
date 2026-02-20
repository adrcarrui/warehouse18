from dotenv import load_dotenv
load_dotenv()

from warehouse18.infrastructure.integrations.mySim.client import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.errors import MySimError
from warehouse18.infrastructure.integrations.mySim.client import rows_normalized

CANDIDATES = [
    "locations", "location",
]

def main():
    cfg = MySimConfig.from_env()
    c = MySimClient(cfg)

    test_id = 90  # destinationLocation que ya viste en un movimiento real

    for ent in CANDIDATES:
        try:
            resp = c.get(entity=ent, limit=5)
            rows = rows_normalized(resp)
            if rows:
                print(f"\n✅ ENTITY MATCH: {ent}")
                print(rows[0])
        except MySimError as e:
            # ignoramos errores "normales"
            pass

if __name__ == "__main__":
    main()
