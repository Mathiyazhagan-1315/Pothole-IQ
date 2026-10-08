from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(500), default="")
    road_name = db.Column(db.String(120), default="")
    photo = db.Column(db.String(200))
    severity_label = db.Column(db.String(20), default="minor")   # minor|moderate|severe
    severity_score = db.Column(db.Float, default=20.0)           # 0-100
    severity_method = db.Column(db.String(30), default="manual")
    report_count = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default="open")            # open|in_progress|fixed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return dict(id=self.id, lat=self.lat, lng=self.lng, description=self.description,
                    road_name=self.road_name, photo=f"/uploads/{self.photo}" if self.photo else None,
                    severity_label=self.severity_label, severity_score=round(self.severity_score, 1),
                    severity_method=self.severity_method, report_count=self.report_count,
                    status=self.status, created_at=self.created_at.isoformat(),
                    age_days=max(0, (datetime.utcnow() - self.created_at).days))
