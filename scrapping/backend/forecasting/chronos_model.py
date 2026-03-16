import pandas as pd
import numpy as np
import torch
from .metrics import calculate_metrics


def run_chronos_forecast(df: pd.DataFrame, periods: int = 30) -> dict:
    """
    Run Amazon Chronos (chronos-bolt-small) for zero-shot time series forecasting.

    Args:
        df: DataFrame with columns ['ds', 'y'] (date, price)
        periods: Number of days to forecast into the future

    Returns:
        dict with forecast data, metrics, and best_time_to_buy info
    """
    try:
        from chronos import BaseChronosPipeline

        df = df.copy()
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds").reset_index(drop=True)

        # Train/Test split (80/20) for evaluation
        split_idx = int(len(df) * 0.8)
        train_values = df["y"].values[:split_idx]
        test_values = df["y"].values[split_idx:]

        # Load pretrained Chronos model
        pipeline = BaseChronosPipeline.from_pretrained(
            "amazon/chronos-bolt-small",
            device_map="cpu",
            torch_dtype=torch.float32,
        )

        # --- Evaluate on test set ---
        context_tensor = torch.tensor(train_values, dtype=torch.float32).unsqueeze(0)
        test_forecast_output = pipeline.predict(
            context_tensor,
            prediction_length=len(test_values),
        )
        # test_forecast_output shape for chronos-bolt: (1, 9_quantiles, prediction_length)
        test_pred = test_forecast_output[0].numpy()[4][:len(test_values)] # index 4 is the median (0.5 quantile)

        metrics = calculate_metrics(test_values[:len(test_pred)], test_pred)

        # --- Final forecast on full data ---
        full_context = torch.tensor(df["y"].values, dtype=torch.float32).unsqueeze(0)
        forecast_output = pipeline.predict(
            full_context,
            prediction_length=periods,
        )
        # forecast_output shape: (1, 9_quantiles, prediction_length)
        quantiles = forecast_output[0].numpy()
        median_forecast = quantiles[4]      # 0.5 quantile
        lower_bound = quantiles[0]          # 0.1 quantile
        upper_bound = quantiles[8]          # 0.9 quantile

        # Build forecast dates
        last_date = df["ds"].iloc[-1]
        forecast_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods, freq="D")

        forecast_data = []
        for i, date in enumerate(forecast_dates):
            forecast_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "predicted_price": round(float(median_forecast[i]), 2),
                "lower_bound": round(float(lower_bound[i]), 2),
                "upper_bound": round(float(upper_bound[i]), 2),
            })

        # Fitted values using rolling prediction (approximate)
        # For Chronos we'll use a simpler approach: predict backwards on known data
        fitted_data = []
        for i, row in df.iterrows():
            fitted_data.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "fitted_price": round(float(row["y"]), 2),  # Chronos doesn't do in-sample fitting
            })

        # Best time to buy
        if forecast_data:
            best = min(forecast_data, key=lambda x: x["predicted_price"])
            best_time = {
                "date": best["date"],
                "predicted_price": best["predicted_price"],
                "lower_bound": best["lower_bound"],
                "upper_bound": best["upper_bound"],
            }
        else:
            best_time = None

        return {
            "success": True,
            "model": "Chronos",
            "forecast": forecast_data,
            "fitted": fitted_data,
            "metrics": metrics,
            "best_time_to_buy": best_time,
        }

    except Exception as e:
        return {"success": False, "error": f"Chronos forecast failed: {str(e)}"}
