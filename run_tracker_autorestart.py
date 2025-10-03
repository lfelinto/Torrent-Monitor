#!/usr/bin/env python3
# run_tracker_autorestart.py
# Runner que reinicia downloads automaticamente quando estiverem quase completos
# Mantém o monitoramento ativo sem completar os downloads

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
# 🔧 CONFIGURAÇÕES
# =========================
TORRENT_DIR = Path("/home/usuario/.config/transmission/torrents/")  # Pasta com .torrent
POLL_TIME_SECONDS = 10        # Intervalo de coleta (segundos)
DURATION = 3600               # Tempo total de execução (1 hora)
COUNTRY_FILTER = None         # ex.: "Spain" para filtrar/alertar; None = todos
FORCE_VERBOSE = True          # Forçar logs DEBUG no monitor
USE_TELEGRAM_STUB = True      # Ignorar login real e apenas "printar" mensagens

# Configurações de Auto-Restart
PROGRESS_THRESHOLD = 0.90     # Limite de progresso (90%) para reiniciar
CHECK_INTERVAL = 30           # Intervalo para verificar progresso (segundos)
MIN_DOWNLOAD_SPEED = 1000     # Velocidade mínima (bytes/s) para considerar download ativo
DOWNLOADS_PATH = Path.cwd() / "Downloads"  # Pasta de downloads

# =========================
# 🧪 TELETHON STUB (para testar sem credenciais)
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
# 🧰 VERIFICAÇÕES BÁSICAS
# =========================
CWD = Path.cwd()
MAIN_PATH = CWD / "TorrentMonitor.py"
if not MAIN_PATH.exists():
    print(f"[ERROR] {MAIN_PATH} não encontrado.")
    sys.exit(1)

if not TORRENT_DIR.is_dir():
    print(f"[ERROR] Diretório de torrents não existe: {TORRENT_DIR}")
    sys.exit(1)

if not any(TORRENT_DIR.glob("*.torrent")):
    print(f"[ERROR] Nenhum arquivo .torrent em {TORRENT_DIR}")
    sys.exit(1)

# Verificar Geo databases
city_mmdb = CWD / "dbs" / "GeoLite2-City_20250926" / "GeoLite2-City.mmdb"
asn_mmdb = CWD / "dbs" / "GeoLite2-ASN_20250929" / "GeoLite2-ASN.mmdb"
missing = [p for p in [city_mmdb, asn_mmdb] if not p.exists()]
if missing:
    print("[ERROR] Databases Geo não encontradas em dbs/")
    print("       Verifique se os arquivos estão em:")
    print("       - dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb")
    print("       - dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb")
    for m in missing:
        print(f"       - faltando: {m}")
    sys.exit(1)
else:
    print("[Runner] GeoIP: MMDBs detectados -> geolocalização ATIVADA")

# Avisos de dependências
for mod in ("libtorrent", "geoip2", "colorama", "requests", "telethon", "pymysql"):
    try:
        __import__(mod)
    except Exception:
        print(f"[WARNING] Dependência Python faltando: {mod}  (instale com: pip install {mod})")

# =========================
# 📥 IMPORTAÇÃO DINÂMICA DO MÓDULO
# =========================
spec = importlib.util.spec_from_file_location("torrent_monitor_module", str(MAIN_PATH))
tm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tm)

if not hasattr(tm, "TorrentTracker"):
    print("[ERROR] Módulo não expôs a classe 'TorrentTracker'.")
    sys.exit(1)

# =========================
# 🔄 MONITOR DE PROGRESSO E AUTO-RESTART
# =========================
monitor_instance = None
stop_monitoring = False

def clean_downloads_folder():
    """Limpa a pasta Downloads para reiniciar os downloads"""
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
    """Calcula o tamanho total da pasta em bytes"""
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
    """Thread que monitora o progresso dos downloads e reinicia quando necessário"""
    global monitor_instance, stop_monitoring
    
    print(f"\n[AutoRestart] 🔍 Monitor de progresso iniciado")
    print(f"[AutoRestart]    Limite de progresso: {PROGRESS_THRESHOLD * 100}%")
    print(f"[AutoRestart]    Velocidade mínima: {MIN_DOWNLOAD_SPEED} bytes/s")
    print(f"[AutoRestart]    Intervalo de verificação: {CHECK_INTERVAL}s\n")
    
    last_download_size = 0
    restart_count = 0
    
    while not stop_monitoring:
        try:
            time.sleep(CHECK_INTERVAL)
            
            if monitor_instance is None or not hasattr(monitor_instance, 'session'):
                continue
            
            # Verificar se há handles ativos
            handles = getattr(monitor_instance, 'handles', [])
            if not handles:
                continue
            
            # Verificar cada torrent
            for handle in handles:
                try:
                    status = handle.status()
                    progress = status.progress
                    download_rate = status.download_rate
                    name = status.name
                    
                    # Verificar tamanho da pasta Downloads
                    current_size = get_folder_size(DOWNLOADS_PATH)
                    is_downloading = download_rate > MIN_DOWNLOAD_SPEED or current_size > last_download_size
                    
                    # Log de status
                    if is_downloading:
                        print(f"\n[AutoRestart] 📊 Status do torrent: {name}")
                        print(f"[AutoRestart]    Progresso: {progress * 100:.2f}%")
                        print(f"[AutoRestart]    Download: {download_rate / 1024:.2f} KB/s")
                        print(f"[AutoRestart]    Tamanho atual: {current_size / (1024*1024):.2f} MB")
                        print(f"[AutoRestart]    Seeds: {status.num_seeds} | Peers: {status.num_peers}")
                    
                    # Verificar se precisa reiniciar
                    if progress >= PROGRESS_THRESHOLD and is_downloading:
                        restart_count += 1
                        print(f"\n[AutoRestart] ⚠️  LIMITE ATINGIDO!")
                        print(f"[AutoRestart]    Torrent: {name}")
                        print(f"[AutoRestart]    Progresso: {progress * 100:.2f}%")
                        print(f"[AutoRestart]    Reinício #{restart_count}")
                        print(f"[AutoRestart] 🔄 Reiniciando download...\n")
                        
                        # Pausar o torrent
                        handle.pause()
                        time.sleep(2)
                        
                        # Limpar pasta Downloads
                        if clean_downloads_folder():
                            # Retomar o torrent (reiniciará do zero)
                            time.sleep(1)
                            handle.resume()
                            print(f"[AutoRestart] ✅ Download reiniciado com sucesso!\n")
                            last_download_size = 0
                        else:
                            # Se falhou a limpeza, tentar retomar mesmo assim
                            handle.resume()
                    
                    last_download_size = current_size
                    
                except Exception as e:
                    print(f"[AutoRestart] ⚠️  Erro ao verificar handle: {e}")
                    continue
                    
        except Exception as e:
            print(f"[AutoRestart] ❌ Erro no monitor: {e}")
            continue
    
    print(f"\n[AutoRestart] 🛑 Monitor de progresso finalizado")
    print(f"[AutoRestart]    Total de reinícios: {restart_count}")

# =========================
# 🧵 TIMER PARA FINALIZAÇÃO GRACIOSA
# =========================
def _graceful_stop_after(duration: int):
    global stop_monitoring
    time.sleep(duration)
    print("\n[Runner] ⏰ Tempo de teste atingido. Enviando SIGINT para finalizar graciosamente...")
    stop_monitoring = True
    time.sleep(2)
    os.kill(os.getpid(), signal.SIGINT)

stopper = None
if DURATION and DURATION > 0:
    stopper = threading.Thread(target=_graceful_stop_after, args=(DURATION,), daemon=True)
    stopper.start()
    print(f"[Runner] ⏱️  Executando por ~{DURATION}s ({DURATION//60} minutos); pressione CTRL+C para parar antes.")

# =========================
# ▶️ EXECUÇÃO IN-PROCESS
# =========================
print(f"\n[Runner] 🚀 Iniciando TorrentMonitor com Auto-Restart")
print(f"[Runner]    Pasta de torrents: {TORRENT_DIR}")
print(f"[Runner]    Pasta de downloads: {DOWNLOADS_PATH}")
print(f"[Runner]    Intervalo de coleta: {POLL_TIME_SECONDS}s")

monitor = tm.TorrentTracker(
    torrent_folder=str(TORRENT_DIR),
    output="monitor_output",
    geo=True,
    database="Monitor_test.db",
    country=COUNTRY_FILTER,
    time_interval=POLL_TIME_SECONDS,
    # Configurações do MariaDB
    db_host='192.168.10.52',
    db_port=3306,
    db_user='admin',
    db_password='Jw%tD7@8P1',
    db_name='torrent_monitor'
)

monitor_instance = monitor

# Forçar alta verbosidade se desejado
if FORCE_VERBOSE and hasattr(monitor, "logger"):
    import logging
    monitor.logger.setLevel(logging.DEBUG)

# Iniciar thread de monitoramento de progresso
progress_thread = threading.Thread(target=monitor_progress_and_restart, daemon=True)
progress_thread.start()

try:
    monitor.main()
except KeyboardInterrupt:
    print("\n[Runner] 🛑 Parado por usuário/tempo (KeyboardInterrupt).")
    stop_monitoring = True
except Exception as e:
    print(f"[Runner] ❌ Erro inesperado: {e}")
    import traceback
    traceback.print_exc()
    stop_monitoring = True

# Aguardar thread de monitoramento finalizar
time.sleep(2)

print("\n[Runner] ✅ Finalizado.")

