import io, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import cv2, numpy as np, pytest
from app import create_app
from services import scoring, severity
from services.geo import haversine_m

def img(hole=True):
    a = np.full((300, 400, 3), 140, np.uint8); a += np.random.RandomState(1).randint(0, 12, a.shape, dtype=np.uint8)
    if hole: cv2.ellipse(a, (200, 150), (90, 60), 0, 0, 360, (25, 25, 25), -1)
    return cv2.imencode(".jpg", a)[1].tobytes()

@pytest.fixture
def client(tmp_path):
    app = create_app(dict(SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path/'t.db'}", UPLOAD_DIR=str(tmp_path), RAIN_DEMO=True, TESTING=True))
    return app.test_client()

def test_haversine(): assert 100 < haversine_m(11.41, 77.69, 11.411, 77.69) < 120
def test_severity_orders_images():
    assert severity.analyze_cv(img(True))["score"] > severity.analyze_cv(img(False))["score"] + 15
def test_more_rain_more_risk(): assert scoring.risk_score(60, 2, 5, "open", 90) > scoring.risk_score(60, 2, 5, "open", 5)
def test_fixed_zero(): assert scoring.risk_score(90, 9, 20, "fixed", 90) == 0
def test_priority_levels():
    assert scoring.priority(95, 8, 90, 20, "open")["level"] == "fix_now"
    assert scoring.priority(10, 1, 5, 0, "open")["level"] == "monitor"

def post(c, lat, lng, hole=True):
    return c.post("/api/reports", data=dict(lat=lat, lng=lng, road_name="Test Rd", photo=(io.BytesIO(img(hole)), "p.jpg")), content_type="multipart/form-data")

def test_create_and_merge(client):
    r = post(client, 11.41, 77.69); assert r.status_code == 201 and r.json["report"]["severity_label"] in ("moderate", "severe")
    r2 = post(client, 11.41001, 77.69001); assert r2.status_code == 200 and r2.json["merged"] and r2.json["report"]["report_count"] == 2
def test_validation(client):
    assert client.post("/api/reports", data={}).status_code == 400
    bad = client.post("/api/reports", data=dict(lat=1, lng=1, photo=(io.BytesIO(b"x"), "a.exe")), content_type="multipart/form-data")
    assert bad.status_code == 400
def test_queue_sorted_and_rain_simulator(client):
    post(client, 11.41, 77.69); post(client, 11.45, 77.72, hole=False)
    q = client.get("/api/queue").json; assert [i["rank"] for i in q] == [1, 2]
    assert q[0]["priority"]["score"] >= q[1]["priority"]["score"]
    assert client.get("/api/queue?rain=120").json[0]["risk"] > client.get("/api/queue?rain=0").json[0]["risk"]
def test_authority_flow(client):
    rid = post(client, 11.41, 77.69).json["report"]["id"]
    assert client.patch(f"/api/reports/{rid}", json={"status": "fixed"}).status_code == 401
    assert client.post("/api/authority/check", json={"pin": "bad"}).status_code == 401
    ok = client.patch(f"/api/reports/{rid}", json={"status": "fixed"}, headers={"X-Authority-Pin": "2026"})
    assert ok.status_code == 200 and ok.json["status"] == "fixed"
    assert client.get("/api/stats").json["fixed"] == 1
def test_csv_and_pages(client):
    post(client, 11.41, 77.69)
    assert client.get("/api/export.csv").data.startswith(b"rank,id")

def test_pages_render(client):
    for p in ("/", "/report", "/dashboard", "/how-it-works"):
        assert client.get(p).status_code == 200
    for f in ("css/app.css", "js/common.js", "js/map.js", "js/report.js", "js/dashboard.js"):
        assert client.get("/static/" + f).status_code == 200
