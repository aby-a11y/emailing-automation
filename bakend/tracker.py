"""
tracker.py — Railway 
Click tracking + Leads persistence with PostgreSQL
"""

from flask import Flask, redirect, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id              SERIAL PRIMARY KEY,
            name            TEXT,
            email           TEXT UNIQUE,
            replied         TEXT DEFAULT 'FALSE',
            round1_sent     TEXT DEFAULT 'FALSE',
            round1_date     TEXT DEFAULT '',
            followup1_sent  TEXT DEFAULT 'FALSE',
            followup1_date  TEXT DEFAULT '',
            followup2_sent  TEXT DEFAULT 'FALSE',
            followup2_date  TEXT DEFAULT '',
            updated_at      TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/track")
def track():
    email      = request.args.get("email", "unknown")
    name       = request.args.get("name",  "unknown")
    round_name = request.args.get("round", "unknown")
    ip         = request.remote_addr
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("INSERT INTO clicks (email, name, round, ip) VALUES (%s, %s, %s, %s)", (email, name, round_name, ip))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB error: {e}")
    return redirect("https://yourwebsite.com")

@app.route("/clicks")
def get_clicks():
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT name, email, round, ip, clicked_at::text as time FROM clicks ORDER BY clicked_at DESC LIMIT 200")
        clicks = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(clicks)
    except:
        return jsonify([]), 500

@app.route("/leads", methods=["GET"])
def get_leads():
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT name, email, replied, round1_sent, round1_date, followup1_sent, followup1_date, followup2_sent, followup2_date FROM leads ORDER BY id ASC")
        leads = [dict(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify(leads)
    except:
        return jsonify([]), 500

@app.route("/leads", methods=["POST"])
def save_leads():
    try:
        data  = request.get_json()
        leads = data.get("leads", [])
        conn  = get_db()
        cur   = conn.cursor()
        for lead in leads:
            cur.execute("""
                INSERT INTO leads (name, email, replied, round1_sent, round1_date, followup1_sent, followup1_date, followup2_sent, followup2_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    name=EXCLUDED.name, replied=EXCLUDED.replied,
                    round1_sent=EXCLUDED.round1_sent, round1_date=EXCLUDED.round1_date,
                    followup1_sent=EXCLUDED.followup1_sent, followup1_date=EXCLUDED.followup1_date,
                    followup2_sent=EXCLUDED.followup2_sent, followup2_date=EXCLUDED.followup2_date,
                    updated_at=NOW()
            """, (lead.get("name",""), lead.get("email",""), lead.get("replied","FALSE"),
                  lead.get("round1_sent","FALSE"), lead.get("round1_date",""),
                  lead.get("followup1_sent","FALSE"), lead.get("followup1_date",""),
                  lead.get("followup2_sent","FALSE"), lead.get("followup2_date","")))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "saved": len(leads)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/leads/toggle-reply", methods=["POST"])
def toggle_reply():
    try:
        data    = request.get_json()
        email   = data.get("email")
        replied = data.get("replied", "FALSE")
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("UPDATE leads SET replied=%s, updated_at=NOW() WHERE email=%s", (replied, email))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/leads/clear", methods=["POST"])
def clear_leads():
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM leads")
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import threading
_stop_flag  = threading.Event()
_is_running = False

@app.route("/automation/status", methods=["GET"])
def automation_status():
    return jsonify({"running": _is_running})

@app.route("/run-emails", methods=["POST"])
def run_emails():
    global _is_running
    if _is_running:
        return jsonify({"status": "already_running"})
    _stop_flag.clear()
    _is_running = True
    def run_with_flag():
        global _is_running
        try:
            from email_sender import run
            run(_stop_flag)
        except Exception as e:
            print(f"Email error: {e}")
        finally:
            _is_running = False
    t = threading.Thread(target=run_with_flag)
    t.daemon = True
    t.start()
    return jsonify({"status": "started"})

@app.route("/stop-emails", methods=["POST"])
def stop_emails():
    global _is_running
    _stop_flag.set()
    _is_running = False
    return jsonify({"status": "stopped"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
