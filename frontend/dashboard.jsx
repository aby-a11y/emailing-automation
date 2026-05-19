import { useState, useCallback, useRef, useEffect } from "react";
import Papa from "papaparse";
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;
const TABS = ["Overview", "Leads", "Clicks", "Settings"];


const ROUND_COLORS = {
  round1: "#00e5a0",
  followup1: "#f5a623",
  followup2: "#e05c5c",
  unknown: "#888",
};

const ROUND_LABELS = {
  round1: "Round 1",
  followup1: "Follow-up 1",
  followup2: "Follow-up 2",
};

function Badge({ text, color }) {
  return (
    <span style={{
      background: color + "22",
      color: color,
      border: `1px solid ${color}44`,
      borderRadius: 4,
      padding: "2px 10px",
      fontSize: 11,
      fontWeight: 700,
      letterSpacing: 1,
      textTransform: "uppercase",
    }}>{text}</span>
  );
}

function StatCard({ label, value, sub, accent }) {
  return (
    <div style={{
      background: "#13161d",
      border: "1px solid #23272f",
      borderRadius: 12,
      padding: "24px 28px",
      flex: 1,
      minWidth: 160,
      position: "relative",
      overflow: "hidden",
    }}>
      <div style={{
        position: "absolute", top: 0, left: 0, width: "100%", height: 3,
        background: `linear-gradient(90deg, ${accent}, transparent)`,
      }} />
      <div style={{ color: "#555", fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 10 }}>{label}</div>
      <div style={{ color: "#f0f0f0", fontSize: 36, fontFamily: "'DM Mono', monospace", fontWeight: 700, lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ color: "#444", fontSize: 12, marginTop: 8 }}>{sub}</div>}
    </div>
  );
}
function AutomationControl({ backendUrl, showToast }) {
  const [running, setRunning] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${backendUrl}/automation/status`)
      .then(r => r.json())
      .then(d => setRunning(d.running))
      .catch(() => {});
  }, [backendUrl]);

  const start = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${backendUrl}/run-emails`, { method: "POST" });
      const d = await res.json();
      if (d.status === "already_running") showToast("Already running!", "#f5a623");
      else { setRunning(true); showToast("✓ Automation started", "#00e5a0"); }
    } catch { showToast("Failed to start", "#e05c5c"); }
    setLoading(false);
  };

  const stop = async () => {
    setLoading(true);
    try {
      await fetch(`${backendUrl}/stop-emails`, { method: "POST" });
      setRunning(false);
      showToast("⏹ Automation stopped", "#f5a623");
    } catch { showToast("Failed to stop", "#e05c5c"); }
    setLoading(false);
  };

  return (
    <div style={{
      background: "#13161d", border: `1px solid ${running ? "#00e5a033" : "#23272f"}`,
      borderRadius: 12, padding: "20px 24px",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      flexWrap: "wrap", gap: 16,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <div style={{
          width: 10, height: 10, borderRadius: "50%",
          background: running ? "#00e5a0" : "#444",
          boxShadow: running ? "0 0 8px #00e5a0" : "none",
        }} />
        <div>
          <div style={{ color: "#ddd", fontSize: 14, fontWeight: 600 }}>
            Email Automation — <span style={{ color: running ? "#00e5a0" : "#666" }}>{running ? "Running" : "Stopped"}</span>
          </div>
          <div style={{ color: "#444", fontSize: 12, marginTop: 2 }}>
            {running ? "Sending emails in background..." : "Click Start to begin email sequence"}
          </div>
        </div>
      </div>
      <div>
        {!running
          ? <button onClick={start} disabled={loading} style={{ background: "#00e5a0", border: "none", color: "#000", borderRadius: 8, padding: "10px 24px", cursor: "pointer", fontWeight: 700, fontSize: 13, fontFamily: "inherit" }}>▶ Start Automation</button>
          : <button onClick={stop} disabled={loading} style={{ background: "#e05c5c22", border: "1px solid #e05c5c44", color: "#e05c5c", borderRadius: 8, padding: "10px 24px", cursor: "pointer", fontWeight: 700, fontSize: 13, fontFamily: "inherit" }}>⏹ Stop Automation</button>
        }
      </div>
    </div>
  );
}

function Overview({ leads, clicks, backendUrl, showToast }) {
  const replied = leads.filter(l => String(l.replied).toUpperCase() === "TRUE").length;
  const r1 = leads.filter(l => String(l.round1_sent).toUpperCase() === "TRUE").length;
  const f1 = leads.filter(l => String(l.followup1_sent).toUpperCase() === "TRUE").length;
  const f2 = leads.filter(l => String(l.followup2_sent).toUpperCase() === "TRUE").length;

  const clickByRound = clicks.reduce((acc, c) => {
    acc[c.round] = (acc[c.round] || 0) + 1;
    return acc;
  }, {});

  const barMax = Math.max(r1, f1, f2, 1);
  const bars = [
    { label: "Round 1", val: r1, color: "#00e5a0" },
    { label: "Follow-up 1", val: f1, color: "#f5a623" },
    { label: "Follow-up 2", val: f2, color: "#e05c5c" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
      {/* Automation Control */}
      <AutomationControl backendUrl={backendUrl} showToast={showToast} />
      {/* Stat Cards */}
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <StatCard label="Total Leads" value={leads.length} sub="Uploaded via CSV" accent="#00e5a0" />
        <StatCard label="Replied" value={replied} sub="Eliminated from future sends" accent="#e05c5c" />
        <StatCard label="Total Clicks" value={clicks.length} sub="Across all rounds" accent="#f5a623" />
        <StatCard label="Pending" value={leads.length - replied} sub="Still in pipeline" accent="#5c9ee0" />
      </div>

      {/* Email Progress */}
      <div style={{ background: "#13161d", border: "1px solid #23272f", borderRadius: 12, padding: 28 }}>
        <div style={{ color: "#888", fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 20 }}>Email Send Progress</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {bars.map(b => (
            <div key={b.label}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ color: "#aaa", fontSize: 13 }}>{b.label}</span>
                <span style={{ color: b.color, fontFamily: "monospace", fontSize: 13 }}>{b.val} / {leads.length}</span>
              </div>
              <div style={{ background: "#1e2229", borderRadius: 4, height: 8, overflow: "hidden" }}>
                <div style={{
                  width: leads.length ? `${(b.val / leads.length) * 100}%` : "0%",
                  height: "100%",
                  background: b.color,
                  borderRadius: 4,
                  transition: "width 0.8s cubic-bezier(.4,0,.2,1)",
                }} />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Click breakdown */}
      <div style={{ background: "#13161d", border: "1px solid #23272f", borderRadius: 12, padding: 28 }}>
        <div style={{ color: "#888", fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 20 }}>Click Breakdown by Round</div>
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {["round1", "followup1", "followup2"].map(r => (
            <div key={r} style={{
              flex: 1, minWidth: 120,
              background: "#0e1016",
              border: `1px solid ${ROUND_COLORS[r]}33`,
              borderRadius: 10,
              padding: "18px 20px",
              textAlign: "center",
            }}>
              <div style={{ color: ROUND_COLORS[r], fontSize: 28, fontFamily: "monospace", fontWeight: 700 }}>
                {clickByRound[r] || 0}
              </div>
              <div style={{ color: "#555", fontSize: 11, marginTop: 6, letterSpacing: 1 }}>{ROUND_LABELS[r]}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LeadsTable({ leads, onToggleReply, onClearLeads }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const filtered = leads.filter(l => {
    const q = search.toLowerCase();
    const match = l.name?.toLowerCase().includes(q) || l.email?.toLowerCase().includes(q);
    if (filter === "replied") return match && String(l.replied).toUpperCase() === "TRUE";
    if (filter === "pending") return match && String(l.replied).toUpperCase() !== "TRUE";
    return match;
  });

  const cols = [
    { key: "name", label: "Name" },
    { key: "email", label: "Email" },
    { key: "replied", label: "Replied" },
    { key: "round1_sent", label: "R1" },
    { key: "followup1_sent", label: "F1" },
    { key: "followup2_sent", label: "F2" },
    { key: "round1_date", label: "Last Sent" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Toolbar */}
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
        <input
          placeholder="Search name or email..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            flex: 1, minWidth: 200,
            background: "#13161d", border: "1px solid #2a2f3a",
            borderRadius: 8, padding: "10px 14px",
            color: "#e0e0e0", fontSize: 13, outline: "none",
            fontFamily: "inherit",
          }}
        />
        {["all", "pending", "replied"].map(f => (
          <button key={f} onClick={() => setFilter(f)} style={{
            background: filter === f ? "#00e5a022" : "transparent",
            border: `1px solid ${filter === f ? "#00e5a0" : "#2a2f3a"}`,
            color: filter === f ? "#00e5a0" : "#666",
            borderRadius: 6, padding: "8px 16px", cursor: "pointer",
            fontSize: 12, letterSpacing: 1, textTransform: "capitalize",
            fontFamily: "inherit",
          }}>{f}</button>
        ))}
        <button onClick={onClearLeads} style={{
          background: "#e05c5c11", border: "1px solid #e05c5c33",
          color: "#e05c5c", borderRadius: 6, padding: "8px 14px",
          cursor: "pointer", fontSize: 12, fontFamily: "inherit",
        }}>Clear All</button>
      </div>

      {/* Table */}
      <div style={{ background: "#13161d", border: "1px solid #23272f", borderRadius: 12, overflow: "hidden" }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #1e2229" }}>
                {cols.map(c => (
                  <th key={c.key} style={{
                    padding: "12px 16px", textAlign: "left",
                    color: "#444", fontSize: 10, letterSpacing: 2,
                    textTransform: "uppercase", fontWeight: 600,
                    whiteSpace: "nowrap",
                  }}>{c.label}</th>
                ))}
                <th style={{ padding: "12px 16px", color: "#444", fontSize: 10, letterSpacing: 2, textTransform: "uppercase" }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={cols.length + 1} style={{ padding: 40, textAlign: "center", color: "#333", fontSize: 14 }}>
                    No leads found — upload a CSV to get started
                  </td>
                </tr>
              )}
              {filtered.map((row, i) => {
                const isReplied = String(row.replied).toUpperCase() === "TRUE";
                return (
                  <tr key={i} style={{
                    borderBottom: "1px solid #1a1e26",
                    background: isReplied ? "#1a0e0e" : "transparent",
                    transition: "background 0.2s",
                  }}>
                    <td style={{ padding: "12px 16px", color: "#ddd", fontSize: 13 }}>{row.name}</td>
                    <td style={{ padding: "12px 16px", color: "#888", fontSize: 13, fontFamily: "monospace" }}>{row.email}</td>
                    <td style={{ padding: "12px 16px" }}>
                      {isReplied
                        ? <Badge text="Replied" color="#e05c5c" />
                        : <Badge text="No Reply" color="#444" />}
                    </td>
                    {["round1_sent", "followup1_sent", "followup2_sent"].map(k => (
                      <td key={k} style={{ padding: "12px 16px" }}>
                        {String(row[k]).toUpperCase() === "TRUE"
                          ? <span style={{ color: "#00e5a0", fontSize: 16 }}>✓</span>
                          : <span style={{ color: "#2a2f3a", fontSize: 16 }}>—</span>}
                      </td>
                    ))}
                    <td style={{ padding: "12px 16px", color: "#555", fontSize: 12, fontFamily: "monospace" }}>
                      {row.round1_date || "—"}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <button onClick={() => onToggleReply(i)} style={{
                        background: isReplied ? "#e05c5c22" : "#00e5a011",
                        border: `1px solid ${isReplied ? "#e05c5c44" : "#00e5a033"}`,
                        color: isReplied ? "#e05c5c" : "#00e5a0",
                        borderRadius: 5, padding: "5px 12px",
                        cursor: "pointer", fontSize: 11, fontFamily: "inherit",
                        whiteSpace: "nowrap",
                      }}>
                        {isReplied ? "Unmark" : "Mark Replied"}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div style={{ padding: "10px 16px", borderTop: "1px solid #1e2229", color: "#333", fontSize: 11 }}>
          {filtered.length} of {leads.length} leads shown
        </div>
      </div>
    </div>
  );
}

function ClicksTable({ clicks }) {
  const [search, setSearch] = useState("");
  const filtered = clicks.filter(c =>
    c.name?.toLowerCase().includes(search.toLowerCase()) ||
    c.email?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <input
        placeholder="Search clicks..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        style={{
          background: "#13161d", border: "1px solid #2a2f3a",
          borderRadius: 8, padding: "10px 14px",
          color: "#e0e0e0", fontSize: 13, outline: "none",
          fontFamily: "inherit", width: "100%", boxSizing: "border-box",
        }}
      />
      <div style={{ background: "#13161d", border: "1px solid #23272f", borderRadius: 12, overflow: "hidden" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #1e2229" }}>
              {["Name", "Email", "Round", "IP", "Clicked At"].map(h => (
                <th key={h} style={{
                  padding: "12px 16px", textAlign: "left",
                  color: "#444", fontSize: 10, letterSpacing: 2, textTransform: "uppercase",
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} style={{ padding: 40, textAlign: "center", color: "#333", fontSize: 14 }}>
                  No clicks recorded yet
                </td>
              </tr>
            )}
            {filtered.map((c, i) => (
              <tr key={i} style={{ borderBottom: "1px solid #1a1e26" }}>
                <td style={{ padding: "12px 16px", color: "#ddd", fontSize: 13 }}>{c.name}</td>
                <td style={{ padding: "12px 16px", color: "#888", fontSize: 13, fontFamily: "monospace" }}>{c.email}</td>
                <td style={{ padding: "12px 16px" }}>
                  <Badge text={ROUND_LABELS[c.round] || c.round} color={ROUND_COLORS[c.round] || "#888"} />
                </td>
                <td style={{ padding: "12px 16px", color: "#555", fontSize: 12, fontFamily: "monospace" }}>{c.ip}</td>
                <td style={{ padding: "12px 16px", color: "#555", fontSize: 12, fontFamily: "monospace" }}>{c.time}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: "10px 16px", borderTop: "1px solid #1e2229", color: "#333", fontSize: 11 }}>
          {filtered.length} clicks
        </div>
      </div>
    </div>
  );
}

function Settings({ trackingUrl, setTrackingUrl }) {
  const [saved, setSaved] = useState(false);
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 560 }}>
      <div style={{ background: "#13161d", border: "1px solid #23272f", borderRadius: 12, padding: 28 }}>
        <div style={{ color: "#888", fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 20 }}>Tracking Server</div>
        <label style={{ color: "#666", fontSize: 12, display: "block", marginBottom: 8 }}>Railway Tracking URL</label>
        <input
          value={trackingUrl}
          onChange={e => { setTrackingUrl(e.target.value); setSaved(false); }}
          placeholder="https://your-app.up.railway.app"
          style={{
            width: "100%", boxSizing: "border-box",
            background: "#0e1016", border: "1px solid #2a2f3a",
            borderRadius: 8, padding: "12px 14px",
            color: "#e0e0e0", fontSize: 13, outline: "none",
            fontFamily: "monospace",
          }}
        />
        <div style={{ marginTop: 8, color: "#444", fontSize: 12 }}>
          Track endpoint: <span style={{ color: "#555", fontFamily: "monospace" }}>{trackingUrl || "https://..."}/track?email=&name=&round=</span>
        </div>
        <button onClick={() => setSaved(true)} style={{
          marginTop: 16,
          background: saved ? "#00e5a022" : "#00e5a0",
          color: saved ? "#00e5a0" : "#000",
          border: "none", borderRadius: 8, padding: "10px 24px",
          cursor: "pointer", fontWeight: 700, fontSize: 13,
          fontFamily: "inherit", transition: "all 0.2s",
        }}>{saved ? "✓ Saved" : "Save URL"}</button>
      </div>

      <div style={{ background: "#13161d", border: "1px solid #23272f", borderRadius: 12, padding: 28 }}>
        <div style={{ color: "#888", fontSize: 11, letterSpacing: 2, textTransform: "uppercase", marginBottom: 16 }}>CSV Format Required</div>
        <div style={{ background: "#0e1016", borderRadius: 8, padding: 16, fontFamily: "monospace", fontSize: 12, color: "#888", lineHeight: 1.8 }}>
          <span style={{ color: "#00e5a0" }}>Name</span>,<span style={{ color: "#f5a623" }}>Email</span>,replied,round1_sent,round1_date,followup1_sent,followup1_date,followup2_sent,followup2_date<br />
          <span style={{ color: "#ccc" }}>John Smith</span>,<span style={{ color: "#ccc" }}>john@agency.com</span>,FALSE,FALSE,,FALSE,,FALSE,<br />
          <span style={{ color: "#ccc" }}>Sarah Lee</span>,<span style={{ color: "#ccc" }}>sarah@co.com</span>,TRUE,TRUE,2025-05-13,FALSE,,FALSE,
        </div>
        <div style={{ marginTop: 12, color: "#444", fontSize: 12, lineHeight: 1.7 }}>
          Minimum required columns: <span style={{ color: "#888" }}>Name, Email</span><br />
          All other columns are auto-populated when missing.
        </div>
      </div>
    </div>
  );
}

// ─── MAIN APP ───────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("Overview");
  const [leads, setLeads] = useState([]);
  const [clicks, setClicks] = useState([]);
  const [trackingUrl, setTrackingUrl] = useState(BACKEND_URL);
  const [dragging, setDragging] = useState(false);
  const [toast, setToast] = useState(null);
  const fileRef = useRef();
  useEffect(() => {
  fetch(`${BACKEND_URL}/leads`)
    .then(r => r.json())
    .then(d => setLeads(Array.isArray(d) ? d : []))
    .catch(() => {});

  fetch(`${BACKEND_URL}/clicks`)
    .then(r => r.json())
    .then(d => setClicks(Array.isArray(d) ? d : []))
    .catch(() => {});
}, []);

  const showToast = (msg, color = "#00e5a0") => {
    setToast({ msg, color });
    setTimeout(() => setToast(null), 3000);
  };

  const processCSV = (file) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (result) => {
        const rows = result.data.map(row => ({
          name: row.Name || row.name || "",
          email: row.Email || row.email || "",
          replied: row.replied || "FALSE",
          round1_sent: row.round1_sent || "FALSE",
          round1_date: row.round1_date || "",
          followup1_sent: row.followup1_sent || "FALSE",
          followup1_date: row.followup1_date || "",
          followup2_sent: row.followup2_sent || "FALSE",
          followup2_date: row.followup2_date || "",
        }));
        setLeads(rows);
        fetch(`${BACKEND_URL}/leads`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ leads: rows }),
        }).catch(() => {});
        showToast(`✓ ${rows.length} leads loaded & saved`);
        setTab("Leads");
      },
      error: () => showToast("CSV parse failed", "#e05c5c"),
    });
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".csv")) processCSV(file);
    else showToast("Please drop a .csv file", "#e05c5c");
  }, []);

  const handleToggleReply = (email, isReplied) => {
    const newVal = isReplied ? "FALSE" : "TRUE";
    setLeads(prev => prev.map(l => l.email === email ? { ...l, replied: newVal } : l));
    fetch(`${BACKEND_URL}/leads/toggle-reply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, replied: newVal }),
    }).catch(() => {});
  };

  const exportCSV = () => {
    if (!leads.length) return showToast("No leads to export", "#f5a623");
    const headers = ["Name","Email","replied","round1_sent","round1_date","followup1_sent","followup1_date","followup2_sent","followup2_date"];
    const rows = leads.map(l => [l.name,l.email,l.replied,l.round1_sent,l.round1_date,l.followup1_sent,l.followup1_date,l.followup2_sent,l.followup2_date]);
    const csv = [headers, ...rows].map(r => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "status.csv"; a.click();
    showToast("✓ status.csv downloaded");
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0c10",
      color: "#e0e0e0",
      fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: #0a0c10; }
        ::-webkit-scrollbar-thumb { background: #23272f; border-radius: 3px; }
        input::placeholder { color: #333; }
        .drop-zone:hover { border-color: #00e5a066 !important; background: #00e5a008 !important; }
        .nav-tab { transition: all 0.15s; }
        .nav-tab:hover { color: #ccc !important; }
      `}</style>

      {/* Header */}
      <div style={{
        background: "#0d0f14",
        borderBottom: "1px solid #1a1e26",
        padding: "0 32px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        height: 60,
        position: "sticky", top: 0, zIndex: 100,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 30, height: 30,
            background: "linear-gradient(135deg, #00e5a0, #00a86b)",
            borderRadius: 8,
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 14, fontWeight: 900, color: "#000",
          }}>A</div>
          <span style={{ fontWeight: 600, fontSize: 15, letterSpacing: 0.5 }}>OutreachOS</span>
          <span style={{
            background: "#00e5a011", color: "#00e5a0",
            border: "1px solid #00e5a033", borderRadius: 4,
            padding: "2px 8px", fontSize: 10, letterSpacing: 1,
          }}>BETA</span>
        </div>

        <div style={{ display: "flex", gap: 6 }}>
          {TABS.map(t => (
            <button key={t} className="nav-tab" onClick={() => setTab(t)} style={{
              background: tab === t ? "#1a1e26" : "transparent",
              border: "none",
              color: tab === t ? "#e0e0e0" : "#444",
              borderRadius: 6, padding: "6px 16px",
              cursor: "pointer", fontSize: 13, fontFamily: "inherit",
            }}>{t}</button>
          ))}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={() => fileRef.current.click()} style={{
            background: "#1a1e26", border: "1px solid #2a2f3a",
            color: "#aaa", borderRadius: 7, padding: "7px 16px",
            cursor: "pointer", fontSize: 12, fontFamily: "inherit",
          }}>↑ Upload CSV</button>
          <button onClick={exportCSV} style={{
            background: "#00e5a0", border: "none",
            color: "#000", borderRadius: 7, padding: "7px 16px",
            cursor: "pointer", fontSize: 12, fontWeight: 700, fontFamily: "inherit",
          }}>↓ Export CSV</button>
          <input ref={fileRef} type="file" accept=".csv" style={{ display: "none" }}
            onChange={e => { if (e.target.files[0]) processCSV(e.target.files[0]); e.target.value = ""; }} />
        </div>
      </div>

      {/* Main */}
      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "32px 24px" }}>

        {/* Drop zone — only when no leads */}
        {leads.length === 0 && tab !== "Settings" && (
          <div
            className="drop-zone"
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileRef.current.click()}
            style={{
              border: `2px dashed ${dragging ? "#00e5a0" : "#23272f"}`,
              borderRadius: 16, padding: "60px 40px",
              textAlign: "center", cursor: "pointer",
              marginBottom: 32,
              background: dragging ? "#00e5a008" : "transparent",
              transition: "all 0.2s",
            }}>
            <div style={{ fontSize: 40, marginBottom: 16 }}>📂</div>
            <div style={{ color: "#555", fontSize: 15 }}>Drop your <span style={{ color: "#00e5a0" }}>leads.csv</span> here or click to upload</div>
            <div style={{ color: "#333", fontSize: 12, marginTop: 8 }}>Required columns: Name, Email</div>
          </div>
        )}

        {/* Tab Content */}
        {tab === "Overview" && <Overview leads={leads} clicks={clicks} backendUrl={BACKEND_URL} showToast={showToast} />}
        {tab === "Leads" && (
          <LeadsTable
            leads={leads}
            onToggleReply={handleToggleReply}
            onClearLeads={() => {
              fetch(`${BACKEND_URL}/leads/clear`, { method: "POST" }).catch(() => {});
              setLeads([]);
              showToast("Leads cleared");
            }}
          />
        )}
        {tab === "Clicks" && <ClicksTable clicks={clicks} />}
        {tab === "Settings" && <Settings trackingUrl={trackingUrl} setTrackingUrl={setTrackingUrl} />}
      </div>

      {/* Toast */}
      {toast && (
        <div style={{
          position: "fixed", bottom: 24, right: 24,
          background: "#13161d", border: `1px solid ${toast.color}44`,
          color: toast.color, borderRadius: 10,
          padding: "12px 20px", fontSize: 13,
          boxShadow: `0 4px 24px ${toast.color}22`,
          animation: "fadeIn 0.2s ease",
          zIndex: 999,
        }}>{toast.msg}</div>
      )}
      <style>{`@keyframes fadeIn { from { opacity:0; transform:translateY(8px) } to { opacity:1; transform:translateY(0) } }`}</style>
    </div>
  );
}
