import { useState } from "react";
import { authApi } from "../api";

export default function Auth({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "", monthly_budget: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload =
        mode === "login"
          ? { email: form.email, password: form.password }
          : { ...form, monthly_budget: Number(form.monthly_budget) || 0 };
      const data = mode === "login" ? await authApi.login(payload) : await authApi.register(payload);
      localStorage.setItem("financeai_token", data.token);
      onAuthenticated(data.user);
    } catch (err) {
      setError(err?.response?.data?.error || "Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <div className="brand"><span className="dot" /> FinanceAI</div>
        <div className="auth-tabs">
          <div className={`nav-item ${mode === "login" ? "active" : ""}`} onClick={() => setMode("login")}>
            Log in
          </div>
          <div className={`nav-item ${mode === "register" ? "active" : ""}`} onClick={() => setMode("register")}>
            Sign up
          </div>
        </div>
        <form onSubmit={submit}>
          {mode === "register" && (
            <div className="form-row">
              <label>Full name</label>
              <input value={form.name} onChange={update("name")} required />
            </div>
          )}
          <div className="form-row">
            <label>Email</label>
            <input type="email" value={form.email} onChange={update("email")} required />
          </div>
          <div className="form-row">
            <label>Password</label>
            <input type="password" value={form.password} onChange={update("password")} required minLength={6} />
          </div>
          {mode === "register" && (
            <div className="form-row">
              <label>Monthly budget (optional)</label>
              <input type="number" value={form.monthly_budget} onChange={update("monthly_budget")} placeholder="e.g. 15000" />
            </div>
          )}
          {error && <div className="error-text">{error}</div>}
          <button type="submit" className="primary" style={{ width: "100%", marginTop: 8 }} disabled={loading}>
            {loading ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
        <p className="muted" style={{ marginTop: 14 }}>
          Demo login: demo@financeai.com / demo1234
        </p>
      </div>
    </div>
  );
}
