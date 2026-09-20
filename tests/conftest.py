import pytest
from fastapi.testclient import TestClient

from severity.service.app import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def good_row():
    return {
    "policy_id": "P0000005",
    "exposure": 1.0,
    "driver_age": 48,
    "years_licensed": 32,
    "vehicle_age": 5,
    "vehicle_type": "sedan",
    "engine_power_kw": 96,
    "annual_mileage_km": 10008,
    "region": "NW",
    "urban_density": "urban",
    "garage": False,
    "bonus_malus": 0.925741,
    "prior_claims_3y": 0,
    "commercial_use": False,
    "telematics_opt_in": True,
    "sum_insured": 33456.311194,
    "policy_year": 2023,
    "num_claims": 1,
    "total_claim_amount": 152.37,
    "avg_claim_amount": 152.37
    }