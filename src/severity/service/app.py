import time
import uuid

from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException

from pydantic import BaseModel, Field

from severity import db
from severity.config import settings

class Features(BaseModel):
    model_config = {"extra": "forbid"}

    policy_id: str
    exposure: float = Field(gt=0)
    driver_age: int
    years_licensed: int
    vehicle_age: int
    vehicle_type: str
    engine_power_kw: int
    annual_mileage_km: int
    region: str
    urban_density: str
    garage: bool
    bonus_malus: float
    prior_claims_3y: int
    commercial_use: bool
    telematics_opt_in: bool
    sum_insured: float | None = None
    policy_year: int
    num_claims: int
    total_claim_amount: float
    avg_claim_amount: float


class Prediction(BaseModel):
    severity: float
    model_version: str
    request_id: str
    latency_ms: float


from pathlib import Path

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path = Path(settings.model_path).expanduser().resolve()
    bundle = joblib.load(model_path)

    app.state.pipeline = bundle["pipeline"]
    app.state.meta = bundle["metadata"]
    app.state.version = bundle["metadata"]["model_version"]

    db.init()
    try:
        yield
    finally:
        app.state.pipeline = None


app = FastAPI(title="insurance", version="1.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok", "model_version": getattr(app.state, "version", "unknown")}

@app.get("/ready")
def ready():
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}



@app.post("/v1/predict")
def predict(x: Features, bg: BackgroundTasks) -> Prediction:
    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())

    payload = x.model_dump()

    frame = pd.DataFrame([payload]).reindex(
        columns=app.state.meta["features"]
    )

    severity = float(app.state.pipeline.predict(frame)[0])

    latency_ms = round(
        (time.perf_counter() - t0) * 1000,
        2
    )

    bg.add_task(
        db.save_prediction,
        request_id,
        payload,
        severity,
        app.state.version,
        latency_ms
    )

    return Prediction(
        severity=severity,
        model_version=app.state.version,
        request_id=request_id,
        latency_ms=latency_ms
    )