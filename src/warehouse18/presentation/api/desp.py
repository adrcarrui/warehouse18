from functools import lru_cache
from warehouse18.infrastructure.integrations.mySim.client import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter

@lru_cache
def get_mysim_client() -> MySimClient:
    cfg = MySimConfig.from_env()
    return MySimClient(cfg)

def get_mysim_gateway() -> MySimAdapter:
    return MySimAdapter(get_mysim_client())
