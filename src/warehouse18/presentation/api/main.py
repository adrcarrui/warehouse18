from fastapi import FastAPI
from fastapi import FastAPI, HTTPException
from psycopg.errors import CheckViolation, ForeignKeyViolation

from warehouse18.infrastructure.db import get_conn
from warehouse18.presentation.api.schemas import (
    ReceiveContainerIn, ConsumeContainerIn, TransferContainerIn,
    ReceiveAssetIn, TransferAssetIn, IssueAssetIn,
    OkOut
)

app = FastAPI(title="warehouse18")

@app.get("/health")
def health():
    return {"status": "ok"}
