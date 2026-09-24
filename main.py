# Auto-healing entry point for Pterodactyl, Docker, and Linux hosts
import os
import sys
import shutil
import subprocess

def auto_clean_disk():
    # 1. Clear pip cache directory to reclaim disk space
    for cache_p in [os.path.expanduser("~/.cache"), ".cache"]:
        if os.path.exists(cache_p):
            try:
                shutil.rmtree(cache_p, ignore_errors=True)
                print(f"[AutoClean] Cleaned {cache_p}")
            except Exception:
                pass

    # 2. Delete any leftover zip file to immediately reclaim 21+ MB
    try:
        for f in os.listdir("."):
            if f.endswith(".zip"):
                try:
                    os.remove(f)
                    print(f"[AutoClean] Removed {f} to free disk space.")
                except Exception:
                    pass
    except Exception:
        pass

def ensure_dependencies():
    try:
        import aiohttp
        import discord
    except ImportError:
        print("[AutoClean] Core dependencies missing. Running lightweight self-installation...")
        auto_clean_disk()
        try:
            cmd = [sys.executable, "-m", "pip", "install", "--no-cache-dir", "-r", "requirements.txt"]
            subprocess.run(cmd, check=True)
            print("[AutoClean] Dependencies installed successfully!")
        except Exception as e:
            print(f"[AutoClean] Pip install failed: {e}")

def wait_for_network(host="gateway.discord.gg", port=443, max_retries=10):
    import socket
    import time
    for i in range(max_retries):
        try:
            socket.getaddrinfo(host, port)
            return True
        except socket.gaierror:
            print(f"[Network] Waiting for host DNS/network to stabilize ({i+1}/{max_retries})...")
            time.sleep(2)
        except Exception:
            return True
    return False

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
                    print(f"[Sanitize] Warning checking {p}: {e}")

def auto_git_update():
    """Sync latest changes from GitHub if running in a git repo."""
    if not os.path.exists(".git"):
        return
    try:
        res = subprocess.run(["git", "pull", "--no-rebase", "origin", "main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15)
        out = (res.stdout + " " + res.stderr).strip()
        if "Already up to date" not in out and out:
            print(f"[AutoUpdate] Git sync result: {out}")
    except Exception as e:
        print(f"[AutoUpdate] Git check warning: {e}")

if __name__ == "__main__":
    auto_clean_disk()
    auto_git_update()
    ensure_dependencies()
    wait_for_network()
    
    # Auto-restore databases if a new zip was deployed or databases were reset
    try:
        from utils.persistence import auto_restore_if_needed
        auto_restore_if_needed()
    except Exception as e:
        print(f"[Persistence] Pre-startup check warning: {e}")

    # Ensure all json files are valid UTF-8
    sanitize_json_databases()

    import runpy
    runpy.run_path("CodeX.py", run_name="__main__")
