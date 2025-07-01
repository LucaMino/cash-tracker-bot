# 💰 cash-tracker-bot

**cash-tracker-bot** is a lightweight Telegram bot that helps you track your personal expenses with natural language input — directly from Telegram.

Log expenses like “Yesterday I spent 10.50 by card for the taxi” — the bot automatically parses the amount, assigns a category and payment method, and stores the entry, syncing to Google Sheets by default, with optional Supabase integration.

---

## ✨ Features

- 📝 Log expenses via Telegram using natural language
- 🔒 Private and secure — works in 1:1 chat
- ☁️ Supports Google Sheets and Supabase for data storage
- 🤖 AI-powered custom export: request data exports with filters and date ranges using natural language (e.g., "Export only groceries from June")
- 📤 Export all logged expenses as CSV via `/export`
- 🌐 Multi-language support (`/set_lang it`, `/set_lang en`)

---

## 🚀 Getting Started

### ⚙️ Configuration

1. Activate the **Google Sheets API** via [Google Cloud Console](https://console.cloud.google.com/)
2. Activate your **Telegram Bot** by creating it with [@BotFather](https://t.me/BotFather) and get the token
3. Activate your **OpenAI API key** from the [OpenAI platform](https://platform.openai.com/account/api-keys)
4. (Optional) Activate a **Supabase** database for persistent storage

---

### 🧪 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/LucaMino/cash-tracker-bot.git
   ```
2. Create `.env` from [.env.example](src/.env.example)
3. Update [settings.json](src/config/settings.json) (Change categories, payment methods...)
4. Build container:
   ```bash
   docker-compose up -d --build
   ```
5. Create Google sheet, rename sheet_name and setup it using command `/build_sheet`

---

## 🛠️ Utils

```sh
fly deploy
fly ssh console --app kickoff-sync  // open an SSH console to your app
docker-compose run script pip list
docker-compose run script pip freeze > requirements.txt
```

<!-- LICENSE -->
### License

Distributed under the MIT License. See `LICENSE.txt` for more information.
