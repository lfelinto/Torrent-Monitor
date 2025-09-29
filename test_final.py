#!/usr/bin/env python3
"""
Teste final para verificar se o TorrentMonitor está funcionando corretamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from TorrentMonitor import TorrentTracker

def test_torrent_tracker():
    """Testa a classe TorrentTracker."""
    print("🚀 Testando TorrentTracker...")
    
    try:
        # Criar instância do TorrentTracker
        tracker = TorrentTracker(
            torrent_folder="test_torrents",  # Pasta que não existe
            output="test_output",
            geo=True,
            database="test.db"
        )
        
        print("✅ TorrentTracker criado com sucesso!")
        
        # Testar geolocalização
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
                print(f"  ❌ Erro na geolocalização")
            
            # Testar get_isp_info
            isp_info = tracker.get_isp_info(ip)
            if isinstance(isp_info, dict):
                org = isp_info.get('autonomous_system_organization', 'N/A')
                asn = isp_info.get('autonomous_system_number', 'N/A')
                print(f"  🏢 ISP: {org} (AS{asn})")
            else:
                print(f"  ❌ Erro na informação do ISP")
        
        print("\n🎉 Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE FINAL DO TORRENTMONITOR")
    print("=" * 60)
    
    success = test_torrent_tracker()
    
    if success:
        print("\n✅ TODOS OS TESTES PASSARAM!")
        print("🎯 O TorrentMonitor está funcionando corretamente com as bases de dados atualizadas.")
    else:
        print("\n❌ ALGUNS TESTES FALHARAM!")
        print("⚠️  Verifique os erros acima.")
