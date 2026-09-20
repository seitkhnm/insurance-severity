# Insurance service в Kubernetes

Манифесты адаптированы из [ML_PRO2026/k8s](https://github.com/artemovmak/ML_PRO2026/tree/main/k8s) для текущего приложения `severity`.

| Файл | Назначение |
| --- | --- |
| `configmap.yaml` | Путь к модели внутри образа и уровень логирования |
| `secret.yaml.example` | Шаблон локального Secret с паролем PostgreSQL и `DATABASE_URL` |
| `deployment.yaml` | API `insurance-service:1.0`, ожидание БД и проверки `/health`, `/ready` |
| `service.yaml` | ClusterIP-сервис API: порт 80 → 8000 |
| `postgres.yaml` | PostgreSQL 17, сервис `postgres` и постоянный том 1 GiB |

База называется `insurance`, пользователь — `postgres`. Создай локальный `secret.yaml` из шаблона `secret.yaml.example` и укажи одинаковый URL-безопасный пароль в `POSTGRES_PASSWORD` и `DATABASE_URL`. Файл `secret.yaml` исключён из Git. Для уже инициализированной БД пароль роли нужно изменить отдельно: обновление Secret не меняет пароль в существующем PVC. Манифесты предназначены для локального учебного запуска.

API стартует в одной реплике и создаёт таблицу `predictions` при запуске. InitContainer сначала проверяет подключение к PostgreSQL. База Kubernetes использует отдельное хранилище: записи из Docker Compose автоматически не переносятся. Перезапуск pod сохраняет данные PVC; удаление локального kind-кластера удалит и его хранилище.

## Запуск через kind

Нужны запущенный Docker, `kind` и `kubectl`. Выполняй команды из корня проекта, где находятся `Dockerfile`, `good.json` и эта папка:

```bash
docker build -t insurance-service:1.0 .
```

Создай кластер один раз. Если кластер `insurance` уже существует, пропусти эту команду:

```bash
kind create cluster --name insurance
```

Подготовь локальный Secret:

```bash
cp k8s/secret.yaml.example k8s/secret.yaml
```

Замени `replace-with-your-password` в обоих полях файла `k8s/secret.yaml`. Шаблон с расширением `.example` не применяется командой `kubectl apply -f k8s/`. Не коммить файл с настоящим паролем.

Загрузи локальный Docker-образ в узлы kind, затем примени манифесты:

```bash
kind load docker-image insurance-service:1.0 --name insurance
kubectl --context kind-insurance apply -f k8s/
kubectl --context kind-insurance rollout status deployment/postgres --timeout=180s
kubectl --context kind-insurance rollout status deployment/insurance-service --timeout=180s
kubectl --context kind-insurance get pods,services,pvc
```

PVC использует StorageClass по умолчанию. В kind она доступна; для другого кластера проверь `kubectl get storageclass` и наличие динамического выделения томов.

## Запрос из good.json

Открой проброс порта и оставь команду работающей. Порт 8001 выбран, чтобы не занимать порт 8000 работающего Docker Compose:

```bash
kubectl --context kind-insurance port-forward service/insurance-service 8001:80
```

В другом терминале, из корня проекта:

```bash
curl http://127.0.0.1:8001/ready

curl -X POST http://127.0.0.1:8001/v1/predict \
  -H "Content-Type: application/json" \
  --data-binary @good.json
```

Swagger: <http://127.0.0.1:8001/docs>.

Проверь сохранённый прогноз:

```bash
kubectl --context kind-insurance exec deployment/postgres -- \
  psql -U postgres -d insurance \
  -c "SELECT request_id, score, latency_ms FROM predictions ORDER BY ts DESC LIMIT 10;"
```

## Обновление приложения или модели

```bash
docker build -t insurance-service:1.0 .
kind load docker-image insurance-service:1.0 --name insurance
kubectl --context kind-insurance apply -f k8s/
kubectl --context kind-insurance rollout restart deployment/insurance-service
kubectl --context kind-insurance rollout status deployment/insurance-service --timeout=180s
```

Поскольку тег образа остаётся прежним, после загрузки обновлённого образа требуется перезапуск pod.

## Диагностика

```bash
kubectl --context kind-insurance logs deployment/insurance-service -c wait-for-postgres
kubectl --context kind-insurance logs deployment/insurance-service -c api
kubectl --context kind-insurance logs deployment/postgres
kubectl --context kind-insurance get events --sort-by=.lastTimestamp
```

`/ready` в текущем коде проверяет загрузку модели. Готовность к сохранению прогнозов после запуска проверяй реальным POST-запросом и чтением таблицы, как показано выше.
