#!/usr/bin/env python3
"""
Test script to verify if GeoLite2 databases are working correctly.
"""

import geoip2.database
import subprocess
import json
import os

def test_geoip2_city():
    """Test GeoLite2-City database using geoip2 library."""
    print("🔍 Testing GeoLite2-City with geoip2...")
    
    try:
        reader = geoip2.database.Reader('dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb')
        
        # Test with known IPs
        test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in test_ips:
            try:
                response = reader.city(ip)
                print(f"  ✅ {ip}: {response.country.name} - {response.city.name}")
            except Exception as e:
                print(f"  ❌ {ip}: Error - {e}")
        
        reader.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading GeoLite2-City database: {e}")
        return False

def test_geoip2_asn():
    """Test GeoLite2-ASN database using geoip2 library."""
    print("\n🔍 Testing GeoLite2-ASN with geoip2...")
    
    try:
        reader = geoip2.database.Reader('dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb')
        
        # Test with known IPs
        test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in test_ips:
            try:
                response = reader.asn(ip)
                print(f"  ✅ {ip}: AS{response.autonomous_system_number} - {response.autonomous_system_organization}")
            except Exception as e:
                print(f"  ❌ {ip}: Error - {e}")
        
        reader.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Error loading GeoLite2-ASN database: {e}")
        return False

def test_mmdbinspect():
    """Test mmdbinspect command."""
    print("\n🔍 Testing mmdbinspect...")
    
    # Check if mmdbinspect is available
    try:
        result = subprocess.run(['mmdbinspect', '--version'], 
                              capture_output=True, text=True, timeout=5)
        print(f"  ✅ mmdbinspect available: {result.stdout.strip()}")
    except Exception as e:
        print(f"  ❌ mmdbinspect not found: {e}")
        return False
    
    # Testa com GeoLite2-City
    try:
        cmd = f"mmdbinspect -db dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb 8.8.8.8"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ mmdbinspect GeoLite2-City working")
            print(f"     Data: {data}")
        else:
            print(f"  ❌ Error in mmdbinspect GeoLite2-City: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error executing mmdbinspect GeoLite2-City: {e}")
        return False
    
    # Testa com GeoLite2-ASN
    try:
        cmd = f"mmdbinspect -db dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb 8.8.8.8"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ mmdbinspect GeoLite2-ASN working")
            print(f"     Data: {data}")
        else:
            print(f"  ❌ Error in mmdbinspect GeoLite2-ASN: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error executing mmdbinspect GeoLite2-ASN: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Starting GeoLite2 database tests...")
    print("=" * 50)
    
    # Check if files exist
    city_path = 'dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb'
    asn_path = 'dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb'
    
    if not os.path.exists(city_path):
        print(f"❌ File not found: {city_path}")
        return False
    
    if not os.path.exists(asn_path):
        print(f"❌ File not found: {asn_path}")
        return False
    
    print(f"✅ Files found:")
    print(f"   - {city_path}")
    print(f"   - {asn_path}")
    
    # Execute tests
    city_ok = test_geoip2_city()
    asn_ok = test_geoip2_asn()
    mmdbinspect_ok = test_mmdbinspect()
    
    print("\n" + "=" * 50)
    print("📊 Test results:")
    print(f"   GeoLite2-City (geoip2): {'✅ OK' if city_ok else '❌ FALHOU'}")
    print(f"   GeoLite2-ASN (geoip2): {'✅ OK' if asn_ok else '❌ FALHOU'}")
    print(f"   mmdbinspect: {'✅ OK' if mmdbinspect_ok else '❌ FAILED'}")
    
    if city_ok and asn_ok and mmdbinspect_ok:
        print("\n🎉 All tests passed! The databases are working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed. Check the configurations.")
        return False

if __name__ == "__main__":
    main()
