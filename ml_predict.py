"""
AI-based prediction layer.

Uses an IsolationForest to flag machines whose simulated behaviour
(utilization, downtime events, avg wait time) looks anomalous compared
to the rest of the line -- a simple stand-in for "predict which machine
is heading toward failure" until you plug in real historical sensor data.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def predict_risk(machine_results: list[dict]) -> list[dict]:
    """
    machine_results: list of dicts with keys:
        name, utilization_pct, downtime_events, total_downtime_seconds, avg_wait_time
    Returns the same list with an added 'risk_score' and 'risk_level'.
    """
    if len(machine_results) < 2:
        # IsolationForest needs multiple samples to be meaningful
        for m in machine_results:
            m["risk_score"] = 0.0
            m["risk_level"] = "insufficient_data"
        return machine_results

    df = pd.DataFrame(machine_results)
    features = df[["utilization_pct", "downtime_events", "total_downtime_seconds", "avg_wait_time"]].fillna(0)

    model = IsolationForest(n_estimators=100, contamination="auto", random_state=42)
    model.fit(features)

    # decision_function: lower (more negative) = more anomalous
    scores = model.decision_function(features)
    preds = model.predict(features)  # -1 = anomaly, 1 = normal

    for i, m in enumerate(machine_results):
        # Normalize score to a 0-100 "risk" number (invert so higher = riskier)
        risk = float(np.clip((0.5 - scores[i]) * 100, 0, 100))
        m["risk_score"] = round(risk, 1)
        m["risk_level"] = "high" if preds[i] == -1 else ("medium" if risk > 40 else "low")

    return machine_results
