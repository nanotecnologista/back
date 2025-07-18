#!/usr/bin/env python3
"""
Script para testar conexão e inicialização do banco de dados.
"""
import sys
import os

# Adicionar o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.modules.database.database import test_database, init_database, db_manager

def main():
    print("=== Teste do Banco de Dados ===")
    
    # Testar conexão
    print("\n1. Testando conexão...")
    try:
        success = test_database()
        print(f"   Conexão: {'✓ OK' if success else '✗ FALHOU'}")
    except Exception as e:
        print(f"   Conexão: ✗ ERRO - {e}")
        return False
    
    if not success:
        print("   Não foi possível conectar ao banco de dados.")
        return False
    
    # Criar tabelas
    print("\n2. Criando tabelas...")
    try:
        init_success = init_database()
        print(f"   Tabelas: {'✓ OK' if init_success else '✗ FALHOU'}")
    except Exception as e:
        print(f"   Tabelas: ✗ ERRO - {e}")
        return False
    
    # Obter informações do banco
    print("\n3. Informações do banco:")
    try:
        info = db_manager.get_database_info()
        print(f"   Tipo: {info.get('type', 'N/A')}")
        print(f"   Database: {info.get('database', 'N/A')}")
        print(f"   Host: {info.get('host', 'N/A')}")
        print(f"   Port: {info.get('port', 'N/A')}")
        
        if 'table_counts' in info:
            print("   Contagem de tabelas:")
            for table, count in info['table_counts'].items():
                print(f"     {table}: {count}")
    except Exception as e:
        print(f"   Erro ao obter informações: {e}")
    
    print("\n=== Teste concluído com sucesso! ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

