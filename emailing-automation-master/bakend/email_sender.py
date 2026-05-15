import smtplib
import random
import time
import pandas as pd
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
import urllib.parse

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────
EMAIL    = os.environ["EMAIL"]       # Railway Variable
PASSWORD = os.environ["PASSWORD"]    # Railway Variable

TRACKING_BASE_URL = os.environ.get("TRACKING_BASE_URL", "...")

LEADS_FILE   = "leads.csv"      # Columns: Name, Email
STATUS_FILE  = "status.csv"     # Auto-manage hoga — mat chhona

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
# STATUS FILE SETUP
# ─────────────────────────────────────────
def load_status():
    if os.path.exists(STATUS_FILE):
        return pd.read_csv(STATUS_FILE)
    else:
        df = pd.read_csv(LEADS_FILE)
        status = pd.DataFrame({
            "Name"           : df["Name"],
            "Email"          : df["Email"],
            "replied"        : False,       # Manual: TRUE likhna jinhone reply kiya
            "round1_sent"    : False,
            "round1_date"    : "",
            "followup1_sent" : False,
            "followup1_date" : "",
            "followup2_sent" : False,
            "followup2_date" : "",
        })
        status.to_csv(STATUS_FILE, index=False)
        print(f"✅ {STATUS_FILE} create ho gaya — jinhone reply kiya unka 'replied' column TRUE kar do.")
        return status

def save_status(df):
    df.to_csv(STATUS_FILE, index=False)

# ─────────────────────────────────────────
# TRACKING URL
# ─────────────────────────────────────────
def make_tracked_url(email, name, round_name):
    params = urllib.parse.urlencode({
        "email": email,
        "name" : name,
        "round": round_name
    })
    return f"{TRACKING_BASE_URL}/track?{params}"

# ─────────────────────────────────────────
# SMTP
# ─────────────────────────────────────────
def connect_server():
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(EMAIL, PASSWORD)
    return server

def send_email(server, to_email, name, subject, body):
    msg          = MIMEText(body)
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
def run():
    status = load_status()
    server = connect_server()
    today  = datetime.today().date()
    sent_count = 0

    for i, row in status.iterrows():

        # Jinhone reply kiya — skip karo
        if str(row["replied"]).strip().upper() == "TRUE":
            print(f"  ⏭  Skipped (replied): {row['Email']}")
            continue

        # Reconnect har 15 emails pe
        if sent_count > 0 and sent_count % 15 == 0:
            try:
                server.quit()
            except:
                pass
            server = connect_server()
            print("🔄 Server reconnected")

        tracked_link = make_tracked_url(row["Email"], row["Name"], "round1")

        # ── Round 1 ──────────────────────────────
        if not str(row["round1_sent"]).strip().upper() == "TRUE":
            subject = random.choice(subjects_round1)
            body    = random.choice(templates_round1).format(
                        name=row["Name"], tracked_link=tracked_link)
            print(f"[Round 1] {row['Name']} <{row['Email']}>")
            ok = send_email(server, row["Email"], row["Name"], subject, body)
            if ok:
                status.at[i, "round1_sent"] = True
                status.at[i, "round1_date"] = str(today)
                save_status(status)
                sent_count += 1
                delay = random.randint(40, 90)
                print(f"  ⏳ Waiting {delay}s...\n")
                time.sleep(delay)
            continue

        # ── Follow-up 1 (3 din baad) ─────────────
        r1_date = row["round1_date"]
        if (str(row["round1_sent"]).upper() == "TRUE"
                and not str(row["followup1_sent"]).upper() == "TRUE"
                and r1_date):
            days_since = (today - datetime.strptime(str(r1_date), "%Y-%m-%d").date()).days
            if days_since >= 3:
                tracked_link = make_tracked_url(row["Email"], row["Name"], "followup1")
                subject = random.choice(subjects_followup1)
                body    = random.choice(templates_followup1).format(
                            name=row["Name"], tracked_link=tracked_link)
                print(f"[Follow-up 1] {row['Name']} <{row['Email']}>")
                ok = send_email(server, row["Email"], row["Name"], subject, body)
                if ok:
                    status.at[i, "followup1_sent"] = True
                    status.at[i, "followup1_date"] = str(today)
                    save_status(status)
                    sent_count += 1
                    delay = random.randint(40, 90)
                    print(f"  ⏳ Waiting {delay}s...\n")
                    time.sleep(delay)
            continue

        # ── Follow-up 2 (6 din baad Round 1 se) ──
        if (str(row["followup1_sent"]).upper() == "TRUE"
                and not str(row["followup2_sent"]).upper() == "TRUE"
                and r1_date):
            days_since = (today - datetime.strptime(str(r1_date), "%Y-%m-%d").date()).days
            if days_since >= 6:
                tracked_link = make_tracked_url(row["Email"], row["Name"], "followup2")
                subject = random.choice(subjects_followup2)
                body    = random.choice(templates_followup2).format(
                            name=row["Name"], tracked_link=tracked_link)
                print(f"[Follow-up 2] {row['Name']} <{row['Email']}>")
                ok = send_email(server, row["Email"], row["Name"], subject, body)
                if ok:
                    status.at[i, "followup2_sent"] = True
                    status.at[i, "followup2_date"] = str(today)
                    save_status(status)
                    sent_count += 1
                    delay = random.randint(40, 90)
                    print(f"  ⏳ Waiting {delay}s...\n")
                    time.sleep(delay)

    try:
        server.quit()
    except:
        pass

    print(f"\n✅ Done! Total emails sent this run: {sent_count}")
    print(f"📄 Status saved in: {STATUS_FILE}")

if __name__ == "__main__":
    run()
