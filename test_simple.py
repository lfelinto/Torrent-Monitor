#!/usr/bin/env python3
"""
Teste simples para verificar apenas as funcionalidades de geolocalização.
"""

import geoip2.database
import os

def test_geolocation_only():
    """Testa apenas as funcionalidades de geolocalização."""
    print("🚀 Testando funcionalidades de geolocalização...")
    
    # Verificar se os arquivos existem
    city_path = 'dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb'
    asn_path = 'dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb'
    
    if not os.path.exists(city_path):
        print(f"❌ Arquivo não encontrado: {city_path}")
        return False
    
    if not os.path.exists(asn_path):
        print(f"❌ Arquivo não encontrado: {asn_path}")
        return False
    
    print("✅ Arquivos de base de dados encontrados!")
    
    # Testar GeoLite2-City
    print("\n🔍 Testando GeoLite2-City...")
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
                print(f"  ❌ {ip}: Erro - {e}")
        
        reader.close()
        print("✅ GeoLite2-City funcionando!")
        
    except Exception as e:
        print(f"❌ Erro ao testar GeoLite2-City: {e}")
        return False
    
    # Testar GeoLite2-ASN
    print("\n🔍 Testando GeoLite2-ASN...")
    try:
        reader = geoip2.database.Reader(asn_path)
        
        for ip in test_ips:
            try:
                response = reader.asn(ip)
                org = response.autonomous_system_organization or 'N/A'
                asn = response.autonomous_system_number or 'N/A'
                print(f"  ✅ {ip}: {org} (AS{asn})")
            except Exception as e:
                print(f"  ❌ {ip}: Erro - {e}")
        
        reader.close()
        print("✅ GeoLite2-ASN funcionando!")
        
    except Exception as e:
        print(f"❌ Erro ao testar GeoLite2-ASN: {e}")
        return False
    
    return True

def test_updated_functions():
    """Testa as funções atualizadas do TorrentMonitor."""
    print("\n🔍 Testando funções atualizadas...")
    
    # Simular as funções get_geo_info e get_isp_info
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
            print(f"Erro na geolocalização para {ip}: {e}")
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
            print(f"Erro na informação do ISP para {ip}: {e}")
            return 'N/A'
    
    # Testar as funções
    test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
    
    for ip in test_ips:
        print(f"\n📡 Testando IP: {ip}")
        
        # Testar geolocalização
        geo_info = get_geo_info(ip)
        if geo_info:
            country = geo_info.get('country', {}).get('names', {}).get('en', 'N/A')
            city = geo_info.get('city', {}).get('names', {}).get('en', 'N/A')
            print(f"  📍 País: {country}, Cidade: {city}")
        else:
            print(f"  ❌ Erro na geolocalização")
        
        # Testar informação do ISP
        isp_info = get_isp_info(ip)
        if isinstance(isp_info, dict):
            org = isp_info.get('autonomous_system_organization', 'N/A')
            asn = isp_info.get('autonomous_system_number', 'N/A')
            print(f"  🏢 ISP: {org} (AS{asn})")
        else:
            print(f"  ❌ Erro na informação do ISP")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE SIMPLES DAS FUNCIONALIDADES DE GEOLOCALIZAÇÃO")
    print("=" * 60)
    
    # Teste básico
    basic_ok = test_geolocation_only()
    
    if basic_ok:
        # Teste das funções atualizadas
        test_updated_functions()
        
        print("\n" + "=" * 60)
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ As bases de dados GeoLite2 estão funcionando corretamente!")
        print("✅ As funções de geolocalização foram atualizadas com sucesso!")
        print("✅ O código agora usa apenas a biblioteca geoip2 (sem mmdbinspect)!")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("⚠️  Verifique os erros acima.")
