# Unified Email AI App

A modular Streamlit application for managing email greetings, AI-powered auto-replies, user/festival management, and Gmail webhook/watch setup.  
This app is designed for teams or individuals who want to automate and streamline their email communication and greetings using AI.

---

## 📦 Features

- **Greeting Workflow**
  - Send personalized birthday and festival greetings to users.
  - Generate professional email, SMS, and HTML card greetings using AI (OpenAI/GPT).
  - Preview and send greetings directly from the app.

- **Auto-Reply**
  - Fetch unread emails from Gmail.
  - Generate AI-powered replies for each email.
  - Save and view replies; mark emails as replied.

- **Email Logs**
  - View a searchable, filterable log of all processed emails and replies.

- **User Management**
  - Add, view, and import users (CSV supported).
  - View user details and birthdays.

- **Festival Management**
  - Add, view, and import festivals (CSV supported).
  - Assign festivals to areas for targeted greetings.

- **Gmail Watch Setup**
  - Set up Gmail push notifications to a Google Cloud Pub/Sub topic for real-time email event handling.

---

## 🚀 Getting Started

### 1. **Clone the Repository**

```bash
git clone https://github.com/yourusername/yourrepo.git
cd yourrepo/email-sms
```

### 2. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 3. **Prepare Credentials**

- Place your `credentials.json` (OAuth client) in the `email-sms/` directory.
- Place your Gmail service account JSON if needed.
- Set up `.streamlit/secrets.toml` for sensitive keys:

```toml
OPENAI_API_KEY = "sk-..."
GMAIL_USER = "your_email@gmail.com"
GMAIL_APP_PASSWORD = "your_app_password"
```

### 4. **Initialize the Database**

The database is auto-initialized on first run.  
You can import users and festivals via CSV from the UI.

### 5. **Run the App**

```bash
streamlit run main.py
```

---

## 🖥️ App Navigation

- **Greeting Workflow:**  
  Send and preview AI-generated greetings for birthdays and festivals.

- **Auto-Reply:**  
  View unread emails, generate and save AI replies.

- **Email Logs:**  
  Browse all processed emails and replies.

- **Manage Users:**  
  Add, import, and view users.

- **Manage Festivals:**  
  Add, import, and view festivals.

- **Gmail Watch Setup:**  
  Configure Gmail push notifications to a Pub/Sub topic.

---

## 🛠️ Modules Overview

- `modules/ai.py`  
  All AI prompt, chain, and reply/greeting logic.

- `modules/db.py`  
  Database setup and CRUD for users, emails, logs, and festivals.

- `modules/gmail.py`  
  Gmail API authentication, fetch, send, and mark-as-read helpers.

- `modules/greetings.py`  
  Greeting workflow UI and logic.

- `modules/auto_reply.py`  
  Auto-reply UI and logic.

- `modules/gmail_watch.py`  
  Gmail watch (push notification) setup UI and logic.

- `modules/webhook.py`  
  Flask webhook for Gmail push notifications (optional, run separately).

---

## ⚡ Tips

- **Credentials:**  
  Never commit your credentials or secrets to git. Use `.gitignore` and `.streamlit/secrets.toml`.

- **Gmail API:**  
  The first time you use Gmail features, a browser window will open for OAuth authentication.

- **OpenAI API:**  
  Make sure your OpenAI API key is valid and has quota.

- **Database:**  
  All data is stored in `emails.db` in the app directory.

---

## 🧩 Extending

- Add more AI chains or prompts in `modules/ai.py`.
- Add new sidebar pages by creating new modules and updating `main.py`.
- Integrate with other email providers or notification systems as needed.

---

## 📝 License

MIT License

---

## 🙋 FAQ

**Q: How do I add users or festivals?**  
A: Use the "Manage Users" or "Manage Festivals" pages. You can add manually or import via CSV.

**Q: How do I set up Gmail push notifications?**  
A: Use the "Gmail Watch Setup" page and follow the instructions for your Google Cloud Pub/Sub topic.

**Q: Can I run the webhook server and Streamlit at the same time?**  
A: Yes, but the webhook server (`modules/webhook.py`) must be run separately (e.g., `python modules/webhook.py`).

---

## 📬 Support

For issues or feature requests, open an issue on