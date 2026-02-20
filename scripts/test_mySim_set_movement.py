from dotenv import load_dotenv
load_dotenv()

from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.application.mySim.movement_types import MovementType
from warehouse18.application.mySim.movement_request import MovementRequest


def main():
    cfg = MySimConfig.from_env()
    api = MySimAdapter(MySimClient(cfg))

    # 1) Resolvemos un part real
    part_code = "GEN-010838"
    part_id = api.get_part_id_by_part_code(part_code)

    if not part_id:
        print("No se encontró el part")
        return

    print("Part ID:", part_id)

    # 2) Creamos un movimiento sencillo (Good tracking es el más seguro)
    req = MovementRequest(
        part_db_id=part_id,
        movement_type=MovementType.GOOD_TRACKING,
        description="Test movement via SET"
    )

    # 3) Llamamos
    resp = api.create_movement(req)

    print("\nRespuesta mySim:")
    print(resp)


if __name__ == "__main__":
    main()
