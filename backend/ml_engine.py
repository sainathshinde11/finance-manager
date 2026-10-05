"""
ML engine for the finance manager.

1. TransactionCategorizer - TF-IDF + Multinomial Naive Bayes text classifier
   that auto-labels a transaction category from its free-text description.
2. detect_anomalies - flags transactions that are statistical outliers
   within their own category using a z-score on amount.
3. forecast_next_month - simple linear regression over monthly totals
   to project next month's spend.
"""

import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LinearRegression

# Seed training data: (description, category)
# In production this would be replaced/augmented by the user's own
# labeled transaction history (active learning loop).
SEED_TRAINING_DATA = [
    ("swiggy order dinner", "Food & Dining"),
    ("zomato lunch", "Food & Dining"),
    ("dominos pizza", "Food & Dining"),
    ("starbucks coffee", "Food & Dining"),
    ("restaurant bill dinner", "Food & Dining"),
    ("cafe coffee day", "Food & Dining"),
    ("big bazaar groceries", "Groceries"),
    ("dmart grocery shopping", "Groceries"),
    ("blinkit grocery order", "Groceries"),
    ("vegetable market", "Groceries"),
    ("supermarket monthly grocery", "Groceries"),
    ("uber ride", "Transport"),
    ("ola cab fare", "Transport"),
    ("petrol pump fuel", "Transport"),
    ("metro card recharge", "Transport"),
    ("bus ticket", "Transport"),
    ("train ticket irctc", "Transport"),
    ("electricity bill payment", "Utilities"),
    ("water bill", "Utilities"),
    ("mobile recharge jio", "Utilities"),
    ("wifi broadband bill", "Utilities"),
    ("gas cylinder booking", "Utilities"),
    ("house rent payment", "Rent"),
    ("flat rent monthly", "Rent"),
    ("amazon shopping order", "Shopping"),
    ("flipkart purchase", "Shopping"),
    ("myntra clothes order", "Shopping"),
    ("electronics store purchase", "Shopping"),
    ("netflix subscription", "Entertainment"),
    ("amazon prime video", "Entertainment"),
    ("movie tickets bookmyshow", "Entertainment"),
    ("spotify premium", "Entertainment"),
    ("gaming purchase steam", "Entertainment"),
    ("pharmacy medicine", "Healthcare"),
    ("hospital consultation fee", "Healthcare"),
    ("doctor appointment", "Healthcare"),
    ("health insurance premium", "Healthcare"),
    ("gym membership fee", "Healthcare"),
    ("course fee udemy", "Education"),
    ("college semester fee", "Education"),
    ("exam form fee", "Education"),
    ("books purchase", "Education"),
    ("coaching class fee", "Education"),
    ("mutual fund sip", "Investment"),
    ("stock market purchase zerodha", "Investment"),
    ("fixed deposit", "Investment"),
    ("recurring deposit", "Investment"),
    ("salary credited", "Salary/Income"),
    ("monthly salary", "Salary/Income"),
    ("freelance payment received", "Salary/Income"),
    ("stipend credited", "Salary/Income"),
    ("bonus credited", "Salary/Income"),
    ("miscellaneous expense", "Other"),
    ("atm cash withdrawal", "Other"),
    ("bank charges", "Other"),
]


def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class TransactionCategorizer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        self.model = MultinomialNB()
        self._fit()

    def _fit(self, extra_data=None):
        data = SEED_TRAINING_DATA + (extra_data or [])
        texts = [_clean(d) for d, _ in data]
        labels = [c for _, c in data]
        X = self.vectorizer.fit_transform(texts)
        self.model.fit(X, labels)

    def predict(self, description: str):
        """Returns (predicted_category, confidence)."""
        X = self.vectorizer.transform([_clean(description)])
        proba = self.model.predict_proba(X)[0]
        idx = int(np.argmax(proba))
        category = self.model.classes_[idx]
        confidence = float(proba[idx])
        return category, round(confidence, 3)

    def retrain_with_feedback(self, description: str, correct_category: str):
        """Online-learning-ish hook: append user correction and refit.
        Cheap for a seed-sized dataset; swap for partial_fit at scale."""
        SEED_TRAINING_DATA.append((description, correct_category))
        self._fit()


def detect_anomalies(transactions, z_threshold: float = 2.0):
    """
    transactions: list of dicts with 'category' and 'amount' (expenses negative).
    Returns a set of transaction indices flagged as anomalous within their category.
    """
    by_category = {}
    for i, t in enumerate(transactions):
        by_category.setdefault(t["category"], []).append((i, abs(t["amount"])))

    anomaly_indices = set()
    for cat, items in by_category.items():
        if len(items) < 4:
            continue  # not enough history to judge outliers
        amounts = np.array([a for _, a in items], dtype=float)
        mean, std = amounts.mean(), amounts.std()
        if std == 0:
            continue
        for (idx, amt) in items:
            z = (amt - mean) / std
            if z > z_threshold:
                anomaly_indices.add(idx)
    return anomaly_indices


def forecast_next_month(monthly_totals: list):
    """
    monthly_totals: list of floats, chronological total spend per month.
    Returns predicted next-month spend using linear regression over the trend.
    Falls back to the average if there isn't enough data for a trend line.
    """
    n = len(monthly_totals)
    if n == 0:
        return 0.0
    if n < 3:
        return round(float(np.mean(monthly_totals)), 2)

    X = np.arange(n).reshape(-1, 1)
    y = np.array(monthly_totals)
    reg = LinearRegression().fit(X, y)
    prediction = reg.predict([[n]])[0]
    return round(max(float(prediction), 0.0), 2)
