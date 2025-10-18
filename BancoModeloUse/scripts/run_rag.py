#!/usr/bin/env python3
"""
Script para testar e executar RAG
"""
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from core.rag.pipeline import RAGPipeline

def testar_rag():
    """Testa o pipeline RAG"""
    print("=== Testando Pipeline RAG ===")
    
    # Inicializar pipeline
    pipeline = RAGPipeline()
    
    # Consultas de teste
    consultas_teste = [
        "Quais foram as vendas do último mês?",
        "Como está a produção da máquina 1?",
        "Qual a correlação entre custos e eficiência?",
        "Mostre o dashboard executivo"
    ]
    
    print("🧪 Executando testes...")
    
    for i, consulta in enumerate(consultas_teste, 1):
        print(f"\n--- Teste {i}: {consulta} ---")
        
        try:
            resultado = pipeline.processar_consulta(consulta)
            
            if "erro" in resultado:
                print(f"❌ Erro: {resultado['erro']}")
            else:
                print(f"✅ Sucesso!")
                print(f"📊 Agente: {resultado.get('agente_destino', 'N/A')}")
                print(f"📊 Tipo: {resultado.get('tipo_consulta', 'N/A')}")
                print(f"📊 Resultado: {resultado.get('resultado', {})}")
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
    
    print("\n=== Teste Concluído ===")

def testar_agentes():
    """Testa agentes individualmente"""
    print("=== Testando Agentes ===")
    
    pipeline = RAGPipeline()
    
    # Testar orquestrador
    print("\n--- Testando Orquestrador ---")
    try:
        resultado = pipeline.orquestrador.processar_consulta("Quais foram as vendas?")
        print(f"✅ Orquestrador: {resultado}")
    except Exception as e:
        print(f"❌ Erro no orquestrador: {e}")
    
    # Testar agente financeiro
    print("\n--- Testando Agente Financeiro ---")
    try:
        resultado = pipeline.agente_financeiro.processar_consulta("vendas", {"data_inicio": "2025-01-01", "data_fim": "2025-01-31"})
        print(f"✅ Agente Financeiro: {resultado}")
    except Exception as e:
        print(f"❌ Erro no agente financeiro: {e}")
    
    # Testar agente industrial
    print("\n--- Testando Agente Industrial ---")
    try:
        resultado = pipeline.agente_industrial.processar_consulta("producao", {"maquina_id": 1})
        print(f"✅ Agente Industrial: {resultado}")
    except Exception as e:
        print(f"❌ Erro no agente industrial: {e}")
    
    # Testar agente finalizador
    print("\n--- Testando Agente Finalizador ---")
    try:
        respostas = [
            {"agente": "financeiro", "resultado": {"tipo": "vendas", "total": 1000}},
            {"agente": "industrial", "resultado": {"tipo": "producao", "total": 500}}
        ]
        resultado = pipeline.agente_finalizador.consolidar_respostas(respostas)
        print(f"✅ Agente Finalizador: {resultado}")
    except Exception as e:
        print(f"❌ Erro no agente finalizador: {e}")

def testar_ferramentas():
    """Testa ferramentas RAG"""
    print("=== Testando Ferramentas ===")
    
    pipeline = RAGPipeline()
    
    # Testar ferramentas financeiras
    print("\n--- Testando Ferramentas Financeiras ---")
    try:
        resultado = pipeline.ferramentas_financeiras.query_financeira("vendas", {"data_inicio": "2025-01-01", "data_fim": "2025-01-31"})
        print(f"✅ Query Financeira: {resultado}")
    except Exception as e:
        print(f"❌ Erro na query financeira: {e}")
    
    # Testar ferramentas industriais
    print("\n--- Testando Ferramentas Industriais ---")
    try:
        resultado = pipeline.ferramentas_industriais.query_operacional("producao", {"maquina_id": 1})
        print(f"✅ Query Operacional: {resultado}")
    except Exception as e:
        print(f"❌ Erro na query operacional: {e}")
    
    # Testar ferramentas de integração
    print("\n--- Testando Ferramentas de Integração ---")
    try:
        resultado = pipeline.ferramentas_integracao.join_financeiro_industrial("vendas_producao", {"data_inicio": "2025-01-01", "data_fim": "2025-01-31"})
        print(f"✅ Join Financeiro-Industrial: {resultado}")
    except Exception as e:
        print(f"❌ Erro no join: {e}")

def mostrar_estatisticas():
    """Mostra estatísticas do pipeline"""
    print("=== Estatísticas do Pipeline ===")
    
    pipeline = RAGPipeline()
    
    try:
        estatisticas = pipeline.obter_estatisticas_pipeline()
        print(f"📊 Total de consultas: {estatisticas.get('total_consultas', 0)}")
        print(f"📊 Consultas por agente: {estatisticas.get('consultas_por_agente', {})}")
        print(f"📊 Taxa de sucesso: {estatisticas.get('taxa_sucesso', 0)}%")
        print(f"📊 Tempo médio: {estatisticas.get('tempo_medio', 0)}s")
        
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")

def consulta_interativa():
    """Modo interativo para consultas"""
    print("=== Modo Interativo RAG ===")
    print("Digite suas consultas (digite 'sair' para encerrar)")
    
    pipeline = RAGPipeline()
    
    while True:
        try:
            consulta = input("\n🔍 Consulta: ").strip()
            
            if consulta.lower() in ['sair', 'exit', 'quit']:
                print("👋 Encerrando modo interativo...")
                break
            
            if not consulta:
                continue
            
            print("🔄 Processando...")
            resultado = pipeline.processar_consulta(consulta)
            
            if "erro" in resultado:
                print(f"❌ Erro: {resultado['erro']}")
            else:
                print(f"✅ Agente: {resultado.get('agente_destino', 'N/A')}")
                print(f"📊 Resultado: {resultado.get('resultado', {})}")
                
        except KeyboardInterrupt:
            print("\n👋 Encerrando modo interativo...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

def main():
    """Função principal"""
    if len(sys.argv) < 2:
        print("Uso: python run_rag.py <comando>")
        print("Comandos disponíveis:")
        print("  testar      - Testa o pipeline RAG")
        print("  agentes     - Testa agentes individualmente")
        print("  ferramentas - Testa ferramentas RAG")
        print("  estatisticas - Mostra estatísticas")
        print("  interativo  - Modo interativo para consultas")
        return
    
    comando = sys.argv[1].lower()
    
    if comando == "testar":
        testar_rag()
    elif comando == "agentes":
        testar_agentes()
    elif comando == "ferramentas":
        testar_ferramentas()
    elif comando == "estatisticas":
        mostrar_estatisticas()
    elif comando == "interativo":
        consulta_interativa()
    else:
        print(f"❌ Comando inválido: {comando}")

if __name__ == "__main__":
    main()
