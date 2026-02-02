from fastapi import FastAPI

app = FastAPI(title="warehouse18")

@app.get("/health")
def health():
    return {"status": "ok"}
