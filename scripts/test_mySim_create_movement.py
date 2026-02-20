from dotenv import load_dotenv
load_dotenv()

from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.application.mySim.movement_types import MovementType, SpecialLocation
from warehouse18.application.mySim.movement_request import MovementRequest


def main():
    cfg = MySimConfig.from_env()
    api = MySimAdapter(MySimClient(cfg))

    # ejemplo: último movimiento para sacar un part_id real (o ponlo fijo)
    part_code = "GEN-010838"
    part_id = api.get_part_id_by_part_code(part_code)
    if part_id is None:
        print("No se encontró part:", part_code)
        return

    req = MovementRequest(
        part_db_id=part_id,
        movement_type=MovementType.GOOD_TRACKING,
        description="RFID test: aesthetic defect noted",
        destination=SpecialLocation.UNKNOWN.value,  # tracking podría ir sin dest si lo decides, pero aquí lo meto opcional
    )

    resp = api.create_movement(req)
    print(resp)


if __name__ == "__main__":
    main()
