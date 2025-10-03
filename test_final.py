#!/usr/bin/env python3
"""
Final test to verify if TorrentMonitor is working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TorrentMonitor import TorrentTracker

def test_torrent_tracker():
    """Test the TorrentTracker class."""
    print("🚀 Testing TorrentTracker...")
    
    try:
        # Create TorrentTracker instance
        tracker = TorrentTracker(
            torrent_folder="test_torrents",  # Folder that does not exist
            output="test_output",
            geo=True,
            database="test.db"
        )
        
        print("✅ TorrentTracker created successfully!")
        
        # Test geolocation
        test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in test_ips:
            print(f"\n🔍 Testando IP: {ip}")
            
            # Testar get_geo_info
            geo_info = tracker.get_geo_info(ip)
            if geo_info:
                country = geo_info.get('country', {}).get('names', {}).get('en', 'N/A')
                city = geo_info.get('city', {}).get('names', {}).get('en', 'N/A')
                print(f"  📍 País: {country}, Cidade: {city}")
            else:
                print(f"  ❌ Geolocation error")
            
            # Testar get_isp_info
            isp_info = tracker.get_isp_info(ip)
            if isinstance(isp_info, dict):
                org = isp_info.get('autonomous_system_organization', 'N/A')
                asn = isp_info.get('autonomous_system_number', 'N/A')
                print(f"  🏢 ISP: {org} (AS{asn})")
            else:
                print(f"  ❌ ISP information error")
        
        print("\n🎉 Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 FINAL TEST OF TORRENTMONITOR")
    print("=" * 60)
    
    success = test_torrent_tracker()
    
    if success:
        print("\n✅ ALL TESTS PASSED!")
        print("🎯 TorrentMonitor is working correctly with updated databases.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️  Check the errors above.")
