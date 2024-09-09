# cash-tracker-bot
A Telegram bot integrated with OpenAI APIs for tracking and managing your cash flow. Automatically logs financial data and transactions into a Google Sheet, making budgeting and expense tracking seamless and efficient.

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

4. Update [settings.json](src/config/settings.json)

5. Create Google sheet and setup it using command `/build_sheet`

<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.