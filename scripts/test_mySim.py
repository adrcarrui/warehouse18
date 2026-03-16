from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter

cfg = MySimConfig.from_env()
client = MySimClient(cfg)
api = MySimAdapter(client)

print("BASE:", cfg.base_url)
print("TOKEN?", bool(cfg.token), "LEN:", len(cfg.token or ""))

print(api.get_part_id_by_part_code("CN235-015922"))