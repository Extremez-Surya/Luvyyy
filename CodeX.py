# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                  ║
# ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
# ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
# ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
# ║                                                                  ║
# ║            © 2026 Vinay Kumar (!Alone💔) — All Rights Reserved              ║
# ║                                                                  ║
# ║   discord  ──  https://discord.com/users/731390792567881739                      ║
# ║   youtube  ──  https://discord.com/users/731390792567881739                   ║
# ║   github   ──  https://github.com/kumar_vinay                        ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
import sys
import subprocess

if sys.platform == "win32":
    if sys.stdout:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if sys.stderr:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def sanitize_json_databases():
    """Ensure all JSON files in jsondb/ are valid UTF-8 and not corrupted with UTF-16 BOM."""
    if not os.path.isdir("jsondb"):
        os.makedirs("jsondb", exist_ok=True)
        return

    import json
    for root, _, files in os.walk("jsondb"):
        for f in files:
            if f.endswith(".json"):
                p = os.path.join(root, f)
                try:
                    with open(p, "rb") as fb:
                        content = fb.read()

                    if not content or content.startswith(b"\xff\xfe") or content.startswith(b"\xfe\xff") or not content.strip():
                        print(f"[Sanitize] Self-healed non-UTF8/empty file {p} to clean UTF-8 {{}}")
                        with open(p, "w", encoding="utf-8") as fw:
                            fw.write("{}")
                    else:
                        try:
                            json.loads(content.decode("utf-8-sig"))
                        except Exception:
                            try:
                                fixed = json.loads(content.decode("utf-16"))
                                with open(p, "w", encoding="utf-8") as fw:
                                    json.dump(fixed, fw, indent=2)
                                print(f"[Sanitize] Converted UTF-16 {p} to clean UTF-8")
                            except Exception:
                                with open(p, "w", encoding="utf-8") as fw:
                                    fw.write("{}")
                                print(f"[Sanitize] Self-healed corrupted {p} to clean UTF-8 {{}}")
                except Exception as e:
                    pass

def auto_git_update():
    """Sync latest changes from GitHub if running in a git repo, or initialize git if missing."""
    repo_url = "https://github.com/Extremez-Surya/Luvyyy.git"
    try:
        if not os.path.exists(".git"):
            print("[AutoUpdate] .git folder missing. Initializing git link to GitHub...")
            subprocess.run(["git", "init"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            subprocess.run(["git", "remote", "add", "origin", repo_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            subprocess.run(["git", "fetch", "origin", "main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
            subprocess.run(["git", "reset", "--hard", "origin/main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            print("[AutoUpdate] Initialized git repo and synced with origin/main successfully!")
            return
        res = subprocess.run(["git", "pull", "--no-rebase", "origin", "main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        out = (res.stdout + " " + res.stderr).strip()
        if "Already up to date" not in out and out:
            print(f"[AutoUpdate] Git sync result: {out}")
    except Exception:
        pass

# Run database sanitation and auto-git check immediately
sanitize_json_databases()
auto_git_update()

# os.system("")
import asyncio
import traceback
from threading import Thread
from datetime import datetime
import random
import time

import aiohttp
import discord
from discord import Spotify
from discord.ext import commands, tasks

from core import Context
from core.Cog import Cog
from core.zyrox import zyrox
from utils.Tools import *
from utils.config import *
from utils.emoji import SUCCESS, ERROR, TICK, CROSS, REACTION_TEST_EMOJIS
from utils.sync_emojis import run_sync

import jishaku
import cogs


os.environ["JISHAKU_NO_DM_TRACEBACK"] = "False"
os.environ["JISHAKU_HIDE"] = "True"
os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_FORCE_PAGINATOR"] = "True"

from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv("TOKEN")

# --- Configuration ---
# IMPORTANT: Replace these with your actual channel IDs.
SERVER_COUNT_CHANNEL_ID = 1419729255977189467  # Replace with your server count channel ID
USER_COUNT_CHANNEL_ID = 1419729283861184632    # Replace with your user count channel ID
LOG_CHANNEL_ID = 1396794297386532978 # Replace with the channel ID for join/leave logs


client = zyrox()
tree = client.tree

# --- Background Task for Stats ---
async def update_stats():
    """A background task to update server and user stats in channel names."""
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            servers = len(client.guilds)
            users = sum(guild.member_count for guild in client.guilds if guild.member_count is not None)
            
            server_channel = client.get_channel(SERVER_COUNT_CHANNEL_ID)
            user_channel = client.get_channel(USER_COUNT_CHANNEL_ID)
            
            if server_channel:
                await server_channel.edit(name=f"Servers: {servers}")
            
            if user_channel:
                await user_channel.edit(name=f"Users: {users}")
                
        except Exception as e:
            print(f"Error updating stats: {e}")
        
        await asyncio.sleep(600) # Update every 10 minutes

# --- Event Handlers ---
@client.event
async def on_ready():
    await client.wait_until_ready()
    
    print("""
        \033[1;31m
 ██████╗ ██████╗ ██████╗ ███████╗██╗  ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝
██║     ██║   ██║██║  ██║█████╗   ╚███╔╝ 
██║     ██║   ██║██║  ██║██╔══╝   ██╔██╗ 
╚██████╗╚██████╔╝██████╔╝███████╗██╔╝ ██╗
 ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
        \033[0m
       """)
    print("Loaded & Online!")
    print(f"Logged in as: {client.user}")
    print(f"Connected to: {len(client.guilds)} guilds")
    print(f"Connected to: {len(client.users)} users")

    # Sync application emojis on startup
    await run_sync(TOKEN)

    async def sync_commands():
        try:
            synced = await client.tree.sync()
            all_commands = list(client.commands)
            print(f"Synced Total {len(all_commands)} Client Commands and {len(synced)} Slash Commands")
        except Exception as e:
            print(f"Error syncing command tree: {e}")

    async def init_persistence():
        try:
            from utils.persistence import get_current_system_stats, restore_from_cloud, create_backup
            stats = get_current_system_stats()
            if stats["total_records"] == 0:
                print("\033[33m[Persistence] 🔍 Empty local database detected on startup. Checking Discord cloud for backup...\033[0m")
                restored = await restore_from_cloud(client)
                if restored:
                    print("\033[32m[Persistence] ✅ Successfully recovered databases from Discord cloud!\033[0m")
            create_backup("startup")
        except Exception as e:
            print(f"[Persistence] Startup persistence check warning: {e}")

    client.loop.create_task(sync_commands())
    client.loop.create_task(update_stats())
    client.loop.create_task(init_persistence())


@client.event
async def on_guild_join(guild: discord.Guild):
    # Log when the bot joins a server
    log_channel = client.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(f"{BRAND_NAME} has been added to the server: **{guild.name}** (ID: `{guild.id}`)")

@client.event
async def on_command_completion(context: commands.Context) -> None:
    if context.author.id in OWNER_IDS:
        return

    full_command_name = context.command.qualified_name
    split = full_command_name.split("\n")
    executed_command = str(split[0])
    webhook_url = CMD_WEBHOOK_URL
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)

        embed_color = 0xFF0000
        embed = discord.Embed(color=embed_color)
        avatar_url = context.author.display_avatar.url

        embed.set_author(name=f"Cmd Executed: {executed_command}", icon_url=avatar_url)
        embed.set_thumbnail(url=avatar_url)

        if context.guild is not None:
            embed.add_field(name="User", value=f"{context.author.mention} (`{context.author.id}`)", inline=False)
            embed.add_field(name="Server", value=f"{context.guild.name} (`{context.guild.id}`)", inline=False)
            embed.add_field(name="Channel", value=f"{context.channel.mention} (`{context.channel.id}`)", inline=False)
        else:
            embed.add_field(name="User (DM)", value=f"{context.author.mention} (`{context.author.id}`)", inline=False)
        
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=f"{BRAND_NAME} Development™ ❤️", icon_url=client.user.display_avatar.url)
        
        try:
            await webhook.send(embed=embed)
        except Exception as e:
            print(f'Command log webhook failed: {e}')


# --- Utility Commands ---
@client.command(name='spotify')
async def spotify(ctx: Context, user: discord.Member = None):
    """Shows what a user is listening to on Spotify."""
    user = user or ctx.author
    spotify_activity = next((activity for activity in user.activities if isinstance(activity, Spotify)), None)

    if not spotify_activity:
        return await ctx.send(f"{user.name} is not listening to Spotify.")
    
    embed = discord.Embed(
        title=f"{user.name}'s Spotify",
        description=f"**Listening to:** {spotify_activity.title}",
        color=0x1DB954 # Spotify Green
    )
    embed.set_thumbnail(url=spotify_activity.album_cover_url)
    embed.add_field(name="Artist", value=spotify_activity.artist)
    embed.add_field(name="Album", value=spotify_activity.album)
    embed.set_footer(text=f"Song started at {spotify_activity.created_at.strftime('%H:%M')}")
    await ctx.send(embed=embed)


@client.command(name='makeinvite', aliases=['createinvite', 'makeinv'])
@commands.is_owner()
async def make_invite(ctx: Context, guild_id: int = None):
    """Creates an invite for a specified server (owner only)."""
    if guild_id is None:
        return await ctx.send("Please provide a Guild ID.")
        
    guild = client.get_guild(guild_id)
    if not guild:
        return await ctx.send("Invalid Guild ID. I am not in that server.")

    if guild.system_channel and guild.system_channel.permissions_for(guild.me).create_instant_invite:
        try:
            invite = await guild.system_channel.create_invite(max_age=0, max_uses=0, unique=True, reason="Owner requested invite.")
            return await ctx.send(f"Invite for **{guild.name}**:\n{invite.url}")
        except Exception:
            pass

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).create_instant_invite:
            try:
                invite = await channel.create_invite(max_age=0, max_uses=0, unique=True, reason="Owner requested invite.")
                return await ctx.send(f"Invite for **{guild.name}** (from #{channel.name}):\n{invite.url}")
            except Exception:
                continue
                
    await ctx.send(f"I don't have 'Create Instant Invite' permission in any channel in **{guild.name}**.")


# --- Webhook Management Commands ---
@client.command(name='create_hook', aliases=['makehook'])
@commands.has_permissions(administrator=True)
async def create_hook(ctx: Context, *, name: str = None):
    """Creates a webhook in the current channel."""
    if name is None:
        return await ctx.send("Please provide a name for the webhook.")
    
    try:
        webhook = await ctx.channel.create_webhook(name=name, reason=f"Created by {ctx.author}")
        embed = discord.Embed(
            title=f"{SUCCESS} Webhook Created",
            description=f"A webhook named **{webhook.name}** was created.",
            color=0xFF0000
        )
        await ctx.author.send(f"Webhook URL for **{webhook.name}** in **{ctx.channel.name}**:\n||{webhook.url}||", embed=embed)
        await ctx.send("Webhook created. I've sent the URL to your DMs.")
    except discord.Forbidden:
        await ctx.send("I don't have permission to create webhooks here.")
    except Exception:
        await ctx.send(f"Webhook created: **{webhook.name}**\n||{webhook.url}||\n(I could not DM you the URL.)")


@client.command(name='delete_hook', aliases=['delhook'])
@commands.has_permissions(administrator=True)
async def delete_hook(ctx: Context, webhook_url: str = None):
    """Deletes a webhook using its URL."""
    if webhook_url is None:
        return await ctx.send("Please provide the webhook URL to delete.")

    try:
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(webhook_url, session=session)
            await webhook.delete(reason=f"Deleted by {ctx.author}")
        await ctx.send(f"{SUCCESS} Webhook deleted successfully.")
    except (discord.NotFound, ValueError):
        await ctx.send(f"{ERROR} Webhook not found or URL is invalid.")


@client.command(name='list_hooks', aliases=['hooks'])
@commands.has_permissions(administrator=True)
async def list_hooks(ctx: Context):
    """Lists all webhooks in the current channel."""
    try:
        webhooks = await ctx.channel.webhooks()
        if not webhooks:
            return await ctx.send("No webhooks found in this channel.")

        embed = discord.Embed(title=f"Webhooks in #{ctx.channel.name}", color=0xFF0000)
        description = "\n".join([f"**Name:** {wh.name} | **ID:** `{wh.id}`" for wh in webhooks])
        embed.description = description
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I don't have permission to view webhooks in this channel.")


# --- Game Command ---
@client.command()
async def reaction(ctx: Context):
    """See how fast you can react to the correct emoji."""
    emojis = ["🍪", "🎉", "🧋", "🍒", "🍑", "💸", "🌙", "💕"]
    correct_emoji = random.choice(emojis)
    random.shuffle(emojis)
    
    embed = discord.Embed(
        title="Reaction Test",
        description="I will show an emoji in a few seconds. Get ready to click it!",
        color=0xFF0000
    )
    message = await ctx.send(embed=embed)
    
    for emoji in emojis:
        await message.add_reaction(emoji)
        
    await asyncio.sleep(random.uniform(2.0, 7.0))
    
    embed.description = f"**GET THE {correct_emoji} EMOJI!**"
    await message.edit(embed=embed)
    start_time = time.time()

    def check(reaction, user):
        return (
            reaction.message.id == message.id
            and str(reaction.emoji) == correct_emoji
            and user == ctx.author
        )

    try:
        reaction, user = await client.wait_for("reaction_add", timeout=15.0, check=check)
        end_time = time.time()
        reaction_time = end_time - start_time
        
        embed.description = f"{user.mention} got the {correct_emoji} in **{reaction_time:.2f} seconds**!"
        await message.edit(embed=embed)
    except asyncio.TimeoutError:
        embed.description = "Timeout! You were too slow."
        await message.edit(embed=embed)


# --- Web Server for 24/7 Keep-Alive & Health Check (Render.com) ---
# --- Optional Web Server for Keep-Alive & Health Check (Render.com) ---
API_ENABLED = os.getenv("API_ENABLED", "false").strip().lower() == "true"

def keep_alive():
    if not API_ENABLED:
        return
    try:
        import uvicorn
        from threading import Thread
        from api.server import create_app
        from api.dependencies import set_bot

        fastapi_app = create_app()
        fastapi_app.state.bot = client
        set_bot(client)

        API_PORT = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

        def run_api():
            try:
                uvicorn.run(fastapi_app, host='0.0.0.0', port=API_PORT, log_level="warning")
            except Exception as e:
                print(f"\033[31m◈ Web Server Error: {e}\033[0m")

        print(f"\033[32m◈ Web Server (Keep-Alive): Starting on port {API_PORT}\033[0m")
        server = Thread(target=run_api, daemon=True)
        server.start()
    except ImportError:
        pass
    except Exception as e:
        print(f"\033[31m◈ Web Server Startup Error: {e}\033[0m")

keep_alive()

async def cleanup_client_session(bot):
    try:
        if not bot.is_closed():
            await bot.close()
    except Exception:
        pass
    try:
        session = getattr(bot.http, "_HTTPClient__session", None)
        if session and not session.closed:
            await session.close()
    except Exception:
        pass
    bot.http.connector = discord.utils.MISSING

def extract_retry_after(error: discord.HTTPException) -> float:
    # 1. Check HTTP response header 'Retry-After'
    try:
        if hasattr(error, "response") and error.response is not None:
            val = error.response.headers.get("Retry-After")
            if val:
                return float(val)
    except Exception:
        pass

    # 2. Check JSON response body {"retry_after": ...}
    try:
        if hasattr(error, "text") and error.text:
            parsed = json.loads(error.text)
            if isinstance(parsed, dict) and "retry_after" in parsed:
                return float(parsed["retry_after"])
    except Exception:
        pass

    return 0.0

# --- Main Bot Execution ---
async def main():
    os.system("cls" if os.name == "nt" else "clear")

    try:
        await client._async_setup_hook()
    except Exception as e:
        print(f"[CodeX] Setup hook warning: {e}")

    try:
        await client.load_extension("jishaku")
    except commands.ExtensionAlreadyLoaded:
        pass
    except Exception as e:
        print(f"[CodeX] Jishaku status: {e}")

    if not TOKEN or not TOKEN.strip():
        print("\033[31m[CodeX] ❌ ERROR: 'TOKEN' environment variable is missing or empty! Please set TOKEN in your .env or environment variables.\033[0m")
        while True:
            await asyncio.sleep(3600)

    attempt = 0
    try:
        while True:
            try:
                print(f"\033[36m[CodeX] 🚀 Connecting to Discord Gateway (Attempt {attempt + 1})...\033[0m")
                await client.start(TOKEN.strip())
                print(f"\033[33m[CodeX] ⚠️ Bot connection finished or disconnected. Reconnecting in 5s...\033[0m")
                await cleanup_client_session(client)
                attempt += 1
                await asyncio.sleep(5)
            except discord.errors.PrivilegedIntentsRequired:
                print("\033[31m[CodeX] ❌ Privileged Gateway Intents (Presences/Members) are not enabled in Discord Developer Portal!\033[0m")
                print("\033[33m[CodeX] 🔄 Falling back to standard default intents (Default + Message Content) so bot can come online...\033[0m")
                client.intents = discord.Intents.default()
                client.intents.message_content = True
                await cleanup_client_session(client)
                attempt += 1
                await asyncio.sleep(3)
            except discord.HTTPException as e:
                if e.status == 429: # Rate Limited (Discord or Cloudflare 1015)
                    retry_after = extract_retry_after(e)
                    if retry_after > 0:
                        wait_time = retry_after + 2.0
                        print(f"\033[33m[CodeX] ⚠️ Discord Rate Limit: Discord requested Retry-After {retry_after}s. Waiting {wait_time:.1f}s before reconnecting...\033[0m")
                    else:
                        backoff = min(30 * (2 ** min(attempt, 4)), 300)
                        wait_time = backoff + random.uniform(2.0, 5.0)
                        sample = (e.text or str(e))[:200].replace('\n', ' ')
                        print(f"\033[33m[CodeX] ⚠️ Shared IP / Gateway Rate Limited (HTTP 429). Response: {sample}\033[0m")
                        print(f"\033[33m[CodeX] Backing off for {wait_time:.1f}s to allow the rate limit bucket to clear...\033[0m")

                    await cleanup_client_session(client)
                    attempt += 1
                    await asyncio.sleep(wait_time)
                elif e.status == 401:
                    print("\033[31m[CodeX] ❌ Invalid Discord Bot Token (HTTP 401 Unauthorized)! Please verify your TOKEN.\033[0m")
                    while True:
                        await asyncio.sleep(3600)
                else:
                    print(f"\033[31m[CodeX] Discord HTTP Error {e.status}: {e}\033[0m")
                    await cleanup_client_session(client)
                    attempt += 1
                    await asyncio.sleep(15)
            except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                print(f"\033[33m[CodeX] Network connection error: {e}. Retrying in 10s...\033[0m")
                await cleanup_client_session(client)
                attempt += 1
                await asyncio.sleep(10)
            except Exception as e:
                print(f"\033[31m[CodeX] Unexpected error during bot execution: {e}\033[0m")
                traceback.print_exc()
                await cleanup_client_session(client)
                attempt += 1
                await asyncio.sleep(15)
    finally:
        try:
            from utils.persistence import create_backup
            create_backup("bot_shutdown")
            print("\033[32m[Persistence] 💾 Saved shutdown database snapshot to data_backup/latest_backup.zip\033[0m")
        except Exception:
            pass

        if not client.is_closed():
            print("\033[33m[CodeX] Closing Discord connection cleanly...\033[0m")
            try:
                await client.close()
            except Exception:
                pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\033[33m[CodeX] Process terminated. Goodbye!\033[0m")
