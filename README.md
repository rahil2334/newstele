# News Automation Assignment

An automated data pipeline and UI dashboard that fetches the top 5 news articles daily, stores them in Google Sheets, sends a summary to a Telegram channel, and visualizes the history in a modern Streamlit application with user authentication.

## Prerequisites
- **Python 3.10+**
- **A Google Account** (to use Google Sheets and Google Cloud Console)
- **A Telegram Account** (to create a bot and a channel)
- **A GitHub Account** (for automation)
- **A Guardian API Key** (optional, for live fetching fallback)

---

## Step 1: APIs Required
- **BBC News RSS**: The project uses the publicly available BBC News RSS feed (`http://feeds.bbci.co.uk/news/rss.xml`), no registration needed here.
- **The Guardian API**: Used as a real-time fallback if no Google sheets data is present for a given day in the UI dashboard. You can use the default `"test"` key for limited usage or get a free API key from [The Guardian Open Platform](https://open-platform.theguardian.com/access/).

---

## Step 2: Set up the Telegram Bot & Channel
1. Open the Telegram app and search for **@BotFather**.
2. Send the command `/newbot` and follow the prompts to create your bot. Best to set a name and a username.
3. Once completed, **BotFather** will provide an HTTP API access token. Save this as `TELEGRAM_BOT_TOKEN`.
4. Create a new **Telegram Channel** (or use an existing one).
5. Add your newly created Bot to the Channel as an **Administrator** so it can post messages.
6. To get your `TELEGRAM_CHAT_ID`:
   - Send a test message in your channel, e.g., "Hello".
   - Go to this URL in your browser: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for `"chat":{"id":-100123456789,...}` in the JSON response.
   - The number (starting with `-100`) is your `TELEGRAM_CHAT_ID`. Save it.

---

## Step 3: Set up Google Sheets
1. Go to [Google Sheets](https://sheets.google.com/) and create a new blank spreadsheet.
2. Name it (e.g., "Automated News Data").
3. You can leave it completely empty, the script will add the headers: `Date`, `Title`, `Source`, `Description`, `URL`.
4. Copy the full URL from your browser's address bar. This is your `GOOGLE_SHEET_URL`.

### Create a Google Cloud Service Account
To allow the script to write to your Sheet automatically:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project or select an existing one.
3. Navigate to **APIs & Services > Library** and enable **Google Sheets API** and **Google Drive API**.
4. Go to **APIs & Services > Credentials**.
5. Click **Create Credentials > Service Account**. Name it and skip the optional role assignments.
6. Once created, click on the Service Account edit icon > **Keys** > **Add Key** > **Create new key** > **JSON**.
7. The JSON file will download to your computer.
8. Open the downloaded JSON file. Locate the `client_email` value.
9. **Crucial Step:** Go back to your Google Sheet, click **Share**, and grant Editor access to that exact `client_email` address.
10. The entire content of that JSON file will be your `GOOGLE_CREDENTIALS_JSON`. Compact it into a single line string to use in secrets easily.

---

## Step 4: Local Testing
1. Clone this repository (or copy the files to a folder).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```env
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=-100xxxxxxxxxx
   GOOGLE_SHEET_URL=https://docs.google.com/spreadsheets/d/your-id/edit
   GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
   
   # UI Login Defaults
   LOGIN_USERNAME=admin
   LOGIN_PASSWORD=password
   
   # Guardian API (Optional)
   GUARDIAN_API_KEY=test
   ```
4. Run the fetch script manually:
   ```bash
   python fetch_news.py
   ```
   *Check your Spreadsheet and Telegram Channel!*
5. Run the Streamlit UI manually:
   ```bash
   streamlit run app.py
   ```
   *(To use `.env` with streamlit, you might need to copy `.env` to `.streamlit/secrets.toml` with the appropriate TOML format or just pass them as env variables).*

### Initial App Login
The first time you run `app.py`, you will be greeted by a Login/Signup page. 
- Use the `LOGIN_USERNAME` and `LOGIN_PASSWORD` from your `.env` to log in, OR 
- Create a new account via the Signup tab. 
- All created credentials are saved locally in a `users.json` file.

---

## Step 5: Automate with GitHub Actions
This project includes a `.github/workflows/daily_news.yml` file which runs `fetch_news.py` every day at midnight (00:00 UTC).
To activate it:
1. Push this folder to a new GitHub repository.
2. In your GitHub repository, go to **Settings > Secrets and variables > Actions**.
3. Add the following **Repository secrets**:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `GOOGLE_SHEET_URL`
   - `GOOGLE_CREDENTIALS_JSON`
4. Go to the **Actions** tab in GitHub. You can click on the **Daily News Automation** workflow and select **Run workflow** to test it right away.

---

## Step 6: Deploy Streamlit App (Optional)
To host the UI permanently:
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Login with GitHub and create a New App.
3. Select your repository and point the path to `app.py`.
4. Click **Advanced settings** and paste your secrets in the format:
   ```toml
   TELEGRAM_BOT_TOKEN = "..."
   TELEGRAM_CHAT_ID = "..."
   GOOGLE_SHEET_URL = "..."
   GOOGLE_CREDENTIALS_JSON = '{"type":"service_account",...}'
   LOGIN_USERNAME = "..."
   LOGIN_PASSWORD = "..."
   GUARDIAN_API_KEY = "..."
   ```
5. Click **Deploy**.
