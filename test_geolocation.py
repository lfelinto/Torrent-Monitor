#!/usr/bin/env python3
"""
Script de teste para verificar se as bases de dados GeoLite2 estão funcionando corretamente.
"""

import geoip2.database
import subprocess
import json
import os

def test_geoip2_city():
    """Testa a base GeoLite2-City usando a biblioteca geoip2."""
    print("🔍 Testando GeoLite2-City com geoip2...")
    
    try:
        reader = geoip2.database.Reader('dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb')
        
        # Teste com IPs conhecidos
        test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in test_ips:
            try:
                response = reader.city(ip)
                print(f"  ✅ {ip}: {response.country.name} - {response.city.name}")
            except Exception as e:
                print(f"  ❌ {ip}: Erro - {e}")
        
        reader.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao carregar base GeoLite2-City: {e}")
        return False

def test_geoip2_asn():
    """Testa a base GeoLite2-ASN usando a biblioteca geoip2."""
    print("\n🔍 Testando GeoLite2-ASN com geoip2...")
    
    try:
        reader = geoip2.database.Reader('dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb')
        
        # Teste com IPs conhecidos
        test_ips = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
        
        for ip in test_ips:
            try:
                response = reader.asn(ip)
                print(f"  ✅ {ip}: AS{response.autonomous_system_number} - {response.autonomous_system_organization}")
            except Exception as e:
                print(f"  ❌ {ip}: Erro - {e}")
        
        reader.close()
        return True
        
    except Exception as e:
        print(f"  ❌ Erro ao carregar base GeoLite2-ASN: {e}")
        return False

def test_mmdbinspect():
    """Testa o comando mmdbinspect."""
    print("\n🔍 Testando mmdbinspect...")
    
    # Verifica se o mmdbinspect está disponível
    try:
        result = subprocess.run(['mmdbinspect', '--version'], 
                              capture_output=True, text=True, timeout=5)
        print(f"  ✅ mmdbinspect disponível: {result.stdout.strip()}")
    except Exception as e:
        print(f"  ❌ mmdbinspect não encontrado: {e}")
        return False
    
    # Testa com GeoLite2-City
    try:
        cmd = f"mmdbinspect -db dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb 8.8.8.8"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ mmdbinspect GeoLite2-City funcionando")
            print(f"     Dados: {data}")
        else:
            print(f"  ❌ Erro no mmdbinspect GeoLite2-City: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao executar mmdbinspect GeoLite2-City: {e}")
        return False
    
    # Testa com GeoLite2-ASN
    try:
        cmd = f"mmdbinspect -db dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb 8.8.8.8"
        result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print(f"  ✅ mmdbinspect GeoLite2-ASN funcionando")
            print(f"     Dados: {data}")
        else:
            print(f"  ❌ Erro no mmdbinspect GeoLite2-ASN: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao executar mmdbinspect GeoLite2-ASN: {e}")
        return False
    
    return True

def main():
    """Função principal de teste."""
    print("🚀 Iniciando testes das bases de dados GeoLite2...")
    print("=" * 50)
    
    # Verifica se os arquivos existem
    city_path = 'dbs/GeoLite2-City_20250926/GeoLite2-City.mmdb'
    asn_path = 'dbs/GeoLite2-ASN_20250929/GeoLite2-ASN.mmdb'
    
    if not os.path.exists(city_path):
        print(f"❌ Arquivo não encontrado: {city_path}")
        return False
    
    if not os.path.exists(asn_path):
        print(f"❌ Arquivo não encontrado: {asn_path}")
        return False
    
    print(f"✅ Arquivos encontrados:")
    print(f"   - {city_path}")
    print(f"   - {asn_path}")
    
    # Executa os testes
    city_ok = test_geoip2_city()
    asn_ok = test_geoip2_asn()
    mmdbinspect_ok = test_mmdbinspect()
    
    print("\n" + "=" * 50)
    print("📊 Resultados dos testes:")
    print(f"   GeoLite2-City (geoip2): {'✅ OK' if city_ok else '❌ FALHOU'}")
    print(f"   GeoLite2-ASN (geoip2): {'✅ OK' if asn_ok else '❌ FALHOU'}")
    print(f"   mmdbinspect: {'✅ OK' if mmdbinspect_ok else '❌ FALHOU'}")
    
    if city_ok and asn_ok and mmdbinspect_ok:
        print("\n🎉 Todos os testes passaram! As bases de dados estão funcionando corretamente.")
        return True
    else:
        print("\n⚠️  Alguns testes falharam. Verifique as configurações.")
        return False

if __name__ == "__main__":
    main()
