# 🔄 Auto-Restart Runner - TorrentMonitor

## 📋 Description

Script that keeps TorrentMonitor running continuously **without completing downloads**. When a torrent reaches a configurable progress threshold (default: 90%), files are automatically deleted and the download restarts from zero.

This is useful for:
- ✅ Keeping peer monitoring active indefinitely
- ✅ Not filling disk space with completed downloads
- ✅ Simulating behavior of a peer that's always downloading
- ✅ Avoiding download completion during monitoring tests

## 🚀 How to Use

### Basic Execution

```bash
python3 run_tracker_autorestart.py
```

### Background Execution

```bash
nohup python3 run_tracker_autorestart.py > autorestart.log 2>&1 &
```

## ⚙️ Available Configuration

Edit the `run_tracker_autorestart.py` file at the top to adjust:

### Main Settings

```python
# Path to .torrent files
TORRENT_DIR = Path("/home/usuario/.config/transmission/torrents/")

# Peer data collection interval (seconds)
POLL_TIME_SECONDS = 10

# Total execution time (0 = infinite)
DURATION = 3600  # 1 hour

# Country filter (None = all)
COUNTRY_FILTER = None  # or "Spain", "Brazil", etc.

# Detailed logs
FORCE_VERBOSE = True
```

### Auto-Restart Settings

```python
# Progress threshold to restart (0.0 to 1.0)
PROGRESS_THRESHOLD = 0.90  # 90%

# Interval to check progress (seconds)
CHECK_INTERVAL = 30

# Minimum speed to consider download active (bytes/s)
MIN_DOWNLOAD_SPEED = 1000  # 1 KB/s

# Folder where downloads are saved
DOWNLOADS_PATH = Path.cwd() / "Downloads"
```

### MariaDB Configuration

```python
db_host='192.168.10.52'
db_port=3306
db_user='admin'
db_password='Jw%tD7@8P1'
db_name='torrent_monitor'
```

## 📊 What the Script Does

### 1. Continuous Monitoring
- Collects peer data every `POLL_TIME_SECONDS`
- Records IPs, ISPs, geolocation, BitTorrent clients
- Saves to MariaDB and CSV file

### 2. Progress Checking
- Every `CHECK_INTERVAL` seconds, checks progress of each torrent
- Shows statistics:
  - Current progress (%)
  - Download speed (KB/s)
  - Current disk size (MB)
  - Number of seeds and peers

### 3. Intelligent Auto-Restart
When it detects a torrent has reached the threshold:
- ⚠️ Pauses the torrent
- 🗑️ Deletes all files from `Downloads` folder
- 🔄 Resumes the torrent (restarts from zero)
- ✅ Continues monitoring

### 4. Active Download Verification
Only restarts if it detects actual downloading:
- Download speed > `MIN_DOWNLOAD_SPEED`
- OR folder size increasing

This prevents restarting torrents that are stopped (no seeds).

## 📈 Script Output

### Main Logs

```
[Runner] GeoIP: MMDBs detected -> geolocation ENABLED
[Runner] 🚀 Starting TorrentMonitor with Auto-Restart
[Runner]    Torrents folder: /home/usuario/.config/transmission/torrents
[Runner]    Downloads folder: /home/usuario/Desktop/cursor/Torrent-Monitor/Downloads
[Runner]    Collection interval: 10s

[AutoRestart] 🔍 Progress monitor started
[AutoRestart]    Progress threshold: 90.0%
[AutoRestart]    Minimum speed: 1000 bytes/s
[AutoRestart]    Check interval: 30s
```

### During Monitoring

```
[AutoRestart] 📊 Torrent status: ubuntu-22.04-desktop-amd64.iso
[AutoRestart]    Progress: 87.32%
[AutoRestart]    Download: 234.56 KB/s
[AutoRestart]    Current size: 3245.67 MB
[AutoRestart]    Seeds: 45 | Peers: 123
```

### When Threshold is Reached

```
[AutoRestart] ⚠️  THRESHOLD REACHED!
[AutoRestart]    Torrent: ubuntu-22.04-desktop-amd64.iso
[AutoRestart]    Progress: 91.25%
[AutoRestart]    Restart #1
[AutoRestart] 🔄 Restarting download...

[AutoRestart] 🗑️  File deleted: ubuntu-22.04-desktop-amd64.iso
[AutoRestart] ✅ Downloads folder cleaned successfully!
[AutoRestart] ✅ Download restarted successfully!
```

## 🛑 Stopping the Script

### Manually
Press `CTRL+C` to stop gracefully.

### By Time
Script stops automatically after `DURATION` seconds.

### Find Background Process
```bash
ps aux | grep run_tracker_autorestart
kill <PID>
```

## 📁 Generated Files

- `monitor_output.csv` - Peer data in CSV format
- `Monitor_test.db` - SQLite database (if not using MariaDB)
- MariaDB tables:
  - `report_table` - Detailed peer data
  - `info_torrent` - Torrent metadata
- `autorestart.log` - Execution log (if using nohup)

## ⚠️ Important Warnings

1. **Disk Space**: Even with restarts, downloads can temporarily use space. Monitor disk usage.

2. **Bandwidth**: Script will continue consuming bandwidth while downloading. Configure `download_rate_limit` if needed.

3. **Seeds**: If no seeds available, download won't start and script won't restart.

4. **MariaDB**: Ensure MariaDB server is accessible with provided configuration.

## 🔧 Troubleshooting

### Error: "No .torrent files"
- Check if there are `.torrent` files in `TORRENT_DIR`
- Adjust `TORRENT_DIR` path in the script

### Error: "GeoIP databases not found"
- Download GeoLite2 databases from MaxMind
- Place in `dbs/GeoLite2-City_20250926/` and `dbs/GeoLite2-ASN_20250929/`

### Not restarting
- Check if seeds are available (speed > 0)
- Adjust `MIN_DOWNLOAD_SPEED` to a lower value
- Check `PROGRESS_THRESHOLD` - might be too high

### Downloads not being deleted
- Check `Downloads` folder permissions
- Verify `DOWNLOADS_PATH` is correct

## 🔍 Differences vs run_tracker_inproc.py

| Feature | run_tracker_inproc.py | run_tracker_autorestart.py |
|---------|------------------------|----------------------------|
| Auto-restart downloads | ❌ No | ✅ Yes |
| Progress monitoring | ❌ No | ✅ Yes |
| Automatic Downloads cleanup | ❌ Manual | ✅ Automatic |
| Active download verification | ❌ No | ✅ Yes |
| Progress statistics | ❌ No | ✅ Yes |
| Default duration | 120s (2 min) | 3600s (1 hour) |

## 📝 Complete Usage Example

```bash
# 1. Check available torrents
ls -la /home/usuario/.config/transmission/torrents/

# 2. Edit configuration if needed
nano run_tracker_autorestart.py

# 3. Run the script
python3 run_tracker_autorestart.py

# 4. Monitor logs in another terminal
tail -f monitor_output.csv

# 5. Query data in MariaDB
mysql -h 192.168.10.52 -u admin -p torrent_monitor
SELECT COUNT(*) FROM report_table;
```

## 🎯 Use Cases

1. **Long-Duration Tests**: Monitor peers for hours/days without completing downloads
2. **Swarm Analysis**: Observe how swarms evolve over time
3. **Pattern Detection**: Identify peak times, most active regions
4. **Space Savings**: No need to store complete files
5. **Realistic Simulation**: Behave like a real peer that's always downloading

## 📞 Support

For issues or questions:
1. Check logs with `FORCE_VERBOSE = True`
2. Test first with `run_tracker_inproc.py` (simpler)
3. Verify all dependencies are installed
4. Confirm MariaDB is accessible

---

**Developed to maintain continuous monitoring of BitTorrent swarms** 🚀

