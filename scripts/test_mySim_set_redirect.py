from dotenv import load_dotenv
load_dotenv()

from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.errors import MySimError


def try_set(entity: str, obj: dict):
    cfg = MySimConfig.from_env()
    client = MySimClient(cfg)

    print("\n=== TEST SET ===")
    print("Entity:", entity)

    try:
        # un objeto “basura” a propósito (debería fallar con JSON si estuviese permitido)
        resp = client.set(entity=entity, objects=[obj])
        print("Response:", resp)

    except MySimError as e:
        print("MySimError:", str(e))
        print("status_code:", e.status_code)
        print("payload:", e.payload)


def main():
    # 1) Entidad inventada: si hay permisos, debería devolver JSON de error (400/404 interno),
    # pero NO debería redirigir a /index.
    try_set("___does_not_exist___", {"foo": "bar"})

    # 2) Una entidad real de lectura: igualmente debería devolver JSON de error por schema,
    # pero NO debería redirigir si /set estuviese permitido.
    try_set("accounts", {"id": -999999, "email": "nope@example.com"})


if __name__ == "__main__":
    main()
