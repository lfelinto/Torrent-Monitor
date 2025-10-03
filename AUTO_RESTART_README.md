# 🔄 Auto-Restart Runner - TorrentMonitor

## 📋 Descrição

Script que mantém o TorrentMonitor em execução contínua **sem completar os downloads**. Quando um torrent atinge um limite de progresso configurável (padrão: 90%), os arquivos são automaticamente apagados e o download reinicia do zero.

Isso é útil para:
- ✅ Manter o monitoramento de peers ativo por tempo indefinido
- ✅ Não ocupar espaço em disco com downloads completos
- ✅ Simular comportamento de um peer que está sempre baixando
- ✅ Evitar completar downloads durante testes de monitoramento

## 🚀 Como Usar

### Execução Básica

```bash
python3 run_tracker_autorestart.py
```

### Execução em Background

```bash
nohup python3 run_tracker_autorestart.py > autorestart.log 2>&1 &
```

## ⚙️ Configurações Disponíveis

Edite o arquivo `run_tracker_autorestart.py` no topo para ajustar:

### Configurações Principais

```python
# Caminho dos arquivos .torrent
TORRENT_DIR = Path("/home/usuario/.config/transmission/torrents/")

# Intervalo de coleta de dados de peers (segundos)
POLL_TIME_SECONDS = 10

# Tempo total de execução (0 = infinito)
DURATION = 3600  # 1 hora

# Filtro de país (None = todos)
COUNTRY_FILTER = None  # ou "Spain", "Brazil", etc.

# Logs detalhados
FORCE_VERBOSE = True
```

### Configurações de Auto-Restart

```python
# Limite de progresso para reiniciar (0.0 a 1.0)
PROGRESS_THRESHOLD = 0.90  # 90%

# Intervalo para verificar progresso (segundos)
CHECK_INTERVAL = 30

# Velocidade mínima para considerar download ativo (bytes/s)
MIN_DOWNLOAD_SPEED = 1000  # 1 KB/s

# Pasta onde os downloads são salvos
DOWNLOADS_PATH = Path.cwd() / "Downloads"
```

### Configurações do MariaDB

```python
db_host='192.168.10.52'
db_port=3306
db_user='admin'
db_password='Jw%tD7@8P1'
db_name='torrent_monitor'
```

## 📊 O Que o Script Faz

### 1. Monitoramento Contínuo
- Coleta dados de peers a cada `POLL_TIME_SECONDS`
- Registra IPs, ISPs, geolocalização, clientes BitTorrent
- Salva em MariaDB e arquivo CSV

### 2. Verificação de Progresso
- A cada `CHECK_INTERVAL` segundos, verifica o progresso de cada torrent
- Mostra estatísticas:
  - Progresso atual (%)
  - Velocidade de download (KB/s)
  - Tamanho atual em disco (MB)
  - Número de seeds e peers

### 3. Auto-Restart Inteligente
Quando detecta que um torrent atingiu o limite:
- ⚠️ Pausa o torrent
- 🗑️ Apaga todos os arquivos da pasta `Downloads`
- 🔄 Retoma o torrent (reinicia do zero)
- ✅ Continua monitorando

### 4. Verificação de Download Ativo
Só reinicia se detectar que realmente está baixando:
- Velocidade de download > `MIN_DOWNLOAD_SPEED`
- OU tamanho da pasta aumentando

Isso evita reiniciar torrents que estão parados (sem seeds).

## 📈 Saída do Script

### Logs Principais

```
[Runner] GeoIP: MMDBs detectados -> geolocalização ATIVADA
[Runner] 🚀 Iniciando TorrentMonitor com Auto-Restart
[Runner]    Pasta de torrents: /home/usuario/.config/transmission/torrents
[Runner]    Pasta de downloads: /home/usuario/Desktop/cursor/Torrent-Monitor/Downloads
[Runner]    Intervalo de coleta: 10s

[AutoRestart] 🔍 Monitor de progresso iniciado
[AutoRestart]    Limite de progresso: 90.0%
[AutoRestart]    Velocidade mínima: 1000 bytes/s
[AutoRestart]    Intervalo de verificação: 30s
```

### Durante o Monitoramento

```
[AutoRestart] 📊 Status do torrent: ubuntu-22.04-desktop-amd64.iso
[AutoRestart]    Progresso: 87.32%
[AutoRestart]    Download: 234.56 KB/s
[AutoRestart]    Tamanho atual: 3245.67 MB
[AutoRestart]    Seeds: 45 | Peers: 123
```

### Quando Atinge o Limite

```
[AutoRestart] ⚠️  LIMITE ATINGIDO!
[AutoRestart]    Torrent: ubuntu-22.04-desktop-amd64.iso
[AutoRestart]    Progresso: 91.25%
[AutoRestart]    Reinício #1
[AutoRestart] 🔄 Reiniciando download...

[AutoRestart] 🗑️  Arquivo apagado: ubuntu-22.04-desktop-amd64.iso
[AutoRestart] ✅ Pasta Downloads limpa com sucesso!
[AutoRestart] ✅ Download reiniciado com sucesso!
```

## 🛑 Parar o Script

### Manualmente
Pressione `CTRL+C` para parar graciosamente.

### Por Tempo
O script para automaticamente após `DURATION` segundos.

### Encontrar Processo em Background
```bash
ps aux | grep run_tracker_autorestart
kill <PID>
```

## 📁 Arquivos Gerados

- `monitor_output.csv` - Dados de peers em CSV
- `Monitor_test.db` - Banco SQLite (se não usar MariaDB)
- Tabelas no MariaDB:
  - `report_table` - Dados detalhados de peers
  - `info_torrent` - Metadados dos torrents
- `notified_peers.txt` - Cache de peers notificados
- `autorestart.log` - Log de execução (se usar nohup)

## ⚠️ Avisos Importantes

1. **Espaço em Disco**: Mesmo reiniciando, os downloads podem ocupar espaço temporariamente. Monitore o disco.

2. **Bandwidth**: O script continuará consumindo banda enquanto baixa. Configure `download_rate_limit` se necessário.

3. **Seeds**: Se não houver seeds, o download não iniciará e o script não reiniciará.

4. **MariaDB**: Certifique-se de que o servidor MariaDB está acessível nas configurações fornecidas.

## 🔧 Troubleshooting

### Erro: "No .torrent files"
- Verifique se há arquivos `.torrent` em `TORRENT_DIR`
- Ajuste o caminho `TORRENT_DIR` no script

### Erro: "GeoIP databases not found"
- Baixe os databases GeoLite2 de MaxMind
- Coloque em `dbs/GeoLite2-City_20250926/` e `dbs/GeoLite2-ASN_20250929/`

### Não está reiniciando
- Verifique se há seeds disponíveis (velocidade > 0)
- Ajuste `MIN_DOWNLOAD_SPEED` para um valor menor
- Verifique `PROGRESS_THRESHOLD` - talvez seja muito alto

### Downloads não são apagados
- Verifique permissões da pasta `Downloads`
- Verifique se `DOWNLOADS_PATH` está correto

## 🔍 Diferenças vs run_tracker_inproc.py

| Característica | run_tracker_inproc.py | run_tracker_autorestart.py |
|----------------|------------------------|----------------------------|
| Auto-restart downloads | ❌ Não | ✅ Sim |
| Monitoramento de progresso | ❌ Não | ✅ Sim |
| Limpeza automática Downloads | ❌ Manual | ✅ Automático |
| Verificação de download ativo | ❌ Não | ✅ Sim |
| Estatísticas de progresso | ❌ Não | ✅ Sim |
| Duração padrão | 120s (2 min) | 3600s (1 hora) |

## 📝 Exemplo de Uso Completo

```bash
# 1. Verificar torrents disponíveis
ls -la /home/usuario/.config/transmission/torrents/

# 2. Editar configurações se necessário
nano run_tracker_autorestart.py

# 3. Executar o script
python3 run_tracker_autorestart.py

# 4. Monitorar logs em outro terminal
tail -f monitor_output.csv

# 5. Consultar dados no MariaDB
mysql -h 192.168.10.52 -u admin -p torrent_monitor
SELECT COUNT(*) FROM report_table;
```

## 🎯 Casos de Uso

1. **Testes de Longa Duração**: Monitorar peers por horas/dias sem completar downloads
2. **Análise de Swarms**: Observar como swarms evoluem ao longo do tempo
3. **Detecção de Padrões**: Identificar horários de pico, regiões mais ativas
4. **Economia de Espaço**: Não precisa armazenar arquivos completos
5. **Simulação Realista**: Comportar-se como um peer real que está sempre baixando

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique os logs com `FORCE_VERBOSE = True`
2. Teste primeiro com `run_tracker_inproc.py` (mais simples)
3. Verifique se todas as dependências estão instaladas
4. Confirme que MariaDB está acessível

---

**Desenvolvido para manter monitoramento contínuo de swarms BitTorrent** 🚀

