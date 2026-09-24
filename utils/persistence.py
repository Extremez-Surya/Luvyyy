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

from __future__ import annotations
import os
import sys
import json
import time
import shutil
import zipfile
import sqlite3
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

BACKUP_ROOT = os.path.abspath("data_backup")
LATEST_BACKUP = os.path.join(BACKUP_ROOT, "latest_backup.zip")
HISTORY_DIR = os.path.join(BACKUP_ROOT, "history")
MANIFEST_FILE = os.path.join(BACKUP_ROOT, "manifest.json")
CONFIG_FILE = os.path.join(BACKUP_ROOT, "backup_config.json")

# Ensure required backup directories exist
os.makedirs(BACKUP_ROOT, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_tracked_data_paths() -> List[str]:
    """Find all database files and persistent data files that must be protected."""
    paths = []
    # 1. db/ directory
    if os.path.isdir("db"):
        for root, _, files in os.walk("db"):
            for f in files:
                if f.endswith((".db", ".sqlite", ".sqlite3", ".json")):
                    paths.append(os.path.normpath(os.path.join(root, f)))
    # 2. jsondb/ directory
    if os.path.isdir("jsondb"):
        for root, _, files in os.walk("jsondb"):
            for f in files:
                if f.endswith(".json"):
                    paths.append(os.path.normpath(os.path.join(root, f)))
    # 3. Root level databases
    for f in os.listdir("."):
        if f.endswith((".db", ".sqlite", ".sqlite3")) and os.path.isfile(f):
            paths.append(os.path.normpath(f))
    return sorted(list(set(paths)))

def get_database_record_count(db_path: str) -> int:
    """Safely count all rows across all user tables in a SQLite database."""
    if not os.path.isfile(db_path) or not db_path.endswith((".db", ".sqlite", ".sqlite3")):
        return 0
    total = 0
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [t[0] for t in cur.fetchall()]
        for table in tables:
            try:
                cur.execute(f"SELECT COUNT(*) FROM \"{table}\";")
                row = cur.fetchone()
                if row:
                    total += row[0]
            except Exception:
                pass
        conn.close()
    except Exception:
        pass
    return total

def get_current_system_stats() -> Dict[str, Any]:
    """Compute statistics for current live data."""
    paths = get_tracked_data_paths()
    total_records = 0
    db_stats = {}
    for p in paths:
        if p.endswith((".db", ".sqlite", ".sqlite3")):
            count = get_database_record_count(p)
            total_records += count
            db_stats[p] = count
        elif p.endswith(".json"):
            try:
                with open(p, "r", encoding="utf-8") as jf:
                    data = json.load(jf)
                    count = len(data) if isinstance(data, (list, dict)) else 1
                    total_records += count
                    db_stats[p] = count
            except Exception:
                db_stats[p] = 0

    return {
        "files_count": len(paths),
        "total_records": total_records,
        "details": db_stats,
        "timestamp": time.time(),
        "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def create_backup(reason: str = "auto") -> tuple[str, Dict[str, Any]]:
    """
    Creates a full backup zip containing all databases and state files.
    Returns: (path_to_zip, stats_dict)
    """
    paths = get_tracked_data_paths()
    stats = get_current_system_stats()
    stats["reason"] = reason

    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    history_filename = f"backup_{timestamp_str}_{reason}.zip"
    history_path = os.path.join(HISTORY_DIR, history_filename)

    # Temporary zip creation to ensure atomic write
    temp_zip = os.path.join(BACKUP_ROOT, "temp_backup.zip")
    with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in paths:
            if os.path.isfile(file_path):
                try:
                    zf.write(file_path, arcname=file_path.replace("\\", "/"))
                except Exception as e:
                    print(f"[Persistence] Warning writing {file_path} to backup: {e}")
        
        # Also store manifest inside the zip
        manifest_data = json.dumps(stats, indent=2)
        zf.writestr("backup_manifest.json", manifest_data)

    # Move to latest_backup.zip
    shutil.copyfile(temp_zip, LATEST_BACKUP)
    shutil.move(temp_zip, history_path)

    # Save manifest outside
    with open(MANIFEST_FILE, "w", encoding="utf-8") as mf:
        json.dump(stats, mf, indent=2)

    # Rotate history: keep only last 5 snapshots to save disk
    try:
        backups = sorted(
            [os.path.join(HISTORY_DIR, f) for f in os.listdir(HISTORY_DIR) if f.endswith(".zip")],
            key=os.path.getmtime
        )
        while len(backups) > 5:
            oldest = backups.pop(0)
            os.remove(oldest)
    except Exception:
        pass

    return LATEST_BACKUP, stats

def restore_backup(zip_path: Optional[str] = None, force: bool = False) -> bool:
    """
    Restores all databases from a backup zip file.
    If zip_path is None, restores from LATEST_BACKUP.
    """
    target_zip = zip_path or LATEST_BACKUP
    if not os.path.isfile(target_zip):
        print(f"[Persistence] [ERROR] Restore target not found: {target_zip}")
        return False

    print(f"[Persistence] [*] Restoring databases from {target_zip}...")
    try:
        with zipfile.ZipFile(target_zip, "r") as zf:
            for item in zf.infolist():
                if item.filename == "backup_manifest.json":
                    continue
                # Make sure directories exist
                dest_path = os.path.normpath(item.filename)
                os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
                
                # Write file safely
                with zf.open(item) as src, open(dest_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
        
        print(f"[Persistence] [OK] Database restore completed successfully from {target_zip}!")
        return True
    except Exception as e:
        print(f"[Persistence] [ERROR] Error during database restore: {e}")
        return False

def auto_restore_if_needed() -> bool:
    """
    Checks if current databases are missing, empty, or have fewer records than the latest backup.
    If so, automatically restores from the backup!
    Returns True if restore was performed, False otherwise.
    """
    if not os.path.isfile(LATEST_BACKUP):
        return False

    current_stats = get_current_system_stats()
    
    backup_records = 0
    if os.path.isfile(MANIFEST_FILE):
        try:
            with open(MANIFEST_FILE, "r", encoding="utf-8") as mf:
                data = json.load(mf)
                backup_records = data.get("total_records", 0)
        except Exception:
            backup_records = 0

    # If manifest is missing or 0, check inside zip
    if backup_records == 0:
        try:
            with zipfile.ZipFile(LATEST_BACKUP, "r") as zf:
                if "backup_manifest.json" in zf.namelist():
                    data = json.loads(zf.read("backup_manifest.json").decode("utf-8"))
                    backup_records = data.get("total_records", 0)
        except Exception:
            pass

    # Condition: Current databases have 0 records or critical dbs are empty/missing, but backup has data
    should_restore = False
    critical_dbs = ["db/anti.db", "db/automod.db", "db/welcome.db", "db/prefix.db"]
    missing_critical = any(not os.path.exists(cdb) or os.path.getsize(cdb) == 0 for cdb in critical_dbs)

    if backup_records > 0 and (current_stats["total_records"] < backup_records or missing_critical):
        should_restore = True
        print(f"[Persistence] [!] Data disparity detected: Current records = {current_stats['total_records']}, Backup records = {backup_records}.")
        print("[Persistence] [*] Auto-restoring existing records (antinuke, automod, greet, etc.)...")
    
    if should_restore:
        return restore_backup(LATEST_BACKUP)
    
    return False

def get_backup_channel_id() -> Optional[int]:
    """Get the configured Discord backup channel ID from config or env."""
    env_ch = os.getenv("BACKUP_CHANNEL_ID")
    if env_ch and env_ch.strip().isdigit():
        return int(env_ch.strip())

    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
                data = json.load(cf)
                ch = data.get("backup_channel_id")
                if ch:
                    return int(ch)
        except Exception:
            pass
    return None

def set_backup_channel_id(channel_id: int) -> None:
    """Save the Discord backup channel ID to config."""
    data = {}
    if os.path.isfile(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as cf:
                data = json.load(cf)
        except Exception:
            data = {}
    data["backup_channel_id"] = channel_id
    with open(CONFIG_FILE, "w", encoding="utf-8") as cf:
        json.dump(data, cf, indent=2)

async def upload_backup_to_discord(client_or_webhook, channel_or_webhook_url=None, reason="auto") -> bool:
    """
    Asynchronously uploads the latest backup zip to a Discord Channel or Webhook.
    """
    import discord
    import aiohttp

    zip_path, stats = create_backup(reason=reason)
    if not os.path.isfile(zip_path):
        return False

    webhook_url = os.getenv("BACKUP_WEBHOOK_URL") or os.getenv("WEBHOOK_URL")
    channel_id = get_backup_channel_id()

    embed = discord.Embed(
        title="📦 Database Backup Archive",
        description=f"**Status:** All bot databases safely backed up and preserved.\n"
                    f"**Reason:** `{reason}`\n"
                    f"**Total Records:** `{stats['total_records']}` across `{stats['files_count']}` files\n"
                    f"**Timestamp:** `<t:{int(stats['timestamp'])}:F>`",
        color=0x2ecc71
    )
    embed.add_field(name="Auto-Restore", value="If the bot resets or a new zip is deployed, this backup will be auto-restored.", inline=False)
    embed.set_footer(text=f"Zyrox Persistence System • {stats['datetime']}")

    # 1. Try Discord Channel if available on client
    if hasattr(client_or_webhook, "get_channel") and channel_id:
        try:
            channel = client_or_webhook.get_channel(channel_id)
            if not channel:
                channel = await client_or_webhook.fetch_channel(channel_id)
            if channel:
                file = discord.File(zip_path, filename=f"zyrox_backup_{int(stats['timestamp'])}.zip")
                await channel.send(embed=embed, file=file)
                print(f"[Persistence] [CLOUD] Backup successfully uploaded to Discord Channel #{channel.name}")
                return True
        except Exception as e:
            print(f"[Persistence] Channel upload warning: {e}")

    # 2. Try Webhook URL if available
    target_webhook = channel_or_webhook_url if (isinstance(channel_or_webhook_url, str) and channel_or_webhook_url.startswith("http")) else webhook_url
    if target_webhook and target_webhook.startswith("https://discord.com/api/webhooks/"):
        timeout = aiohttp.ClientTimeout(total=25)
        for attempt in range(2):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    webhook = discord.Webhook.from_url(target_webhook, session=session)
                    file = discord.File(zip_path, filename=f"zyrox_backup_{int(stats['timestamp'])}.zip")
                    await webhook.send(embed=embed, file=file, username="Zyrox Backup System")
                    print(f"[Persistence] [CLOUD] Backup successfully uploaded to Discord Webhook")
                    return True
            except Exception as e:
                if attempt == 1:
                    print(f"[Persistence] Webhook upload notice (local backup safe): {e}")
                else:
                    await asyncio.sleep(2)

    return False

async def restore_from_cloud(client, channel_id: Optional[int] = None) -> bool:
    """
    Looks for the latest backup zip uploaded to the Discord backup channel,
    downloads it, and restores all databases.
    """
    import discord
    ch_id = channel_id or get_backup_channel_id()
    if not ch_id:
        return False
    try:
        channel = client.get_channel(ch_id)
        if not channel:
            channel = await client.fetch_channel(ch_id)
        if not channel:
            return False

        async for msg in channel.history(limit=30):
            for att in msg.attachments:
                if att.filename.endswith(".zip") and ("zyrox_backup" in att.filename or "backup" in att.filename):
                    temp_cloud_zip = os.path.join(BACKUP_ROOT, "cloud_download.zip")
                    await att.save(temp_cloud_zip)
                    success = restore_backup(temp_cloud_zip)
                    if success:
                        shutil.copyfile(temp_cloud_zip, LATEST_BACKUP)
                        print(f"[Persistence] [CLOUD] Restored latest backup from Discord channel #{channel.name} ({att.filename})")
                        return True
    except Exception as e:
        print(f"[Persistence] Cloud restore warning: {e}")
    return False

