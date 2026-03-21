# ════════════════════════════════════════════════════════
#  OTP EMAIL AUTHENTICATION
#  Paste this entire block into server.py
#  BEFORE the line:  if __name__ == "__main__":
#
#  Then add these to Railway → Variables:
#    EMAIL_USER = your Gmail address  (e.g. yourapp@gmail.com)
#    EMAIL_PASS = your Gmail App Password (NOT your normal password)
#
#  To get Gmail App Password:
#    1. Go to myaccount.google.com → Security
#    2. Enable 2-Step Verification
#    3. Go to App Passwords → Generate
#    4. Copy the 16-character password → paste as EMAIL_PASS
# ════════════════════════════════════════════════════════

import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# In-memory OTP store: { email: { otp, expires_at } }
_otp_store = {}

EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASS = os.environ.get("EMAIL_PASS", "")


def _generate_otp():
    return ''.join(random.choices(string.digits, k=6))


def _send_otp_email(to_email, otp):
    """Send OTP via Gmail SMTP."""
    if not EMAIL_USER or not EMAIL_PASS:
        raise Exception("EMAIL_USER and EMAIL_PASS not configured in environment variables")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your Market Pit Verification Code"
    msg["From"]    = f"Market Pit <{EMAIL_USER}>"
    msg["To"]      = to_email

    html = f"""
    <div style="font-family:'Manrope',sans-serif;max-width:480px;margin:0 auto;padding:40px 20px;background:#f8faf7;">
      <div style="text-align:center;margin-bottom:32px;">
        <h2 style="font-family:'Noto Serif',serif;color:#003227;font-size:28px;margin:0;">Market Pit</h2>
        <p style="color:#707975;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin-top:4px;">Institutional Terminal</p>
      </div>
      <div style="background:#ffffff;border-radius:12px;padding:40px;box-shadow:0 4px 24px rgba(25,28,27,0.08);border:1px solid #e7e9e6;">
        <h3 style="font-family:'Noto Serif',serif;color:#003227;font-size:22px;margin:0 0 8px;">Verify Your Identity</h3>
        <p style="color:#404945;font-size:14px;line-height:1.6;margin:0 0 32px;">
          Enter this 6-digit code to access your Market Pit account. It expires in <strong>5 minutes</strong>.
        </p>
        <div style="background:#f2f4f1;border-radius:8px;padding:24px;text-align:center;margin-bottom:32px;">
          <span style="font-family:'Noto Serif',serif;font-size:40px;font-weight:700;letter-spacing:12px;color:#003227;">{otp}</span>
        </div>
        <p style="color:#707975;font-size:12px;line-height:1.6;margin:0;">
          If you didn't request this code, you can safely ignore this email. 
          Never share this code with anyone.
        </p>
      </div>
      <p style="text-align:center;color:#bfc9c4;font-size:11px;margin-top:24px;">
        © 2024 Market Pit Intelligence. Institutional Grade Security.
      </p>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, to_email, msg.as_string())


@app.route("/api/send-otp", methods=["POST"])
def api_send_otp():
    """Generate OTP, store it, send to email."""
    data  = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email or "@" not in email:
        return jsonify({"ok": False, "message": "Invalid email address"}), 400

    otp        = _generate_otp()
    expires_at = datetime.now() + timedelta(minutes=5)
    _otp_store[email] = {"otp": otp, "expires_at": expires_at}

    try:
        _send_otp_email(email, otp)
        print(f"[OTP] Sent to {email}: {otp}")
        return jsonify({"ok": True, "message": f"OTP sent to {email}"})
    except Exception as e:
        print(f"[OTP] Failed to send email: {e}")
        # For development/testing: return OTP in response if email fails
        # Remove the otp field before going live!
        return jsonify({
            "ok": False,
            "message": f"Email failed: {str(e)}. Check EMAIL_USER and EMAIL_PASS in Railway variables.",
            "debug_otp": otp  # REMOVE THIS LINE IN PRODUCTION
        }), 500


@app.route("/api/verify-otp", methods=["POST"])
def api_verify_otp():
    """Verify the OTP entered by the user."""
    data  = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    otp   = data.get("otp", "").strip()

    if not email or not otp:
        return jsonify({"ok": False, "message": "Email and OTP required"}), 400

    record = _otp_store.get(email)

    if not record:
        return jsonify({"ok": False, "message": "No OTP found for this email. Please request a new one."}), 400

    if datetime.now() > record["expires_at"]:
        del _otp_store[email]
        return jsonify({"ok": False, "message": "OTP has expired. Please request a new one."}), 400

    if record["otp"] != otp:
        return jsonify({"ok": False, "message": "Incorrect code. Please try again."}), 400

    # OTP correct — clear it and allow access
    del _otp_store[email]
    return jsonify({"ok": True, "message": "Verified successfully"})
