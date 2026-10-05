import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, CartesianGrid, Legend
} from "recharts";

const COLORS = ["#00d9a3", "#5eead4", "#38bdf8", "#818cf8", "#f472b6", "#fb923c", "#facc15", "#a3e635", "#f87171", "#c084fc", "#94a3b8", "#4ade80"];

export default function Dashboard({ summary, forecast }) {
  if (!summary || !forecast) return <div className="card">Loading dashboard…</div>;

  const pieData = Object.entries(summary.spend_by_category).map(([name, value]) => ({ name, value }));
  const lineData = forecast.history.map((h) => ({ month: h.month, spend: h.total }));
  if (forecast.predicted_next_month) {
    lineData.push({ month: "Next (predicted)", spend: forecast.predicted_next_month, predicted: true });
  }

  return (
    <div>
      <div className="grid grid-3" style={{ marginBottom: 18 }}>
        <div className="card">
          <div className="stat-label">Total income</div>
          <div className="stat-value positive">₹{summary.total_income.toLocaleString("en-IN")}</div>
        </div>
        <div className="card">
          <div className="stat-label">Total expenses</div>
          <div className="stat-value negative">₹{summary.total_expense.toLocaleString("en-IN")}</div>
        </div>
        <div className="card">
          <div className="stat-label">Net savings</div>
          <div className={`stat-value ${summary.net_savings >= 0 ? "positive" : "negative"}`}>
            ₹{summary.net_savings.toLocaleString("en-IN")}
          </div>
        </div>
      </div>

      <div className="grid grid-2" style={{ marginBottom: 18 }}>
        <div className="card">
          <h3 className="section-title">Spend by category</h3>
          {pieData.length === 0 ? (
            <p className="muted">No expenses logged yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95} paddingAngle={2}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#141c2e", border: "1px solid #253048", borderRadius: 8 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h3 className="section-title">Spend trend &amp; ML forecast</h3>
          {lineData.length < 2 ? (
            <p className="muted">Add a few months of data to see a trend.</p>
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={lineData}>
                <CartesianGrid stroke="#253048" strokeDasharray="3 3" />
                <XAxis dataKey="month" stroke="#8a94a6" fontSize={11} />
                <YAxis stroke="#8a94a6" fontSize={11} />
                <Tooltip contentStyle={{ background: "#141c2e", border: "1px solid #253048", borderRadius: 8 }} />
                <Line type="monotone" dataKey="spend" stroke="#00d9a3" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
          <p className="muted" style={{ marginTop: 8 }}>
            Predicted next month spend: <strong style={{ color: "var(--text)" }}>₹{forecast.predicted_next_month.toLocaleString("en-IN")}</strong>
            {forecast.over_budget_risk && <span className="chip anomaly" style={{ marginLeft: 8 }}>⚠ over budget risk</span>}
          </p>
        </div>
      </div>

      {summary.anomalies.length > 0 && (
        <div className="card">
          <h3 className="section-title">⚠ Unusual transactions (ML-flagged)</h3>
          {summary.anomalies.map((a) => (
            <div className="txn-row" key={a.id} style={{ gridTemplateColumns: "2fr 1fr 1fr" }}>
              <div>{a.description}</div>
              <div className="muted">{a.category}</div>
              <div className="amount neg">−₹{Math.abs(a.amount).toLocaleString("en-IN")}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
