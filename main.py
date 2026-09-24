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

if __name__ == "__main__":
    auto_clean_disk()
    ensure_dependencies()
    wait_for_network()
    
    # Auto-restore databases if a new zip was deployed or databases were reset
    try:
        from utils.persistence import auto_restore_if_needed
        auto_restore_if_needed()
    except Exception as e:
        print(f"[Persistence] Pre-startup check warning: {e}")

    import runpy
    runpy.run_path("CodeX.py", run_name="__main__")
