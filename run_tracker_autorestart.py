#!/usr/bin/env python3
# run_tracker_autorestart.py
# Runner that automatically restarts downloads when almost complete
# Keeps monitoring active without completing downloads

import os
import sys
import time
import signal
import threading
import shutil
from pathlib import Path
from datetime import datetime
import importlib.util

# =========================
# 🔧 CONFIGURATION
# =========================
TORRENT_DIR = Path("/home/usuario/.config/transmission/torrents/")  # .torrent files folder
POLL_TIME_SECONDS = 10        # Data collection interval (seconds)
DURATION = 3600               # Total execution time (1 hour, 0 = infinite)
COUNTRY_FILTER = None         # e.g.: "Spain" to filter/alert; None = all countries
FORCE_VERBOSE = True          # Force DEBUG logs in monitor
USE_TELEGRAM_STUB = True      # Ignore real login and just print messages

# Auto-Restart Settings
PROGRESS_THRESHOLD = 0.90     # Progress threshold (90%) to restart
CHECK_INTERVAL = 30           # Interval to check progress (seconds)
MIN_DOWNLOAD_SPEED = 1000     # Minimum speed (bytes/s) to consider download active
DOWNLOADS_PATH = Path.cwd() / "Downloads"  # Downloads folder

# =========================
# 🧪 TELETHON STUB (for testing without credentials)
# =========================
def _install_telethon_stub():
    import types
    telethon_mod = types.ModuleType("telethon")
    sync_mod = types.ModuleType("telethon.sync")
    errors_mod = types.ModuleType("telethon.errors")

    class SessionPasswordNeededError(Exception):
        pass

    class _DummyEntity:
        def __init__(self, target): self.target = target

    class TelegramClient:
        def __init__(self, session_name, api_id, api_hash, *_, **__):
            self.session_name = session_name
            self.api_id = api_id
            self.api_hash = api_hash
            self._authorized = True

        def connect(self): print("[StubTelethon] connect()")
        def is_user_authorized(self): return True
        def send_code_request(self, phone): print(f"[StubTelethon] send_code_request({phone})")
        def sign_in(self, *args, **kwargs): print(f"[StubTelethon] sign_in(args={args}, kwargs={kwargs})")
        def get_entity(self, channel_id):
            print(f"[StubTelethon] get_entity({channel_id})"); return _DummyEntity(channel_id)
        def send_message(self, entity, message, parse_mode=None):
            print(f"[StubTelethon] send_message(to={entity.target}, mode={parse_mode})")
            print("-----8<----- Telegram message (stub) -----")
            print(message)
            print("-----8<-----------------------------------")

    telethon_mod.TelegramClient = TelegramClient
    sync_mod.TelegramClient = TelegramClient
    errors_mod.SessionPasswordNeededError = SessionPasswordNeededError

    telethon_mod.sync = sync_mod
    telethon_mod.errors = errors_mod

    sys.modules["telethon"] = telethon_mod
    sys.modules["telethon.sync"] = sync_mod
    sys.modules["telethon.errors"] = errors_mod

if USE_TELEGRAM_STUB:
    _install_telethon_stub()

# =========================
# 🧰 BASIC PRE-CHECKS
# =========================
CWD = Path.cwd()
MAIN_PATH = CWD / "TorrentMonitor.py"
if not MAIN_PATH.exists():
    print(f"[ERROR] {MAIN_PATH} not found.")
    sys.exit(1)

if not TORRENT_DIR.is_dir():
    print(f"[ERROR] Torrent directory does not exist: {TORRENT_DIR}")
    sys.exit(1)

if not any(TORRENT_DIR.glob("*.torrent")):
    print(f"[ERROR] No .torrent files in {TORRENT_DIR}")
    sys.exit(1)

# Check Geo databases
city_mmdb = CWD / "dbs" / "GeoLite2-City_20250926" / "GeoLite2-City.mmdb"
asn_mmdb = CWD / "dbs" / "GeoLite2-ASN_20250929" / "GeoLite2-ASN.mmdb"
missing = [p for p in [city_mmdb, asn_mmdb] if not p.exists()]
if missing:
    print("[ERROR] Geo databases not found in dbs/ folder")
    print("       Check if files are in:")
    print("       - dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb")
    print("       - dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb")
    for m in missing:
        print(f"       - missing: {m}")
    sys.exit(1)
else:
    print("[Runner] GeoIP: MMDBs detected -> geolocation ENABLED")

# Dependency warnings (best-effort)
for mod in ("libtorrent", "geoip2", "colorama", "requests", "telethon", "pymysql"):
    try:
        __import__(mod)
    except Exception:
        print(f"[WARNING] Missing Python dependency: {mod}  (install with: pip install {mod})")

# =========================
# 📥 DYNAMIC MODULE IMPORT
# =========================
spec = importlib.util.spec_from_file_location("torrent_monitor_module", str(MAIN_PATH))
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

if not hasattr(tm, "TorrentTracker"):
    print("[ERROR] Module did not expose 'TorrentTracker' class.")
    sys.exit(1)

# =========================
# 🔄 PROGRESS MONITOR AND AUTO-RESTART
# =========================
monitor_instance = None
stop_monitoring = False

def clean_downloads_folder():
    """Cleans Downloads folder to restart downloads"""
    try:
        if DOWNLOADS_PATH.exists():
            for item in DOWNLOADS_PATH.iterdir():
                if item.is_file():
                    item.unlink()
                    print(f"[AutoRestart] 🗑️  Arquivo apagado: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"[AutoRestart] 🗑️  Pasta apagada: {item.name}")
            print("[AutoRestart] ✅ Pasta Downloads limpa com sucesso!")
            return True
    except Exception as e:
        print(f"[AutoRestart] ❌ Erro ao limpar Downloads: {e}")
        return False

def get_folder_size(path):
    """Calculates total folder size in bytes"""
    total = 0
    try:
        for entry in path.iterdir():
            if entry.is_file():
                total += entry.stat().st_size
            elif entry.is_dir():
                total += get_folder_size(entry)
    except Exception:
        pass
    return total

def monitor_progress_and_restart():
    """Thread that monitors download progress and restarts when necessary"""
    global monitor_instance, stop_monitoring
    
    print(f"\n[AutoRestart] 🔍 Progress monitor started")
    print(f"[AutoRestart]    Progress threshold: {PROGRESS_THRESHOLD * 100}%")
    print(f"[AutoRestart]    Minimum speed: {MIN_DOWNLOAD_SPEED} bytes/s")
    print(f"[AutoRestart]    Check interval: {CHECK_INTERVAL}s\n")
    
    last_download_size = 0
    restart_count = 0
    
    while not stop_monitoring:
        try:
            time.sleep(CHECK_INTERVAL)
            
            if monitor_instance is None or not hasattr(monitor_instance, 'session'):
                continue
            
            # Check for active handles
            handles = getattr(monitor_instance, 'handles', [])
            if not handles:
                continue
            
            # Check each torrent
            for handle in handles:
                try:
                    status = handle.status()
                    progress = status.progress
                    download_rate = status.download_rate
                    name = status.name
                    
                    # Check Downloads folder size
                    current_size = get_folder_size(DOWNLOADS_PATH)
                    is_downloading = download_rate > MIN_DOWNLOAD_SPEED or current_size > last_download_size
                    
                    # Status logging
                    if is_downloading:
                        print(f"\n[AutoRestart] 📊 Torrent status: {name}")
                        print(f"[AutoRestart]    Progress: {progress * 100:.2f}%")
                        print(f"[AutoRestart]    Download: {download_rate / 1024:.2f} KB/s")
                        print(f"[AutoRestart]    Current size: {current_size / (1024*1024):.2f} MB")
                        print(f"[AutoRestart]    Seeds: {status.num_seeds} | Peers: {status.num_peers}")
                    
                    # Check if restart is needed
                    if progress >= PROGRESS_THRESHOLD and is_downloading:
                        restart_count += 1
                        print(f"\n[AutoRestart] ⚠️  THRESHOLD REACHED!")
                        print(f"[AutoRestart]    Torrent: {name}")
                        print(f"[AutoRestart]    Progress: {progress * 100:.2f}%")
                        print(f"[AutoRestart]    Restart #{restart_count}")
                        print(f"[AutoRestart] 🔄 Restarting download...\n")
                        
                        # Pause the torrent
                        handle.pause()
                        time.sleep(2)
                        
                        # Clean Downloads folder
                        if clean_downloads_folder():
                            # Resume torrent (will restart from zero)
                            time.sleep(1)
                            handle.resume()
                            print(f"[AutoRestart] ✅ Download restarted successfully!\n")
                            last_download_size = 0
                        else:
                            # If cleanup failed, try to resume anyway
                            handle.resume()
                    
                    last_download_size = current_size
                    
                except Exception as e:
                    print(f"[AutoRestart] ⚠️  Error checking handle: {e}")
                    continue
                    
        except Exception as e:
            print(f"[AutoRestart] ❌ Monitor error: {e}")
            continue
    
    print(f"\n[AutoRestart] 🛑 Progress monitor stopped")
    print(f"[AutoRestart]    Total restarts: {restart_count}")

# =========================
# 🧵 TIMER FOR GRACEFUL FINISH
# =========================
def _graceful_stop_after(duration: int):
    global stop_monitoring
    time.sleep(duration)
    print("\n[Runner] ⏰ Test time reached. Sending SIGINT to finish gracefully...")
    stop_monitoring = True
    time.sleep(2)
    os.kill(os.getpid(), signal.SIGINT)

stopper = None
if DURATION and DURATION > 0:
    stopper = threading.Thread(target=_graceful_stop_after, args=(DURATION,), daemon=True)
    stopper.start()
    print(f"[Runner] ⏱️  Running for ~{DURATION}s ({DURATION//60} minutes); press CTRL+C to stop early.")

# =========================
# ▶️ IN-PROCESS EXECUTION
# =========================
print(f"\n[Runner] 🚀 Starting TorrentMonitor with Auto-Restart")
print(f"[Runner]    Torrents folder: {TORRENT_DIR}")
print(f"[Runner]    Downloads folder: {DOWNLOADS_PATH}")
print(f"[Runner]    Collection interval: {POLL_TIME_SECONDS}s")

monitor = tm.TorrentTracker(
    torrent_folder=str(TORRENT_DIR),
    output="monitor_output",
    geo=True,
    database="Monitor_test.db",
    country=COUNTRY_FILTER,
    time_interval=POLL_TIME_SECONDS,
    # MariaDB configuration
    db_host='192.168.10.52',
    db_port=3306,
    db_user='admin',
    db_password='Jw%tD7@8P1',
    db_name='torrent_monitor'
)

monitor_instance = monitor

# Force high verbosity if desired
if FORCE_VERBOSE and hasattr(monitor, "logger"):
    import logging
    monitor.logger.setLevel(logging.DEBUG)

# Start progress monitoring thread
progress_thread = threading.Thread(target=monitor_progress_and_restart, daemon=True)
progress_thread.start()

try:
    monitor.main()
except KeyboardInterrupt:
    print("\n[Runner] 🛑 Stopped by user/time (KeyboardInterrupt).")
    stop_monitoring = True
except Exception as e:
    print(f"[Runner] ❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    stop_monitoring = True

# Wait for monitoring thread to finish
time.sleep(2)

print("\n[Runner] ✅ Finished.")

