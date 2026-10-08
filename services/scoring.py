"""Transparent risk + priority scoring. Every component is returned so the ranking is explainable."""
import math

def rain_factor(mm):
    return 1 - math.exp(-mm / 55.0)

def risk_score(severity, report_count, age_days, status, mm):
    """Predicted likelihood (0-100) that the spot worsens in the next days of rain."""
    if status == "fixed":
        return 0.0
    vulnerability = 0.35 + 0.65 * (severity / 100.0)
    recurrence = min(1.0, math.log1p(report_count) / math.log(8))
    neglect = min(1.0, age_days / 30.0)
    base = 0.55 * rain_factor(mm) * vulnerability + 0.25 * recurrence + 0.10 * neglect + 0.10 * (severity / 100)
    return round(min(100.0, base * 120), 1)

def priority(severity, report_count, risk, age_days, status):
    if status == "fixed":
        return dict(score=0.0, level="fixed", parts=dict(severity=0, reports=0, risk=0, age=0))
    reports = min(100.0, 100 * math.log1p(report_count) / math.log(10))
    age = min(100.0, age_days * 3.3)
    parts = dict(severity=round(0.40 * severity, 1), reports=round(0.15 * reports, 1),
                 risk=round(0.35 * risk, 1), age=round(0.10 * age, 1))
    score = round(sum(parts.values()), 1)
    return dict(score=score, level="fix_now" if score >= 55 else "soon" if score >= 35 else "monitor", parts=parts)

def explain(item):
    p = item["priority"]["parts"]; top = max(p, key=p.get)
    why = {"severity": "a deep or wide defect", "reports": "repeated citizen reports",
           "risk": "high predicted rain damage", "age": "how long it has been open"}[top]
    return f"Ranked mainly because of {why}."
