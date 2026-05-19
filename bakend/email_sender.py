import smtplib
import random
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from email.mime.text import MIMEText
from datetime import datetime
import os
import urllib.parse

# ─────────────────────────────────────────
# CONFIG — Railway env variables se aata hai
# ─────────────────────────────────────────
EMAIL             = os.environ.get("SENDER_EMAIL",      "deya5579@gmail.com")
PASSWORD          = os.environ.get("SENDER_PASSWORD",   "bwto rsis pzaw osnp")
TRACKING_BASE_URL = os.environ.get("TRACKING_BASE_URL", "https://your-app.up.railway.app")

# ─────────────────────────────────────────
# SUBJECTS
# ─────────────────────────────────────────
subjects_round1 = [
    "Quick help with your workload (low-cost support)",
    "Quick support for your agency workload",
    "Struggling to keep up with client work?",
    "Can I help with your current projects?",
    "Scale your agency without hiring more staff",
    "Suggestion for your business",
    "Quick question about your delivery process",
    "Reliable backend support for your agency",
    "Extra hands for your agency?",
    "Quick 10-min idea"
]

subjects_followup1 = [
    "Just checking in — did you get my last email?",
    "Following up on my previous message",
    "Still open to help with your workload",
    "Quick follow-up from Abhishek",
    "Did my last email reach you?"
]

subjects_followup2 = [
    "Last follow-up from my side",
    "One last check-in before I close out",
    "Final note — backend support offer",
    "Closing the loop on my earlier message",
    "One more try — hope this finds you well"
]

# ─────────────────────────────────────────
# TEMPLATES — Round 1
# ─────────────────────────────────────────
templates_round1 = [
"""Hi {name},

I came across your agency and noticed you're doing great work in digital marketing.

I understand that scaling an agency often comes with challenges like managing workload, hiring reliable talent, and maintaining delivery timelines.

I wanted to reach out because I can help you handle your backend work at a very affordable cost.

We provide support in:
- Website development (WordPress, custom sites)
- SEO (on-page, technical, audits)
- Digital marketing tasks (campaign setup, reporting, optimization)

The best part is — you don't need to hire full-time staff.
You can outsource work to us starting at just $5–$6/hour, ensuring your projects are delivered on time without increasing your overhead.

If you're open to it, I'd be happy to do a small sample task so you can evaluate the quality before moving forward.

👉 Click here to see how we work: {tracked_link}

Let me know if you'd like to discuss or test this out.

Best regards,
Abhishek
""",

"""Hello {name},

I came across your agency and noticed the kind of projects you're handling.

Most agencies I speak with are great at getting clients but often get stuck when it comes to execution bandwidth.

I help agencies handle their backend work — whether it's web development, SEO tasks, or campaign execution — so they can scale without worrying about hiring.

If you're ever looking for reliable extra hands to deliver work on time, I'd be happy to help.

👉 Learn more here: {tracked_link}

Happy to do a quick sample task as well so you can check quality.

Best,
Abhishek
""",

"""Hi {name},

Quick question — are you ever in a situation where client work piles up but hiring someone full-time doesn't make sense?

That's exactly where I come in.

I support agencies with:
- Website development
- SEO execution
- Digital marketing tasks

So you can focus on getting clients while I handle the delivery side.

No long-term commitment — just reliable support when you need it.

👉 See how it works: {tracked_link}

Let me know if you'd like to test with a small task.

Best,
Abhishek
"""
]

# ─────────────────────────────────────────
# TEMPLATES — Follow-up 1 (3 din baad)
# ─────────────────────────────────────────
templates_followup1 = [
"""Hi {name},

Just wanted to follow up on my email from a few days ago.

I had reached out about helping your agency with backend work — web development, SEO, and marketing tasks — at a very affordable rate ($5–$6/hr).

In case my earlier email got buried, I'd love to connect and discuss if there's a fit.

👉 Quick look here: {tracked_link}

Happy to start with a free sample task, no commitment needed.

Best,
Abhishek
""",

"""Hello {name},

Hope you're doing well!

I sent you an email a few days back about supporting your agency with execution work.

Just checking in to see if you had a chance to go through it.

If you're ever dealing with project overload or need extra bandwidth, I'd love to help — starting with a trial task.

👉 Check this out: {tracked_link}

Let me know either way!

Best,
Abhishek
""",

"""Hi {name},

I know inboxes get busy — just a quick nudge on my earlier message.

I work with agencies to handle delivery-side work (development, SEO, campaigns) so you can scale without hiring.

If it sounds interesting, happy to do a small task so you can judge quality before deciding anything.

👉 More info here: {tracked_link}

Best,
Abhishek
"""
]

# ─────────────────────────────────────────
# TEMPLATES — Follow-up 2 (6 din baad)
# ─────────────────────────────────────────
templates_followup2 = [
"""Hi {name},

This will be my last follow-up — I don't want to clutter your inbox.

I had reached out twice about helping your agency with backend execution work.

If the timing isn't right now, totally understood. But if at any point you need reliable support for web, SEO, or marketing tasks, feel free to reach out anytime.

👉 You can always find me here: {tracked_link}

Wishing you and your team continued success!

Best,
Abhishek
""",

"""Hello {name},

Just one final note from my side.

I've sent a couple of emails about helping your agency scale without the hiring headache — execution support for dev, SEO, and marketing.

If it's not the right time, no worries at all. I'll stop here.

But if things ever change, the door is open.

👉 Keep this link handy: {tracked_link}

Take care!

Best,
Abhishek
"""
]

# ─────────────────────────────────────────
# DB FUNCTIONS — CSV bilkul nahi, sirf PostgreSQL
# ─────────────────────────────────────────
def get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)

def load_status():
    """DB se saare leads fetch karo"""
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT name, email, replied,
               round1_sent, round1_date,
               followup1_sent, followup1_date,
               followup2_sent, followup2_date
        FROM leads ORDER BY id ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    print(f"📋 DB se {len(rows)} leads load hue")
    return rows

def save_lead_round1(email, date_str):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE leads SET round1_sent='TRUE', round1_date=%s, updated_at=NOW() WHERE email=%s",
        (date_str, email)
    )
    conn.commit(); cur.close(); conn.close()

def save_lead_followup1(email, date_str):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE leads SET followup1_sent='TRUE', followup1_date=%s, updated_at=NOW() WHERE email=%s",
        (date_str, email)
    )
    conn.commit(); cur.close(); conn.close()

def save_lead_followup2(email, date_str):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(
        "UPDATE leads SET followup2_sent='TRUE', followup2_date=%s, updated_at=NOW() WHERE email=%s",
        (date_str, email)
    )
    conn.commit(); cur.close(); conn.close()

# ─────────────────────────────────────────
# TRACKING URL
# ─────────────────────────────────────────
def make_tracked_url(email, name, round_name):
    params = urllib.parse.urlencode({"email": email, "name": name, "round": round_name})
    return f"{TRACKING_BASE_URL}/track?{params}"

# ─────────────────────────────────────────
# SMTP
# ─────────────────────────────────────────
def connect_server():
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, PASSWORD)
    return server

def send_email(server, to_email, name, subject, body):
    msg            = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = EMAIL
    msg["To"]      = to_email
    try:
        server.sendmail(EMAIL, to_email, msg.as_string())
        print(f"  ✅ Sent → {to_email}")
        return True
    except Exception as e:
        print(f"  ❌ Failed → {to_email} | {e}")
        return False

# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────
def run(stop_flag=None):
    leads      = load_status()
    today      = datetime.today().date()
    sent_count = 0

    if not leads:
        print("⚠️  DB mein koi leads nahi hain. Pehle dashboard se CSV upload karo.")
        return

    server = connect_server()

    for row in leads:

        if stop_flag and stop_flag.is_set():
            print("⏹ Stop flag — automation band")
            break

        name  = row.get("name",  "") or ""
        email = row.get("email", "") or ""

        if not email:
            continue

        # Replied wale skip
        if str(row["replied"]).strip().upper() == "TRUE":
            print(f"  ⏭  Skipped (replied): {email}")
            continue

        # Reconnect har 15 pe
        if sent_count > 0 and sent_count % 15 == 0:
            try: server.quit()
            except: pass
            server = connect_server()
            print("🔄 Server reconnected")

        # ── Round 1 ──────────────────────────────
        if str(row["round1_sent"]).strip().upper() != "TRUE":
            tracked_link = make_tracked_url(email, name, "round1")
            subject = random.choice(subjects_round1)
            body    = random.choice(templates_round1).format(name=name, tracked_link=tracked_link)
            print(f"[Round 1] {name} <{email}>")
            ok = send_email(server, email, name, subject, body)
            if ok:
                save_lead_round1(email, str(today))
                sent_count += 1
                delay = random.randint(40, 90)
                print(f"  ⏳ Waiting {delay}s...\n")
                if stop_flag and stop_flag.is_set(): break
                time.sleep(delay)
            continue

        r1_date = row.get("round1_date", "") or ""

        # ── Follow-up 1 (3 din baad) ─────────────
        if str(row["round1_sent"]).upper() == "TRUE" and str(row["followup1_sent"]).upper() != "TRUE" and r1_date:
            try:
                days_since = (today - datetime.strptime(str(r1_date), "%Y-%m-%d").date()).days
            except:
                days_since = 0
            if days_since >= 3:
                tracked_link = make_tracked_url(email, name, "followup1")
                subject = random.choice(subjects_followup1)
                body    = random.choice(templates_followup1).format(name=name, tracked_link=tracked_link)
                print(f"[Follow-up 1] {name} <{email}>")
                ok    = send_email(server, email, name, subject, body)
                delay = random.randint(40, 90)
                if ok:
                    save_lead_followup1(email, str(today))
                    sent_count += 1
                print(f"  ⏳ Waiting {delay}s...\n")
                if stop_flag and stop_flag.is_set(): break
                time.sleep(delay)
            continue

        # ── Follow-up 2 (6 din baad Round 1 se) ──
        if str(row["followup1_sent"]).upper() == "TRUE" and str(row["followup2_sent"]).upper() != "TRUE" and r1_date:
            try:
                days_since = (today - datetime.strptime(str(r1_date), "%Y-%m-%d").date()).days
            except:
                days_since = 0
            if days_since >= 6:
                tracked_link = make_tracked_url(email, name, "followup2")
                subject = random.choice(subjects_followup2)
                body    = random.choice(templates_followup2).format(name=name, tracked_link=tracked_link)
                print(f"[Follow-up 2] {name} <{email}>")
                ok    = send_email(server, email, name, subject, body)
                delay = random.randint(40, 90)
                if ok:
                    save_lead_followup2(email, str(today))
                    sent_count += 1
                print(f"  ⏳ Waiting {delay}s...\n")
                if stop_flag and stop_flag.is_set(): break
                time.sleep(delay)

    try: server.quit()
    except: pass

    print(f"\n✅ Done! Total emails sent this run: {sent_count}")

if __name__ == "__main__":
    run()
