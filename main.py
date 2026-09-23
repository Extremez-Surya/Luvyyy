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

if __name__ == "__main__":
    auto_clean_disk()
    ensure_dependencies()
    
    import runpy
    runpy.run_path("CodeX.py", run_name="__main__")
