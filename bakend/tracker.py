"""
tracker.py — Railway pe deploy karo
Click tracking server with PostgreSQL support
"""

from flask import Flask, redirect, request, jsonify
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

app = Flask(__name__)

# ─────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────
def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS clicks (
            id        SERIAL PRIMARY KEY,
            email     TEXT,
            name      TEXT,
            round     TEXT,
            ip        TEXT,
            clicked_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
init_db() 
# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.route("/track")
def track():
    email      = request.args.get("email", "unknown")
    name       = request.args.get("name",  "unknown")
    round_name = request.args.get("round", "unknown")
    ip         = request.remote_addr

    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO clicks (email, name, round, ip) VALUES (%s, %s, %s, %s)",
            (email, name, round_name, ip)
        )
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Click: {name} | {email} | {round_name} | {ip}")
    except Exception as e:
        print(f"❌ DB error: {e}")

    # ← Apni website ka URL daalo
    return redirect("https://yourwebsite.com")


@app.route("/stats")
def stats():
    """
    Browser mein /stats khologe to click summary dikhega
    """
    try:
        conn = get_db()
        cur  = conn.cursor()

        cur.execute("SELECT COUNT(*) AS total FROM clicks")
        total = cur.fetchone()["total"]

        cur.execute("""
            SELECT email, name, round, ip, clicked_at
            FROM clicks
            ORDER BY clicked_at DESC
            LIMIT 50
        """)
        rows = cur.fetchall()

        cur.execute("""
            SELECT round, COUNT(*) as cnt
            FROM clicks
            GROUP BY round
        """)
        by_round = cur.fetchall()

        cur.close()
        conn.close()

        html  = f"<h2>📊 Total Clicks: {total}</h2>"
        html += "<h3>By Round:</h3><ul>"
        for r in by_round:
            html += f"<li>{r['round']}: {r['cnt']} clicks</li>"
        html += "</ul>"
        html += "<h3>Recent Clicks:</h3><table border='1' cellpadding='6'>"
        html += "<tr><th>Name</th><th>Email</th><th>Round</th><th>IP</th><th>Time</th></tr>"
        for row in rows:
            html += f"<tr><td>{row['name']}</td><td>{row['email']}</td><td>{row['round']}</td><td>{row['ip']}</td><td>{row['clicked_at']}</td></tr>"
        html += "</table>"
        return html

    except Exception as e:
        return f"❌ Error: {e}"
    
@app.route("/stats-json")
def stats_json():
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) AS total FROM clicks")
        total = cur.fetchone()["total"]
        cur.execute("""
            SELECT email, name, round, ip,
                   clicked_at::text as clicked_at
            FROM clicks ORDER BY clicked_at DESC LIMIT 200
        """)
        clicks = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT round, COUNT(*) as cnt FROM clicks GROUP BY round")
        by_round = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"total": total, "clicks": clicks, "by_round": by_round})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/clicks")
def get_clicks():
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            SELECT name, email, round, ip,
                   clicked_at::text as time
            FROM clicks ORDER BY clicked_at DESC LIMIT 200
        """)
        clicks = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(clicks)
    except Exception as e:
        return jsonify([]), 500
    
  

    
@app.route("/upload-leads", methods=["POST"])
def upload_leads():
    try:
        file = request.files["file"]
        file.save("leads.csv")
        return jsonify({"status": "ok", "message": "leads.csv uploaded"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/run-emails", methods=["POST"])
def run_emails():
    import threading
    from email_sender import run
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
    return jsonify({"status": "started", "message": "Email sending started in background"})

import threading
_stop_flag = threading.Event()

@app.route("/stop-emails", methods=["POST"])
def stop_emails():
    _stop_flag.set()
    return jsonify({"status": "stopped"})        
    
    




# ─────────────────────────────────────────
# START
# ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
