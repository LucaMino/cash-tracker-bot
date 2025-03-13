# cash-tracker-bot
A Telegram bot for tracking and managing cash flow.
It automatically logs financial data and transactions into a Google Sheet and generates custom exports using OpenAI APIs.

## Examples
- **Log Expenses**  
  Simply tell the bot about your expenses, e.g.:  
  _"Today I spent 5.00 € at the bar and 2.00 € for the bus ticket."_  
  The bot will automatically record these transactions in a Google Sheet.  
- Generate Reports: You can request reports with commands like "Give me an export of all expenses for September by {category}" and the bot will generate the requested data.
- Export Data: Use the `/export` command to export the full list of transactions via CSV.

<!-- GETTING STARTED -->
## Getting Started

### Configuration
- Activate Google Sheet API
- Activate OpenAI API
- Create Telegram bot and set token on [`.env`](src/.env.example)

### Installation
1. Clone the repo
   ```sh
   git clone https://github.com/LucaMino/cash-tracker-bot.git
   ```
2. Build container
   ```sh
   docker-compose up -d --build
   ```
3. Create `.env` from [.env.example](src/.env.example)

4. Update [settings.json](src/config/settings.json) (Change categories, payment methods...)

5. Create Google sheet, rename sheet_name and setup it using command `/build_sheet`

<!-- USAGE -->
### Usage
- Possibility to set lang using `/set_lang it` or `/set_lang en` (Change default on [settings.json](src/config/settings.json))
- Possibility to customize OpenAi prompt on [OpenAIService.py](src/services/open_ai_service.py)
- Possibility to enable database storage on [settings.json](src/config/settings.json)

<!-- UTILS -->
```sh
docker-compose run script pip list
docker-compose run script pip freeze > requirements.txt
# pip list using venv
docker-compose run script /app/venv/bin/pip list
# check file using mypy
docker-compose run script /app/venv/bin/mypy /app/src/bot.py
```

<!-- LICENSE -->
### License

Distributed under the MIT License. See `LICENSE.txt` for more information.
