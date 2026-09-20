# Insurance severity prediction

FastAPI service for predicting insurance claim severity with a trained scikit-learn pipeline: preprocessing, median imputation, and GradientBoostingRegressor. The project includes a training notebook, synthetic data, a saved model, API tests, Docker Compose, and Kubernetes manifests.

## Docker Compose

Choose a URL-safe development password and start the API and PostgreSQL:

```bash
export POSTGRES_PASSWORD='replace-with-your-password'
docker compose up --build -d
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

Send the example request:

```bash
curl --fail-with-body -X POST http://localhost:8000/v1/predict \
  -H 'Content-Type: application/json' --data @good.json
```

The response includes `severity`, `model_version`, `request_id`, and `latency_ms`. `sum_insured` accepts `null`; the trained pipeline imputes missing values.

View saved predictions:

```bash
docker compose exec db psql -U postgres -d insurance \
  -c "SELECT request_id, score, latency_ms FROM predictions ORDER BY ts DESC LIMIT 10;"
```

`docker compose down` stops the services while preserving the database volume. Changing the environment password does not change the password of an existing PostgreSQL role.

## Local development

Install Python and uv, then run:

```bash
uv sync
uv run pytest
uv run uvicorn severity.service.app:app --host 127.0.0.1 --port 8000
```

Local prediction works without PostgreSQL when `DATABASE_URL` is unset. Set it to enable prediction logging. The service loads `artifact/severity_gradient_boosting.joblib`. Retrain with `model_severity.ipynb` and the synthetic dataset in `data/`.

## Kubernetes with kind

```bash
kind create cluster --name insurance
docker build -t insurance-service:1.0 .
kind load docker-image insurance-service:1.0 --name insurance
cp k8s/secret.yaml.example k8s/secret.yaml
```

Edit the local `k8s/secret.yaml` and replace the placeholder with the same URL-safe password in both fields. Do not commit this file. The `.example` template is not applied by kubectl.

```bash
kubectl --context kind-insurance apply -f k8s/
kubectl --context kind-insurance rollout status deployment/postgres
kubectl --context kind-insurance rollout status deployment/insurance-service
kubectl --context kind-insurance port-forward service/insurance-service 8001:80
```

In another terminal:

```bash
curl --fail-with-body -X POST http://localhost:8001/v1/predict \
  -H 'Content-Type: application/json' --data @good.json
```

Kubernetes uses a separate database volume from Docker Compose. See `k8s/README.md` for deployment details.
