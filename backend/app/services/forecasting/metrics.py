import numpy as np


def calculate_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """
    Calculate forecasting evaluation metrics.
    Returns dict with MAPE, MAE, RMSE, R², and SMAPE.
    """
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    n = len(actual)
    if n == 0:
        return {"mape": 0, "mae": 0, "rmse": 0, "r2": 0, "smape": 0}

    errors = actual - predicted
    abs_errors = np.abs(errors)

    # MAE
    mae = float(np.mean(abs_errors))

    # RMSE
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # MAPE (avoid division by zero)
    non_zero_mask = actual != 0
    if non_zero_mask.any():
        mape = float(np.mean(abs_errors[non_zero_mask] / np.abs(actual[non_zero_mask])) * 100)
    else:
        mape = 0.0

    # SMAPE
    denominator = (np.abs(actual) + np.abs(predicted)) / 2
    non_zero_denom = denominator != 0
    if non_zero_denom.any():
        smape = float(np.mean(abs_errors[non_zero_denom] / denominator[non_zero_denom]) * 100)
    else:
        smape = 0.0

    # R²
    ss_res = np.sum(errors ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot != 0 else 0.0

    return {
        "mape": round(mape, 2),
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "r2": round(r2, 4),
        "smape": round(smape, 2),
    }
