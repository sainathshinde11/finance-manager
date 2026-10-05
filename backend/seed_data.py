"""Run `python seed_data.py` after starting the app once (so finance.db exists)
to create a demo user with a few months of sample transactions."""

import random
from datetime import date, timedelta
from app import app
from models import db, User, Transaction

DEMO_EMAIL = "demo@financeai.com"
DEMO_PASSWORD = "demo1234"

SAMPLE_EXPENSES = [
    ("swiggy order dinner", -350, "Food & Dining"),
    ("dmart grocery shopping", -1800, "Groceries"),
    ("uber ride", -220, "Transport"),
    ("electricity bill payment", -1400, "Utilities"),
    ("house rent payment", -9000, "Rent"),
    ("amazon shopping order", -1200, "Shopping"),
    ("netflix subscription", -499, "Entertainment"),
    ("pharmacy medicine", -300, "Healthcare"),
    ("course fee udemy", -799, "Education"),
    ("mutual fund sip", -3000, "Investment"),
]

with app.app_context():
    db.create_all()
    if User.query.filter_by(email=DEMO_EMAIL).first():
        print("Demo user already exists.")
    else:
        user = User(name="Demo User", email=DEMO_EMAIL, monthly_budget=15000)
        user.set_password(DEMO_PASSWORD)
        db.session.add(user)
        db.session.commit()

        today = date.today()
        for month_offset in range(4, -1, -1):
            month_date = today - timedelta(days=30 * month_offset)
            db.session.add(Transaction(
                user_id=user.id, description="salary credited", amount=25000,
                category="Salary/Income", category_source="ml", date=month_date.replace(day=1)
            ))
            for desc, amt, cat in SAMPLE_EXPENSES:
                jitter = random.uniform(0.8, 1.3)
                txn_date = month_date.replace(day=min(28, random.randint(1, 28)))
                db.session.add(Transaction(
                    user_id=user.id, description=desc, amount=round(amt * jitter, 2),
                    category=cat, category_source="ml", date=txn_date
                ))
        db.session.commit()
        print(f"Seeded demo user: {DEMO_EMAIL} / {DEMO_PASSWORD}")
