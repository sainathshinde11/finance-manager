import { useEffect, useState, useCallback } from "react";
import Auth from "./components/Auth";
import Dashboard from "./components/Dashboard";
import TransactionList from "./components/TransactionList";
import AddTransaction from "./components/AddTransaction";
import { authApi, txnApi, analyticsApi, categoriesApi, budgetApi } from "./api";

export default function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [view, setView] = useState("dashboard");
  const [categories, setCategories] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [budgetInput, setBudgetInput] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("financeai_token");
    if (!token) { setCheckingAuth(false); return; }
    authApi.me().then((u) => setUser(u)).catch(() => localStorage.removeItem("financeai_token"))
      .finally(() => setCheckingAuth(false));
  }, []);

  const refreshAll = useCallback(async () => {
    const [txns, summ, fc, cats] = await Promise.all([
      txnApi.list(), analyticsApi.summary(), analyticsApi.forecast(), categoriesApi.list(),
    ]);
    setTransactions(txns);
    setSummary(summ);
    setForecast(fc);
    setCategories(cats);
  }, []);

  useEffect(() => {
    if (user) refreshAll();
  }, [user, refreshAll]);

  useEffect(() => {
    if (user) setBudgetInput(user.monthly_budget || "");
  }, [user]);

  const logout = () => {
    localStorage.removeItem("financeai_token");
    setUser(null);
  };

  const saveBudget = async () => {
    const updated = await budgetApi.set(Number(budgetInput) || 0);
    setUser(updated);
    refreshAll();
  };

  if (checkingAuth) return null;
  if (!user) return <Auth onAuthenticated={setUser} />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="dot" /> FinanceAI</div>
        <div className={`nav-item ${view === "dashboard" ? "active" : ""}`} onClick={() => setView("dashboard")}>Dashboard</div>
        <div className={`nav-item ${view === "transactions" ? "active" : ""}`} onClick={() => setView("transactions")}>Transactions</div>
        <div className={`nav-item ${view === "budget" ? "active" : ""}`} onClick={() => setView("budget")}>Budget</div>
        <div style={{ flex: 1 }} />
        <div className="muted" style={{ padding: "0 12px", marginBottom: 8 }}>{user.name}</div>
        <div className="nav-item" onClick={logout}>Log out</div>
      </aside>

      <main className="main">
        <div className="top-row">
          <h2>
            {view === "dashboard" && "Overview"}
            {view === "transactions" && "Transactions"}
            {view === "budget" && "Budget settings"}
          </h2>
        </div>

        {view === "dashboard" && <Dashboard summary={summary} forecast={forecast} />}

        {view === "transactions" && (
          <div className="grid grid-2">
            <TransactionList transactions={transactions} onChanged={refreshAll} />
            <AddTransaction categories={categories} onCreated={refreshAll} />
          </div>
        )}

        {view === "budget" && (
          <div className="card" style={{ maxWidth: 400 }}>
            <div className="form-row">
              <label>Monthly budget (₹)</label>
              <input type="number" value={budgetInput} onChange={(e) => setBudgetInput(e.target.value)} />
            </div>
            <button className="primary" onClick={saveBudget}>Save budget</button>
          </div>
        )}
      </main>
    </div>
  );
}
