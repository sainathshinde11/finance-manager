from datetime import datetime, date, timedelta
from collections import defaultdict

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)

from models import db, User, Transaction, CATEGORIES
from ml_engine import TransactionCategorizer, detect_anomalies, forecast_next_month

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finance.db"
app.config["JWT_SECRET_KEY"] = "dev-secret-change-in-production"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)

CORS(app)
db.init_app(app)
jwt = JWTManager(app)

categorizer = TransactionCategorizer()

with app.app_context():
    db.create_all()


# ---------------------------------------------------------------- AUTH ----

@app.post("/api/auth/register")
def register():
    data = request.get_json(force=True)
    name, email, password = data.get("name"), data.get("email"), data.get("password")
    if not all([name, email, password]):
        return jsonify({"error": "name, email, and password are required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "an account with this email already exists"}), 409

    user = User(name=name, email=email, monthly_budget=data.get("monthly_budget", 0))
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@app.post("/api/auth/login")
def login():
    data = request.get_json(force=True)
    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not user.check_password(data.get("password", "")):
        return jsonify({"error": "invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@app.get("/api/auth/me")
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify(user.to_dict())


# ----------------------------------------------------------- CATEGORIES ---

@app.get("/api/categories")
def get_categories():
    return jsonify(CATEGORIES)


@app.post("/api/categorize-preview")
@jwt_required()
def categorize_preview():
    """Lets the frontend show an ML suggestion before the user commits it."""
    data = request.get_json(force=True)
    description = data.get("description", "")
    if not description.strip():
        return jsonify({"error": "description is required"}), 400
    category, confidence = categorizer.predict(description)
    return jsonify({"category": category, "confidence": confidence})


# --------------------------------------------------------- TRANSACTIONS ---

@app.get("/api/transactions")
@jwt_required()
def list_transactions():
    user_id = int(get_jwt_identity())
    q = Transaction.query.filter_by(user_id=user_id)

    category = request.args.get("category")
    if category:
        q = q.filter_by(category=category)

    start = request.args.get("start")
    end = request.args.get("end")
    if start:
        q = q.filter(Transaction.date >= datetime.fromisoformat(start).date())
    if end:
        q = q.filter(Transaction.date <= datetime.fromisoformat(end).date())

    txns = q.order_by(Transaction.date.desc()).all()
    return jsonify([t.to_dict() for t in txns])


@app.post("/api/transactions")
@jwt_required()
def create_transaction():
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True)

    description = data.get("description", "").strip()
    amount = data.get("amount")
    if not description or amount is None:
        return jsonify({"error": "description and amount are required"}), 400

    category = data.get("category")
    category_source = "manual"
    if not category:
        category, _ = categorizer.predict(description)
        category_source = "ml"

    txn_date = datetime.fromisoformat(data["date"]).date() if data.get("date") else date.today()

    txn = Transaction(
        user_id=user_id,
        description=description,
        amount=float(amount),
        category=category,
        category_source=category_source,
        date=txn_date,
    )
    db.session.add(txn)
    db.session.commit()

    _refresh_anomaly_flags(user_id)
    return jsonify(txn.to_dict()), 201


@app.put("/api/transactions/<int:txn_id>")
@jwt_required()
def update_transaction(txn_id):
    user_id = int(get_jwt_identity())
    txn = Transaction.query.filter_by(id=txn_id, user_id=user_id).first_or_404()
    data = request.get_json(force=True)

    old_description, old_category = txn.description, txn.category

    for field in ("description", "amount", "category"):
        if field in data:
            setattr(txn, field, data[field])
    if "date" in data:
        txn.date = datetime.fromisoformat(data["date"]).date()

    # If the user manually corrected an ML-assigned category, feed it back
    if data.get("category") and data["category"] != old_category and txn.category_source == "ml":
        categorizer.retrain_with_feedback(old_description, data["category"])
        txn.category_source = "manual"

    db.session.commit()
    _refresh_anomaly_flags(user_id)
    return jsonify(txn.to_dict())


@app.delete("/api/transactions/<int:txn_id>")
@jwt_required()
def delete_transaction(txn_id):
    user_id = int(get_jwt_identity())
    txn = Transaction.query.filter_by(id=txn_id, user_id=user_id).first_or_404()
    db.session.delete(txn)
    db.session.commit()
    return jsonify({"deleted": txn_id})


def _refresh_anomaly_flags(user_id):
    txns = Transaction.query.filter_by(user_id=user_id).filter(Transaction.amount < 0).all()
    payload = [{"category": t.category, "amount": t.amount} for t in txns]
    anomaly_idx = detect_anomalies(payload)
    for i, t in enumerate(txns):
        t.is_anomaly = i in anomaly_idx
    db.session.commit()


# ------------------------------------------------------------- ANALYTICS --

@app.get("/api/analytics/summary")
@jwt_required()
def analytics_summary():
    user_id = int(get_jwt_identity())
    txns = Transaction.query.filter_by(user_id=user_id).all()

    total_income = sum(t.amount for t in txns if t.amount > 0)
    total_expense = sum(-t.amount for t in txns if t.amount < 0)

    by_category = defaultdict(float)
    for t in txns:
        if t.amount < 0:
            by_category[t.category] += -t.amount

    anomalies = [t.to_dict() for t in txns if t.is_anomaly]

    return jsonify({
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(total_income - total_expense, 2),
        "spend_by_category": {k: round(v, 2) for k, v in by_category.items()},
        "anomalies": anomalies,
        "transaction_count": len(txns),
    })


@app.get("/api/analytics/forecast")
@jwt_required()
def analytics_forecast():
    user_id = int(get_jwt_identity())
    txns = Transaction.query.filter_by(user_id=user_id, ).filter(Transaction.amount < 0).all()

    monthly = defaultdict(float)
    for t in txns:
        key = f"{t.date.year}-{t.date.month:02d}"
        monthly[key] += -t.amount

    ordered_keys = sorted(monthly.keys())
    totals = [round(monthly[k], 2) for k in ordered_keys]
    prediction = forecast_next_month(totals)

    user = User.query.get(user_id)
    over_budget_risk = bool(user.monthly_budget) and prediction > user.monthly_budget

    return jsonify({
        "history": [{"month": k, "total": monthly[k]} for k in ordered_keys],
        "predicted_next_month": prediction,
        "monthly_budget": user.monthly_budget,
        "over_budget_risk": over_budget_risk,
    })


@app.put("/api/budget")
@jwt_required()
def set_budget():
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True)
    user = User.query.get(user_id)
    user.monthly_budget = float(data.get("monthly_budget", 0))
    db.session.commit()
    return jsonify(user.to_dict())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
