import os, csv, io, uuid
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory, Response
from config import Config
from models import db, Report
from services.geo import haversine_m
from services import severity as sev, rainfall as rain, scoring

def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides: app.config.update(overrides)
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    def is_authority():
        return request.headers.get("X-Authority-Pin", "") == app.config["AUTHORITY_PIN"]

    def enrich(reports, override_mm=None):
        out, cache = [], {}
        for r in reports:
            d = r.to_dict()
            k = (round(r.lat, 1), round(r.lng, 1))
            if k not in cache:
                cache[k] = rain.get_rainfall(r.lat, r.lng, app.config)
            mm = rain.effective_mm(cache[k], override_mm)
            risk = scoring.risk_score(r.severity_score, r.report_count, d["age_days"], r.status, mm)
            d["risk"] = risk
            d["priority"] = scoring.priority(r.severity_score, r.report_count, risk, d["age_days"], r.status)
            d["why"] = scoring.explain(d)
            out.append(d)
        return out

    def mm_arg():
        v = request.args.get("rain")
        try: return float(v) if v not in (None, "") else None
        except ValueError: return None

    def read_photo():
        f = request.files.get("photo")
        if not f or not f.filename: return None, None
        ext = f.filename.rsplit(".", 1)[-1].lower()
        if ext not in app.config["ALLOWED_EXT"]: raise ValueError("Please upload a JPG, PNG or WEBP photo.")
        return f.read(), ext

    # ---------- pages ----------
    @app.get("/")
    def page_map(): return render_template("map.html", center=app.config["DEFAULT_CENTER"])
    @app.get("/report")
    def page_report(): return render_template("report.html", center=app.config["DEFAULT_CENTER"])
    @app.get("/dashboard")
    def page_dash(): return render_template("dashboard.html")
    @app.get("/how-it-works")
    def page_how(): return render_template("how.html")
    @app.get("/uploads/<path:name>")
    def uploads(name): return send_from_directory(app.config["UPLOAD_DIR"], name)

    # ---------- API ----------
    @app.post("/api/analyze")
    def api_analyze():
        try:
            data, _ = read_photo()
            if not data: return jsonify(error="Please choose a photo."), 400
            return jsonify(sev.analyze(data, app.config))
        except ValueError as e:
            return jsonify(error=str(e)), 400

    @app.post("/api/reports")
    def api_create():
        try:
            lat, lng = float(request.form["lat"]), float(request.form["lng"])
        except (KeyError, ValueError):
            return jsonify(error="Please pin the pothole location on the map."), 400
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            return jsonify(error="Invalid coordinates."), 400
        try:
            data, ext = read_photo()
        except ValueError as e:
            return jsonify(error=str(e)), 400
        desc = request.form.get("description", "").strip()[:500]
        road = request.form.get("road_name", "").strip()[:120]
        result = None
        if data:
            try: result = sev.analyze(data, app.config)
            except ValueError as e: return jsonify(error=str(e)), 400
        # duplicate merge: same open spot within radius -> bump count, keep worst severity
        for r in Report.query.filter(Report.status != "fixed").all():
            if haversine_m(lat, lng, r.lat, r.lng) <= app.config["DUPLICATE_RADIUS_M"]:
                r.report_count += 1; r.updated_at = datetime.utcnow()
                if result and result["score"] > r.severity_score:
                    r.severity_score, r.severity_label, r.severity_method = result["score"], result["label"], result["method"]
                db.session.commit()
                return jsonify(merged=True, report=enrich([r])[0]), 200
        photo_name = None
        if data:
            photo_name = f"{uuid.uuid4().hex}.{ext}"
            with open(os.path.join(app.config["UPLOAD_DIR"], photo_name), "wb") as fh: fh.write(data)
        score = result["score"] if result else float(request.form.get("severity_score", 30))
        r = Report(lat=lat, lng=lng, description=desc, road_name=road, photo=photo_name,
                   severity_score=score, severity_label=sev.label_for(score),
                   severity_method=result["method"] if result else "manual")
        db.session.add(r); db.session.commit()
        return jsonify(merged=False, report=enrich([r])[0], analysis=result), 201

    @app.get("/api/reports")
    def api_list():
        q = Report.query.order_by(Report.created_at.desc())
        status = request.args.get("status")
        if status: q = q.filter_by(status=status)
        return jsonify(enrich(q.all(), mm_arg()))

    @app.get("/api/queue")
    def api_queue():
        items = [i for i in enrich(Report.query.filter(Report.status != "fixed").all(), mm_arg())]
        items.sort(key=lambda i: i["priority"]["score"], reverse=True)
        for n, i in enumerate(items, 1): i["rank"] = n
        return jsonify(items)

    @app.get("/api/stats")
    def api_stats():
        items = enrich(Report.query.all(), mm_arg())
        open_ = [i for i in items if i["status"] != "fixed"]
        return jsonify(total=len(items), open=len(open_),
                       fixed=len(items) - len(open_),
                       fix_now=sum(i["priority"]["level"] == "fix_now" for i in open_),
                       severe=sum(i["severity_label"] == "severe" for i in open_),
                       duplicates_merged=sum(i["report_count"] - 1 for i in items),
                       avg_risk=round(sum(i["risk"] for i in open_) / len(open_), 1) if open_ else 0,
                       by_severity={k: sum(i["severity_label"] == k for i in open_) for k in ("minor", "moderate", "severe")},
                       by_status={k: sum(i["status"] == k for i in items) for k in ("open", "in_progress", "fixed")})

    @app.get("/api/rain")
    def api_rain():
        lat = float(request.args.get("lat", app.config["DEFAULT_CENTER"][0]))
        lng = float(request.args.get("lng", app.config["DEFAULT_CENTER"][1]))
        r = rain.get_rainfall(lat, lng, app.config)
        return jsonify(**r, effective_mm=round(rain.effective_mm(r), 1))

    @app.post("/api/authority/check")
    def api_pin():
        ok = (request.get_json(silent=True) or {}).get("pin", "") == app.config["AUTHORITY_PIN"]
        return (jsonify(ok=True), 200) if ok else (jsonify(ok=False, error="Wrong PIN"), 401)

    @app.patch("/api/reports/<int:rid>")
    def api_update(rid):
        if not is_authority(): return jsonify(error="Authority PIN required"), 401
        r = db.session.get(Report, rid)
        if not r: return jsonify(error="Not found"), 404
        status = (request.get_json(silent=True) or {}).get("status")
        if status not in ("open", "in_progress", "fixed"): return jsonify(error="Invalid status"), 400
        r.status, r.updated_at = status, datetime.utcnow(); db.session.commit()
        return jsonify(enrich([r])[0])

    @app.get("/api/export.csv")
    def api_export():
        items = enrich(Report.query.filter(Report.status != "fixed").all(), mm_arg())
        items.sort(key=lambda i: i["priority"]["score"], reverse=True)
        buf = io.StringIO(); w = csv.writer(buf)
        w.writerow(["rank", "id", "road", "lat", "lng", "severity", "severity_score", "reports", "risk", "priority", "level", "status", "why"])
        for n, i in enumerate(items, 1):
            w.writerow([n, i["id"], i["road_name"], i["lat"], i["lng"], i["severity_label"], i["severity_score"],
                        i["report_count"], i["risk"], i["priority"]["score"], i["priority"]["level"], i["status"], i["why"]])
        return Response(buf.getvalue(), mimetype="text/csv",
                        headers={"Content-Disposition": "attachment; filename=potholeiq_repair_queue.csv"})
    if os.getenv("SEED_DEMO") == "1":
        with app.app_context():
            if Report.query.count() == 0:
                from seed import seed
                seed(app)
    return app

if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
