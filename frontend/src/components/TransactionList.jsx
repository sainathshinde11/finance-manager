import { txnApi } from "../api";

export default function TransactionList({ transactions, onChanged }) {
  const remove = async (id) => {
    await txnApi.remove(id);
    onChanged();
  };

  return (
    <div className="card">
      <h3 className="section-title">Recent transactions</h3>
      {transactions.length === 0 && <p className="muted">No transactions yet. Add your first one.</p>}
      {transactions.map((t) => (
        <div className="txn-row" key={t.id}>
          <div>
            <div>{t.description}</div>
            <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
              <span className="chip">{t.category}</span>
              {t.category_source === "ml" && <span className="chip ml">ML-tagged</span>}
              {t.is_anomaly && <span className="chip anomaly">⚠ unusual</span>}
            </div>
          </div>
          <div className="muted">{t.date}</div>
          <div />
          <div className={`amount ${t.amount >= 0 ? "pos" : "neg"}`}>
            {t.amount >= 0 ? "+" : "−"}₹{Math.abs(t.amount).toLocaleString("en-IN")}
          </div>
          <button className="ghost" onClick={() => remove(t.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
}
