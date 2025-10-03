# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2025-10-03

### Added
- 🔁 **Auto-Restart Runner** (`run_tracker_autorestart.py`)
  - Automatically restarts downloads when reaching 90% completion (configurable)
  - Intelligent progress monitoring with real-time statistics
  - Automatic cleanup of Downloads folder
  - Active download verification to prevent unnecessary restarts
  - Configurable thresholds and intervals
  - Detailed progress logs and restart counter
  
- 📚 **Comprehensive Documentation**
  - `AUTO_RESTART_README.md` with full usage guide
  - Updated main `README.md` with new features
  - Enhanced troubleshooting section
  
- ⚡ **Enhanced TorrentMonitor**
  - Exposed `handles` attribute for external monitoring
  - Better integration with runner scripts

### Changed
- 🌍 **All Comments Converted to English**
  - Standardized codebase language
  - Improved international collaboration
  - Better code readability
  
- 📦 **Updated Dependencies**
  - Consolidated `requirements.txt` with exact versions
  - Removed duplicate `requirements_updated.txt`
  - Added inline documentation for each dependency
  
- 🧹 **Cleaned Up Repository**
  - Removed temporary files and caches
  - Deleted unused database (GeoLite2-Country)
  - Removed test output files
  - Better `.gitignore` configuration

### Removed
- 🗑️ **Cleaned Temporary Files**
  - `__pycache__/` - Python cache
  - `session.session` - Telegram session
  - `monitor_output.csv` - Test output
  - `Monitor_test.db` - Test database
  - `notified_peers.txt` - Temporary cache
  - `requirements_updated.txt` - Duplicate file
  - `dbs/GeoLite2-Country_20250926/` - Unused database

### Fixed
- 🐛 **Bug Fixes**
  - Fixed handle exposure for external monitoring
  - Improved error handling in auto-restart
  - Better folder size calculation
  - Enhanced download state detection

## [2.0.0] - 2025-09-29

### Added
- Fixed database paths for GeoLite2 databases
- Modernized dependencies
- Enhanced data storage with real-time saving
- Improved geolocation handling with native `geoip2`
- Better performance and security
- Comprehensive testing suite
- In-process runner for easier testing

### Changed
- Updated to Python 3.8+ compatibility
- Replaced deprecated `mmdbinspect` with `geoip2`
- Organized database structure in `dbs/` directory
- Enhanced logging and error handling

### Fixed
- Database saving issues
- Geolocation data retrieval
- MariaDB integration
- HTTP security with HTTPS

## [1.0.0] - Original

### Added
- Initial release from N4rr34n6/Torrent-Monitor
- Basic peer monitoring functionality
- Telegram integration
- CSV and SQLite output
- Geolocation support
- Multiple torrent client simulation

---

## Version Comparison

| Feature | v1.0 | v2.0 | v2.1 |
|---------|------|------|------|
| Basic Monitoring | ✅ | ✅ | ✅ |
| Geolocation | ✅ | ✅ | ✅ |
| MariaDB Support | ❌ | ✅ | ✅ |
| In-Process Runner | ❌ | ✅ | ✅ |
| Auto-Restart | ❌ | ❌ | ✅ |
| Progress Monitoring | ❌ | ❌ | ✅ |
| English Comments | ❌ | ❌ | ✅ |
| Clean Codebase | ❌ | ⚠️ | ✅ |

## Future Plans

### Planned Features
- [ ] Web dashboard for monitoring
- [ ] Multi-threaded torrent handling
- [ ] Advanced analytics and reporting
- [ ] REST API for remote control
- [ ] Docker containerization
- [ ] Prometheus metrics export
- [ ] Custom alerting rules
- [ ] Peer relationship mapping
- [ ] Historical data visualization

### Under Consideration
- [ ] GUI application
- [ ] Cloud storage integration
- [ ] Machine learning for pattern detection
- [ ] Distributed monitoring support
- [ ] Plugin system for extensions

---

**Note**: This project is licensed under AGPL-3.0. See [LICENSE](LICENSE) for details.

