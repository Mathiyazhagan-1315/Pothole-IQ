"""Severity analysis: OpenCV pipeline (always available) + optional Claude vision."""
import base64, json, re
import cv2, numpy as np, requests

def label_for(score):
    return "severe" if score >= 66 else "moderate" if score >= 38 else "minor"

def analyze_cv(image_bytes):
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not read image")
    h, w = img.shape[:2]
    s = 480 / max(h, w)
    if s < 1: img = cv2.resize(img, (int(w * s), int(h * s)))
    gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (7, 7), 0)
    local = cv2.GaussianBlur(gray, (0, 0), 25)
    dark = ((local.astype(int) - gray.astype(int)) > 28).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    area_ratio = float(dark.mean() / 255)
    cnts, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    biggest = max((cv2.contourArea(c) for c in cnts), default=0) / dark.size
    edge_density = float(cv2.Canny(gray, 50, 140).mean() / 255)
    score = max(5.0, min(100.0, 380 * biggest + 120 * area_ratio + 220 * edge_density))
    return dict(score=round(score, 1), label=label_for(score), method="opencv",
                detail=dict(hole_area_pct=round(biggest * 100, 1), dark_area_pct=round(area_ratio * 100, 1),
                            edge_density_pct=round(edge_density * 100, 1)))

def analyze_claude(image_bytes, api_key, model):
    b64 = base64.b64encode(image_bytes).decode()
    media = "image/png" if image_bytes[:4] == b"\x89PNG" else "image/jpeg"
    prompt = ('You assess road damage for a municipal repair team. Reply with ONLY JSON: '
              '{"is_pothole": bool, "score": 0-100, "reason": "one short sentence"}. '
              'Score 0-37 minor, 38-65 moderate, 66-100 severe (deep, wide, water-filled).')
    r = requests.post("https://api.anthropic.com/v1/messages", timeout=25,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": 200, "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
            {"type": "text", "text": prompt}]}]})
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json()["content"])
    data = json.loads(re.search(r"\{.*\}", text, re.S).group(0))
    score = float(data["score"])
    return dict(score=round(score, 1), label=label_for(score), method="claude-vision",
                detail=dict(is_pothole=bool(data.get("is_pothole", True)), reason=data.get("reason", "")))

def analyze(image_bytes, cfg):
    """Claude vision when a key is set (blended with OpenCV); always falls back to OpenCV."""
    cv_result = analyze_cv(image_bytes)
    if cfg.get("ANTHROPIC_API_KEY"):
        try:
            c = analyze_claude(image_bytes, cfg["ANTHROPIC_API_KEY"], cfg["CLAUDE_MODEL"])
            c["detail"]["opencv_score"] = cv_result["score"]
            c["score"] = round(0.7 * c["score"] + 0.3 * cv_result["score"], 1)
            c["label"] = label_for(c["score"]); c["method"] = "claude+opencv"
            return c
        except Exception as e:
            cv_result["detail"]["note"] = f"Claude unavailable ({type(e).__name__}); used OpenCV"
    return cv_result
