#!/usr/bin/env python3
# run_tracker_inproc.py
# In-process runner to test TorrentMonitor.py (geo MANDATORY, without CSV/DB)

import os
import sys
import time
import signal
import threading
from pathlib import Path
from datetime import datetime
import importlib.util

# =========================
# 🔧 TEST CONFIGURATIONS
# =========================
TORRENT_DIR = Path("/home/usuario/.config/transmission/torrents/")  # .torrent folder
POLL_TIME_SECONDS = 10        # collection interval (seconds)
DURATION = 120                # total execution time; then sends SIGINT
COUNTRY_FILTER = None         # ex.: "BR" to filter/alert; None = all
FORCE_VERBOSE = True          # force DEBUG logs in monitor
USE_TELEGRAM_STUB = True      # ignore real login and just "print" messages

# =========================
# 🧪 OPTIONAL TELETHON STUB (to test without credentials)
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
    print(f"[ERROR] {MAIN_PATH} not found (save your code as 'TorrentMonitor.py' next to this runner).")
    sys.exit(1)

if not TORRENT_DIR.is_dir():
    print(f"[ERROR] Torrent directory does not exist: {TORRENT_DIR}")
    sys.exit(1)

if not any(TORRENT_DIR.glob("*.torrent")):
    print(f"[ERROR] No .torrent files in {TORRENT_DIR}")
    sys.exit(1)

# Geo is MANDATORY in lean monitor: validate early for more friendly error
city_mmdb = CWD / "dbs" / "GeoLite2-City_20250926" / "GeoLite2-City.mmdb"
asn_mmdb = CWD / "dbs" / "GeoLite2-ASN_20250929" / "GeoLite2-ASN.mmdb"
missing = [p for p in [city_mmdb, asn_mmdb] if not p.exists()]
if missing:
    print("[ERROR] Required Geo databases not found in dbs/ folder.")
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
        print(f"[WARNING] Missing Python dependency: {mod}  (install with: python -m pip install {mod})")

# =========================
# 📥 DYNAMIC IMPORT OF YOUR MODULE
# =========================
spec = importlib.util.spec_from_file_location("torrent_monitor_module", str(MAIN_PATH))
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)  # execute top-level of TorrentMonitor.py

if not hasattr(tm, "TorrentTracker"):
    print("[ERROR] Module did not expose 'TorrentTracker' class.")
    sys.exit(1)

# =========================
# 🧵 TIMER FOR GRACEFUL FINISH
# =========================
def _graceful_stop_after(duration: int):
    time.sleep(duration)
    print("\n[Runner] Test time reached. Sending SIGINT to finish gracefully...")
    os.kill(os.getpid(), signal.SIGINT)

stopper = None
if DURATION and DURATION > 0:
    stopper = threading.Thread(target=_graceful_stop_after, args=(DURATION,), daemon=True)
    stopper.start()
    print(f"[Runner] Running for ~{DURATION}s; press CTRL+C to stop early.")

# =========================
# ▶️ IN-PROCESS EXECUTION
# =========================
# Instantiate and run the monitor (with CSV/DB). COUNTRY_FILTER=None => all countries.
monitor = tm.TorrentTracker(
    torrent_folder=str(TORRENT_DIR),
    output="monitor_output",  # With CSV
    geo=True,      # Geolocation enabled
    database="Monitor_test.db",  # Legacy parameter (not used with MariaDB)
    country=COUNTRY_FILTER,  # Country filter
    time_interval=POLL_TIME_SECONDS,  # Time interval
    # Configurações do MariaDB
    db_host='192.168.10.52',
    db_port=3306,
    db_user='admin',
    db_password='Jw%tD7@8P1',
    db_name='torrent_monitor'
)

# Force high verbosity if desired
if FORCE_VERBOSE and hasattr(monitor, "logger"):
    import logging
    monitor.logger.setLevel(logging.DEBUG)

try:
    monitor.main()
except KeyboardInterrupt:
    print("[Runner] Stopped by user/time (KeyboardInterrupt).")
except Exception as e:
    print(f"[Runner] Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("[Runner] Finished.")
