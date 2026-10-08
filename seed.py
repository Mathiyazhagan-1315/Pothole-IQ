"""Seed realistic demo data around Erode. Run: python seed.py"""
import random
from datetime import datetime, timedelta
from app import create_app
from models import db, Report
ROADS = ["Perundurai Rd", "Brough Rd", "Gandhiji Rd", "EVN Rd", "Sathy Rd", "Bhavani Rd", "Mettur Rd", "Chennimalai Rd", "Kollampalayam Rd", "Nasiyanur Rd"]
def seed(app, n=28):
    random.seed(7)
    with app.app_context():
        db.drop_all(); db.create_all()
        for i in range(n):
            score = random.choice([14, 22, 31, 45, 52, 61, 72, 81, 90])
            created = datetime.utcnow() - timedelta(days=random.randint(0, 25))
            db.session.add(Report(lat=11.4102 + random.uniform(-.035, .035), lng=77.6980 + random.uniform(-.045, .045),
                road_name=random.choice(ROADS), description=random.choice(["Water-filled hole near junction", "Edge of road breaking up", "Deep crater, two-wheelers swerving", "Shallow dent after rain", "Cracks spreading across lane"]),
                severity_score=score, severity_label="severe" if score >= 66 else "moderate" if score >= 38 else "minor",
                severity_method="seed", report_count=random.choice([1, 1, 1, 2, 3, 5, 8]), created_at=created, updated_at=created,
                status=random.choices(["open", "in_progress", "fixed"], [8, 1, 1])[0]))
        db.session.commit()
if __name__ == "__main__":
    seed(create_app()); print("Seeded demo data.")
