#!/usr/bin/env python3
# run_tracker_inproc.py
# Runner in-process para testar TorrentMonitor.py (geo OBRIGATÓRIA, sem CSV/DB)

import os
import sys
import time
import signal
import threading
from pathlib import Path
from datetime import datetime
import importlib.util

# =========================
# 🔧 CONFIGURAÇÕES DO TESTE
# =========================
TORRENT_DIR = Path("/home/usuario/.config/transmission/torrents/")  # pasta dos .torrent
POLL_TIME_SECONDS = 10        # intervalo de coleta (segundos)
DURATION = 120                # tempo total de execução; depois envia SIGINT
COUNTRY_FILTER = None         # ex.: "BR" para filtrar/avisar; None = todos
FORCE_VERBOSE = True          # força logs DEBUG no monitor
USE_TELEGRAM_STUB = True      # ignora login real e apenas "printa" mensagens

# =========================
# 🧪 STUB OPCIONAL DO TELETHON (para testar sem credenciais)
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
# 🧰 PRÉ-CHECKS BÁSICOS
# =========================
CWD = Path.cwd()
MAIN_PATH = CWD / "TorrentMonitor.py"
if not MAIN_PATH.exists():
    print(f"[ERRO] {MAIN_PATH} não encontrado (salve seu código como 'TorrentMonitor.py' ao lado deste runner).")
    sys.exit(1)

if not TORRENT_DIR.is_dir():
    print(f"[ERRO] Diretório de torrents inexistente: {TORRENT_DIR}")
    sys.exit(1)

if not any(TORRENT_DIR.glob("*.torrent")):
    print(f"[ERRO] Nenhum arquivo .torrent em {TORRENT_DIR}")
    sys.exit(1)

# Geo é OBRIGATÓRIO no monitor lean: valide cedo para erro mais amigável
city_mmdb = CWD / "dbs" / "GeoLite2-City_20250926" / "GeoLite2-City.mmdb"
asn_mmdb = CWD / "dbs" / "GeoLite2-ASN_20250929" / "GeoLite2-ASN.mmdb"
missing = [p for p in [city_mmdb, asn_mmdb] if not p.exists()]
if missing:
    print("[ERRO] Bases Geo obrigatórias não encontradas na pasta dbs/.")
    print("       Verifique se os arquivos estão em:")
    print("       - dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb")
    print("       - dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb")
    for m in missing:
        print(f"       - ausente: {m}")
    sys.exit(1)
else:
    print("[Runner] GeoIP: MMDBs detectados -> geolocalização ATIVADA")

# Avisos de dependências (best-effort)
for mod in ("libtorrent", "geoip2", "colorama", "requests", "telethon", "sqlite3"):
    try:
        __import__(mod)
    except Exception:
        print(f"[AVISO] Dependência Python ausente: {mod}  (instale com: python -m pip install {mod})")

# =========================
# 📥 IMPORT DINÂMICO DO SEU MÓDULO
# =========================
spec = importlib.util.spec_from_file_location("torrent_monitor_module", str(MAIN_PATH))
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)  # executa top-level do TorrentMonitor.py

if not hasattr(tm, "TorrentTracker"):
    print("[ERRO] O módulo não expôs a classe 'TorrentTracker'.")
    sys.exit(1)

# =========================
# 🧵 TIMER PARA FINALIZAR GRACIOSAMENTE
# =========================
def _graceful_stop_after(duration: int):
    time.sleep(duration)
    print("\n[Runner] Tempo de teste atingido. Enviando SIGINT para finalizar graciosamente...")
    os.kill(os.getpid(), signal.SIGINT)

stopper = None
if DURATION and DURATION > 0:
    stopper = threading.Thread(target=_graceful_stop_after, args=(DURATION,), daemon=True)
    stopper.start()
    print(f"[Runner] Executando por ~{DURATION}s; pressione CTRL+C para encerrar antes.")

# =========================
# ▶️ EXECUÇÃO IN-PROCESS
# =========================
# Instancia e roda o monitor (sem CSV/DB). COUNTRY_FILTER=None => todos os países.
monitor = tm.TorrentTracker(
    torrent_folder=str(TORRENT_DIR),
    output="monitor_output",  # Com CSV
    geo=True,      # Geolocalização ativada
    database="Monitor_test.db",  # Database de teste
    country=COUNTRY_FILTER,  # Filtro de país
    time_interval=POLL_TIME_SECONDS  # Intervalo de tempo
)

# Força verbosidade alta se desejado
if FORCE_VERBOSE and hasattr(monitor, "logger"):
    import logging
    monitor.logger.setLevel(logging.DEBUG)

try:
    monitor.main()
except KeyboardInterrupt:
    print("[Runner] Encerrado pelo usuário/tempo (KeyboardInterrupt).")
