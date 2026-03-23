import pandas as pd
import numpy as np
from prophet import Prophet
from .metrics import calculate_metrics


def run_prophet_forecast(df: pd.DataFrame, periods: int = 30) -> dict:
    """
    Run Facebook Prophet on price history data.

    Args:
        df: DataFrame with columns ['ds', 'y'] (date, price)
        periods: Number of days to forecast into the future

    Returns:
        dict with forecast data, metrics, and best_time_to_buy info
    """
    try:
        df = df.copy()
        df["ds"] = pd.to_datetime(df["ds"])
        df = df.sort_values("ds").reset_index(drop=True)

        # Train/Test split (80/20) for evaluation
        split_idx = int(len(df) * 0.8)
        train_df = df.iloc[:split_idx].copy()
        test_df = df.iloc[split_idx:].copy()

        # Fit Prophet
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_mode="multiplicative",
        )
        model.fit(train_df)

        # Predict on test set for metrics
        test_forecast = model.predict(test_df[['ds']])

        # Align test predictions
        test_pred = test_forecast["yhat"].values
        test_actual = test_df["y"].values

        metrics = calculate_metrics(test_actual, test_pred)

        # Refit on full data for final forecast
        full_model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05,
            seasonality_mode="multiplicative",
        )
        full_model.fit(df)

        future = full_model.make_future_dataframe(periods=periods, freq="D")
        forecast = full_model.predict(future)

        # Extract forecast portion (future only)
        future_forecast = forecast.iloc[len(df):]

        forecast_data = []
        for _, row in future_forecast.iterrows():
            forecast_data.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "predicted_price": round(float(row["yhat"]), 2),
                "lower_bound": round(float(row["yhat_lower"]), 2),
                "upper_bound": round(float(row["yhat_upper"]), 2),
            })

        # Also include fitted values for the historical period
        historical_fitted = forecast.iloc[:len(df)]
        fitted_data = []
        for _, row in historical_fitted.iterrows():
            fitted_data.append({
                "date": row["ds"].strftime("%Y-%m-%d"),
                "fitted_price": round(float(row["yhat"]), 2),
            })

        # Best time to buy: find the date with the lowest predicted price
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
            "model": "Prophet",
            "forecast": forecast_data,
            "fitted": fitted_data,
            "metrics": metrics,
            "best_time_to_buy": best_time,
        }

    except Exception as e:
        return {"success": False, "error": f"Prophet forecast failed: {str(e)}"}
