# Trained model artifacts

`severity_gradient_boosting.joblib` contains the fitted preprocessing, median imputation, and GradientBoostingRegressor pipeline plus metadata. The API loads this bundle at startup.

`severity_metadata.json` and `model_severity_summary.csv` record model metadata and evaluation results. Retrain using the notebook in the repository root.
