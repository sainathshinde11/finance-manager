from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

CATEGORIES = [
    "Food & Dining", "Groceries", "Transport", "Utilities", "Rent",
    "Shopping", "Entertainment", "Healthcare", "Education",
    "Investment", "Salary/Income", "Other"
]


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    monthly_budget = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship(
        "Transaction", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "monthly_budget": self.monthly_budget,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # negative = expense, positive = income
    category = db.Column(db.String(80), nullable=False)
    category_source = db.Column(db.String(20), default="manual")  # manual | ml
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    is_anomaly = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "category_source": self.category_source,
            "date": self.date.isoformat(),
            "is_anomaly": self.is_anomaly,
        }
