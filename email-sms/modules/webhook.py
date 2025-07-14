from flask import Flask, request, jsonify
import hmac
import hashlib
import os

app = Flask(__name__)

# Optional: Set a secret for webhook verification
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "changeme")

@app.route("/gmail-webhook", methods=["POST"])
def gmail_webhook():
    # Optional: Verify webhook signature if you set up one
    # signature = request.headers.get("X-Hub-Signature")
    # if not verify_signature(request.data, signature):
    #     return "Invalid signature", 403

    data = request.get_json()
    # Process the webhook data (e.g., Gmail push notification)
    # You can trigger your auto-reply logic here or flag the DB for Streamlit to process

    # Example: Just print and acknowledge
    print("Received webhook:", data)
    return jsonify({"status": "received"}), 200

# Optional: Signature verification function
def verify_signature(payload, signature):
    mac = hmac.new(WEBHOOK_SECRET.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)