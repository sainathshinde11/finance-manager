import { useEffect, useRef, useState } from "react";
import { txnApi } from "../api";

export default function AddTransaction({ categories, onCreated }) {
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [type, setType] = useState("expense"); // expense | income
  const [category, setCategory] = useState("");
  const [suggestion, setSuggestion] = useState(null);
  const debounceRef = useRef(null);

  useEffect(() => {
    clearTimeout(debounceRef.current);
    if (description.trim().length < 3) {
      setSuggestion(null);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const result = await txnApi.categorizePreview(description);
        setSuggestion(result);
      } catch {
        setSuggestion(null);
      }
    }, 400);
    return () => clearTimeout(debounceRef.current);
  }, [description]);

  const submit = async (e) => {
    e.preventDefault();
    if (!description.trim() || !amount) return;
    const signedAmount = type === "expense" ? -Math.abs(Number(amount)) : Math.abs(Number(amount));
    await txnApi.create({
      description: description.trim(),
      amount: signedAmount,
      category: category || undefined, // let ML decide if left blank
    });
    setDescription("");
    setAmount("");
    setCategory("");
    setSuggestion(null);
    onCreated();
  };

  return (
    <div className="card">
      <h3 className="section-title">Add transaction</h3>
      <form onSubmit={submit}>
        <div className="form-row">
          <label>Description</label>
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. swiggy order dinner"
            required
          />
          {suggestion && (
            <div className="chip ml" style={{ marginTop: 8 }}>
              ✨ ML suggests: {suggestion.category} · {Math.round(suggestion.confidence * 100)}% confidence
            </div>
          )}
        </div>

        <div className="grid grid-2" style={{ gap: 12 }}>
          <div className="form-row">
            <label>Amount (₹)</label>
            <input type="number" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </div>
          <div className="form-row">
            <label>Type</label>
            <select value={type} onChange={(e) => setType(e.target.value)}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <label>Category (leave blank to auto-categorize with ML)</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">— Auto-categorize —</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <button type="submit" className="primary" style={{ width: "100%" }}>
          Add transaction
        </button>
      </form>
    </div>
  );
}
