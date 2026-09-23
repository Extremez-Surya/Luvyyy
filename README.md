<div align="center">

```
██╗     ██╗   ██╗██╗   ██╗██╗   ██╗██╗   ██╗
██║     ██║   ██║██║   ██║╚██╗ ██╔╝╚██╗ ██╔╝
██║     ██║   ██║██║   ██║ ╚████╔╝  ╚████╔╝ 
██║     ██║   ██║╚██╗ ██╔╝  ╚██╔╝    ╚██╔╝  
███████╗╚██████╔╝ ╚████╔╝    ██║      ██║   
╚══════╝ ╚═════╝   ╚═══╝     ╚═╝      ╚═╝   
```

<h3>Luvyyy Discord Bot — All-in-One Discord Bot</h3>

<p>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white"/></a>
  <a href="https://discordpy.readthedocs.io"><img src="https://img.shields.io/badge/Discord.py-v2-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://render.com"><img src="https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-red?style=for-the-badge"/></a>
</p>
<p>
  <a href="https://discord.com/users/731390792567881739"><img src="https://img.shields.io/badge/Developer-Vinay_Kumar-5865F2?style=for-the-badge&logo=discord&logoColor=white"/></a>
  <a href="https://github.com/kumar_vinay"><img src="https://img.shields.io/badge/GitHub-kumar_vinay-181717?style=for-the-badge&logo=github&logoColor=white"/></a>
</p>

</div>

---

## ✦ Project Overview

**Luvyyy** is an advanced, production-grade Discord Bot built using `discord.py v2` with high-performance voice/music (Lavalink v4 & Wavelink), antinuke security, automod, moderation, games, leveling, utility, and an integrated keep-alive healthcheck server for **24/7 hosting on Render.com**.

```
Zyrox/
├── cogs/
│   ├── antinuke/          Antinuke security protection
│   ├── automod/           Automod enforcement event listeners
│   ├── commands/          260+ Client & 89 Slash command modules
│   ├── events/            Discord event listeners & handlers
│   ├── moderation/        Moderation action modules
│   └── zyrox/             Core feature cogs
├── core/                  Bot client, Context, Cog base classes
├── games/                 Interactive button games (wordle, chess, rps, etc.)
├── utils/                 Emoji, tools, paginators, cv2 views
├── assets/                Fonts, backgrounds, assets
├── api/                   Built-in healthcheck & status server
├── CodeX.py               Main entry point
├── render.yaml            Render 1-click Blueprint deployment spec
├── runtime.txt            Python 3.11.9 runtime spec for Render
└── requirements.txt       Clean, Linux-optimized Python dependencies
```

---

## ✦ Deploying 24/7 on Render.com (Full Guide)

Render gives you a **Free Web Service** that can run this bot 24/7! Follow these simple steps:

### Method 1: One-Click Deploy via Blueprint (`render.yaml`)

1. **Push your code to GitHub:**
   Make sure this repository is on your GitHub account (Public or Private).
2. **Go to Render:**
   Open [dashboard.render.com](https://dashboard.render.com) and log in.
3. **Create New Blueprint:**
   Click **New +** (top right) ➔ **Blueprint**.
4. **Connect Repository:**
   Select this GitHub repository. Render will automatically read `render.yaml`!
5. **Set Secret Variables:**
   Render will ask you for `TOKEN`:
   - Paste your Discord Bot Token.
6. **Click Apply / Deploy!**
   Render will install dependencies and start your bot.

---

### Method 2: Manual Web Service Setup on Render

If you prefer to configure manually:

1. In Render Dashboard, click **New +** ➔ **Web Service**.
2. Connect your GitHub repository.
3. Configure the following fields:
   - **Name:** `luvyyy-bot`
   - **Environment:** `Python 3`
   - **Region:** Any (e.g. `Oregon` or `Frankfurt`)
   - **Branch:** `main` (or `master`)
   - **Root Directory:** *(leave blank / empty)*
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python CodeX.py`
   - **Instance Type:** `Free`
4. Expand **Advanced** ➔ **Health Check Path**:
   - Set to: `/health`
5. Under **Environment Variables**, add:
   - `TOKEN` = `your_discord_bot_token`
   - `OWNER_IDS` = `731390792567881739`
   - `brand_name` = `Luvyyy`
   - `LAVALINK_HOST` = `lavalink.serenetia.com`
   - `LAVALINK_PASSWORD` = `youshallnotpass`
   - `LAVALINK_SECURE` = `true`
   - `LAVALINK_PORT` = `443`
   - `EMOJI_SYNC` = `false`
   - `API_ENABLED` = `true`
   - `PYTHON_VERSION` = `3.11.9`
6. Click **Create Web Service**.

---

## ✦ Keeping Bot Online 24/7 for Free (UptimeRobot / Cron)

Render's Free Web Services go to sleep after 15 minutes if there are no HTTP requests. Because **Luvyyy** has a built-in healthcheck server listening on `$PORT`, you can keep it awake forever using a free pinger:

1. Copy your Render Web Service URL from the top of your Render service page:
   `https://luvyyy-bot.onrender.com`
2. Go to [uptimerobot.com](https://uptimerobot.com) (free) or [cron-job.org](https://cron-job.org).
3. Create a **New Monitor**:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `Luvyyy Bot Keepalive`
   - **URL (or IP):** `https://luvyyy-bot.onrender.com/health`
   - **Monitoring Interval:** `Every 5 minutes`
4. Save the monitor.
5. **Done!** UptimeRobot will ping `/health` every 5 minutes. Render will never sleep, keeping your Discord bot online **24/7/365**!

---

## ✦ Local Development

To run the bot locally on your computer:

```bash
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Create your .env file
# (Copy from .env.example and add your BOT TOKEN)

# 5. Start the bot
python CodeX.py
```

---

## ✦ Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `TOKEN` | — | Discord Bot Token from Discord Developer Portal |
| `OWNER_IDS` | `731390792567881739` | Comma-separated Discord User IDs of bot owners |
| `brand_name` | `Luvyyy` | Display name of the bot across embeds and messages |
| `LAVALINK_HOST` | `lavalink.serenetia.com` | Active Lavalink v4 server hostname |
| `LAVALINK_PASSWORD`| `youshallnotpass` | Lavalink password |
| `LAVALINK_SECURE`| `true` | `true` for HTTPS/WSS, `false` for HTTP/WS |
| `LAVALINK_PORT` | `443` | Lavalink port |
| `API_ENABLED` | `true` | Enables the internal 24/7 keep-alive & health check server |
| `PORT` | `8000` | Port for the health check web server (Render sets this dynamically) |

---

## ✦ Developers & Support

- **Developers:** Vinay Kumar (`!Alone💔`) & Surya (`Extremez`)
- **Discord:** [kumar_vinay](https://discord.com/users/731390792567881739) & [Surya](https://discord.com/users/984409270344908872)
- **GitHub:** [kumar_vinay](https://github.com/kumar_vinay) & [Extremez-Surya](https://github.com/Extremez-Surya)
