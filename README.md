# FinanceAI — AI-Powered Personal Finance Manager

A full-stack personal finance tracker that uses machine learning to
auto-categorize transactions, flag unusual spending, and forecast next
month's expenses.

## Features

- **JWT authentication** — register/login, per-user data isolation
- **ML auto-categorization** — TF-IDF + Multinomial Naive Bayes classifier
  labels each transaction (e.g. "swiggy order dinner" → *Food & Dining*)
  from its free-text description, with a live confidence score shown in the UI
- **Online feedback loop** — correcting an ML-assigned category retrains
  the classifier with that correction
- **Anomaly detection** — flags transactions that are statistical outliers
  (z-score) within their own category, e.g. an unusually large grocery bill
- **Spend forecasting** — linear regression over monthly totals projects
  next month's spend and flags budget-risk
- **Interactive dashboard** — income/expense/savings summary, category
  breakdown (pie chart), spend trend + forecast (line chart)

## Tech stack

| Layer      | Tech |
|------------|------|
| Frontend   | React (Vite), Recharts, Axios |
| Backend    | Flask, Flask-JWT-Extended, Flask-SQLAlchemy, Flask-CORS |
| ML         | scikit-learn (TfidfVectorizer, MultinomialNB, LinearRegression), NumPy |
| Database   | SQLite (swap the SQLAlchemy URI for Postgres/MySQL in production) |

## Project structure

```
finance-manager/
├── backend/
│   ├── app.py            # Flask app + REST API routes
│   ├── models.py          # SQLAlchemy models (User, Transaction)
│   ├── ml_engine.py        # categorizer, anomaly detection, forecasting
│   ├── seed_data.py        # creates a demo account with sample history
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── api.js
    │   └── components/
    │       ├── Auth.jsx
    │       ├── Dashboard.jsx
    │       ├── TransactionList.jsx
    │       └── AddTransaction.jsx
    └── package.json
```

## Running locally

### 1. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py                   # runs on http://localhost:5000
```

Optional — seed a demo account (`demo@financeai.com` / `demo1234`) with
5 months of sample transactions:

```bash
python seed_data.py
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev                     # runs on http://localhost:5173
```

The Vite dev server proxies `/api` requests to the Flask backend, so just
open http://localhost:5173.

## API overview

| Method | Route                        | Purpose |
|--------|-------------------------------|---------|
| POST   | `/api/auth/register`          | Create account |
| POST   | `/api/auth/login`              | Log in, get JWT |
| GET    | `/api/transactions`            | List transactions (filter by category/date) |
| POST   | `/api/transactions`             | Create transaction (auto-categorized if no category given) |
| PUT    | `/api/transactions/<id>`        | Edit transaction (correcting category retrains the model) |
| DELETE | `/api/transactions/<id>`        | Delete transaction |
| POST   | `/api/categorize-preview`       | Live ML category suggestion for a description |
| GET    | `/api/analytics/summary`        | Income/expense totals, category breakdown, anomalies |
| GET    | `/api/analytics/forecast`       | Monthly history + next-month prediction |
| PUT    | `/api/budget`                   | Set monthly budget |

## Notes on the ML design

- The categorizer ships with a ~55-row seed training set covering 12
  common spending categories. In a production version this would be
  bootstrapped further from the user's transaction history, and
  `MultinomialNB.partial_fit` would replace the current refit-on-correction
  approach for scale.
- Anomaly detection is intentionally simple and explainable (per-category
  z-score) rather than a black-box model — appropriate for a personal
  finance tool where the user needs to trust *why* something was flagged.
- Forecasting falls back to a plain average when there's under 3 months
  of history, since a regression line on 1–2 points is not meaningful.

## Possible extensions

- Bank statement import (CSV/PDF parsing) with the ML categorizer applied in bulk
- Email/push alerts when a transaction is flagged as anomalous
- Multi-currency support
- Recurring transaction detection (subscriptions)
