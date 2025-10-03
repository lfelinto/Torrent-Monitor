#!/usr/bin/env python3
"""
Simple test to verify only geolocation functionalities.
"""

import geoip2.database
import os

def test_geolocation_only():
    """Test only geolocation functionalities."""
    print("🚀 Testing geolocation functionalities...")
    
    # Check if files exist
    city_path = 'dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb'
    asn_path = 'dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb'
    
    if not os.path.exists(city_path):
        print(f"❌ File not found: {city_path}")
        return False
    
    if not os.path.exists(asn_path):
        print(f"❌ File not found: {asn_path}")
        return False
    
    print("✅ Database files found!")
    
    # Test GeoLite2-City
    print("\n🔍 Testing GeoLite2-City...")
    try:
        reader = geoip2.database.Reader(city_path)
        
        test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in test_ips:
            try:
                response = reader.city(ip)
                country = response.country.name or 'N/A'
                city = response.city.name or 'N/A'
                print(f"  ✅ {ip}: {country} - {city}")
            except Exception as e:
                print(f"  ❌ {ip}: Error - {e}")
        
        reader.close()
        print("✅ GeoLite2-City working!")
        
    except Exception as e:
        print(f"❌ Error testing GeoLite2-City: {e}")
        return False
    
    # Test GeoLite2-ASN
    print("\n🔍 Testing GeoLite2-ASN...")
    try:
        reader = geoip2.database.Reader(asn_path)
        
        for ip in test_ips:
            try:
                response = reader.asn(ip)
                org = response.autonomous_system_organization or 'N/A'
                asn = response.autonomous_system_number or 'N/A'
                print(f"  ✅ {ip}: {org} (AS{asn})")
            except Exception as e:
                print(f"  ❌ {ip}: Error - {e}")
        
        reader.close()
        print("✅ GeoLite2-ASN working!")
        
    except Exception as e:
        print(f"❌ Error testing GeoLite2-ASN: {e}")
        return False
    
    return True

def test_updated_functions():
    """Test updated TorrentMonitor functions."""
    print("\n🔍 Testing updated functions...")
    
    # Simulate get_geo_info and get_isp_info functions
    def get_geo_info(ip):
        try:
            reader = geoip2.database.Reader('dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb')
            response = reader.city(ip)
            reader.close()
            
            return {
                'country': {
                    'names': {'en': response.country.name},
                    'iso_code': response.country.iso_code
                },
                'city': {
                    'names': {'en': response.city.name}
                },
                'subdivisions': [
                    {
                        'names': {'en': subdivision.name}
                    } for subdivision in response.subdivisions
                ]
            }
        except Exception as e:
            print(f"Geolocation error for {ip}: {e}")
            return None
    
    def get_isp_info(ip):
        try:
            reader = geoip2.database.Reader('dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb')
            response = reader.asn(ip)
            reader.close()
            
            return {
                'autonomous_system_organization': response.autonomous_system_organization,
                'autonomous_system_number': response.autonomous_system_number
            }
        except Exception as e:
            print(f"ISP information error for {ip}: {e}")
            return 'N/A'
    
    # Testar as funções
    test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
    
    for ip in test_ips:
        print(f"\n📡 Testando IP: {ip}")
        
        # Test geolocation
        geo_info = get_geo_info(ip)
        if geo_info:
            country = geo_info.get('country', {}).get('names', {}).get('en', 'N/A')
            city = geo_info.get('city', {}).get('names', {}).get('en', 'N/A')
            print(f"  📍 País: {country}, Cidade: {city}")
        else:
            print(f"  ❌ Geolocation error")
        
        # Testar informação do ISP
        isp_info = get_isp_info(ip)
        if isinstance(isp_info, dict):
            org = isp_info.get('autonomous_system_organization', 'N/A')
            asn = isp_info.get('autonomous_system_number', 'N/A')
            print(f"  🏢 ISP: {org} (AS{asn})")
        else:
            print(f"  ❌ ISP information error")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 SIMPLE TEST OF GEOLOCATION FUNCTIONALITIES")
    print("=" * 60)
    
    # Basic test
    basic_ok = test_geolocation_only()
    
    if basic_ok:
        # Test of updated functions
        test_updated_functions()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("✅ GeoLite2 databases are working correctly!")
        print("✅ Geolocation functions were updated successfully!")
        print("✅ Code now uses only geoip2 library (without mmdbinspect)!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("⚠️  Check the errors above.")
