#main.py
import argparse
import time
import sys
from typing import List
import psutil
from Scripts.factory import StrategyFactory
from model import RelatorioFinanceiro
from Scripts.services.context import RelatoriosFinanceirosContext
from Scripts.output.salva_csv import gerar_csv_consolidado

def processar_empresa(empresa: str, apenas_extrair: bool = False, 
                     usar_arquivos_existentes: bool = False, 
                     max_workers: int = None,
                     usar_cache: bool = True) -> List[RelatorioFinanceiro]:
    """
    Processa os relatórios financeiros de uma única empresa, com opção de apenas extrair ou usar PDFs já baixados.

    Parâmetros:
        empresa (str): Nome da empresa a ser processada.
        apenas_extrair (bool, opcional): Se True, apenas realiza a raspagem (download dos PDFs), sem processamento posterior.
        usar_arquivos_existentes (bool, opcional): Se True, ignora a raspagem e utiliza arquivos PDFs já existentes em disco.
        max_workers (int, opcional): Número máximo de processos paralelos para processamento.
        usar_cache (bool, opcional): Se True, utiliza cache para evitar reprocessamento de PDFs.

    Retorna:
        List[RelatorioFinanceiro]: Lista de objetos contendo os dados dos relatórios processados.
    """
    
    print(f"\n{'=' * 60}")
    print(f"Iniciando processamento da empresa: {empresa}")
    print(f"{'=' * 60}")
    inicio = time.time()

    # Criar o contexto com as novas opções
    context = RelatoriosFinanceirosContext(
        strategy=None,  # Será definido depois
        max_workers=max_workers, 
        usar_cache=usar_cache
    )
    context.strategy = StrategyFactory.get_strategy(empresa)

    if usar_arquivos_existentes:
        print("Pulando raspagem. Usando arquivos já existentes...")
        relatorios = context.processar_relatorios_existentes(empresa)
    else:
        print(f"Raspando relatórios de {empresa}...")
        relatorios = context.executar_raspagem()
        print(f"{len(relatorios)} relatórios extraídos.")

    if apenas_extrair:
        print("Processamento dos relatórios ignorado (--apenas-extrair)")
        relatorios_processados = relatorios
    else:
        print("Processando os relatórios...")
        relatorios_processados = context.processar_relatorios()
        print(f"{len(relatorios_processados)} relatórios processados.")

    print(f"Tempo total: {time.time() - inicio:.2f} segundos")
    return relatorios_processados

def listar_empresas_disponiveis(empresas: List[str]):
    """
    Exibe na tela a lista de empresas suportadas pelo sistema.

    Parâmetros:
        empresas (list[str]): Lista de nomes de empresas suportadas.
    """
    
    print("\nEmpresas disponíveis:")
    for e in empresas:
        print(f" - {e}")


def main():
    """
    Função principal que executa o pipeline de extração e processamento de relatórios financeiros.

    Permite a escolha de empresas específicas, apenas extração de PDFs ou execução completa com geração de CSV.

    Argumentos da linha de comando:
    --empresas: Lista de empresas a processar. Se omitido, todas as empresas serão processadas.
    --apenas-extrair: Se definido, apenas os PDFs serão baixados, sem extrair texto ou gerar CSV.
    --usar-existentes: Se definido, pula a raspagem e usa os arquivos já baixados no disco.
    --listar: Lista as empresas disponíveis e encerra o programa.
    --csv: Nome do arquivo CSV de saída consolidada (default: relatorios_consolidados.csv)
    --workers: Número de processos paralelos para processamento (default: núcleos disponíveis - 1)
    --sem-cache: Desativa o cache de extração de PDF
    """

    parser = argparse.ArgumentParser(description="Sistema de Extração de Relatórios Financeiros")
    parser.add_argument("--empresas", type=str, nargs="*", help="Empresas específicas a processar (opcional)")
    parser.add_argument("--apenas-extrair", action="store_true", help="Somente extrair PDFs, sem processamento")
    parser.add_argument("--usar-existentes", action="store_true", help="Usar PDFs já baixados sem raspagem")
    parser.add_argument("--listar", action="store_true", help="Listar empresas disponíveis e sair")
    parser.add_argument("--csv", type=str, default="relatorios_consolidados.csv", help="Arquivo CSV de saída")
    parser.add_argument("--workers", type=int, default=None, help="Número de processos para processamento paralelo")
    parser.add_argument("--sem-cache", action="store_true", help="Desativa o cache de extração de PDF")
    
    args = parser.parse_args()

    # Determinar número de CPU cores disponíveis
    cpu_count = psutil.cpu_count(logical=False) or 2  # Físicos, ou 2 se não for possível determinar
    default_workers = max(1, cpu_count - 1)
    max_workers = args.workers if args.workers is not None else default_workers
    
    print(f"Configuração do sistema:")
    print(f"- CPUs disponíveis: {cpu_count}")
    print(f"- Workers paralelos: {max_workers}")
    print(f"- Cache de extração: {'Desativado' if args.sem_cache else 'Ativado'}")

    empresas_disponiveis = StrategyFactory.listar_empresas()

    if args.listar:
        listar_empresas_disponiveis(empresas_disponiveis)
        return

    empresas_alvo = args.empresas or empresas_disponiveis

    # Verificar se todas são válidas
    for emp in empresas_alvo:
        if emp not in empresas_disponiveis:
            print(f"ERRO: Empresa inválida: '{emp}'. Use --listar para opções válidas.")
            sys.exit(1)

    relatorios_totais = []
    inicio_geral = time.time()

    for empresa in empresas_alvo:
        try:
            relatorios = processar_empresa(
                empresa, 
                args.apenas_extrair, 
                args.usar_existentes,
                max_workers,
                not args.sem_cache
            )
            relatorios_totais.extend(relatorios)
        except Exception as e:
            print(f"ERRO ao processar '{empresa}': {e}")
            import traceback
            traceback.print_exc()

    if not args.apenas_extrair:
        gerar_csv_consolidado(relatorios_totais, args.csv)

    print(f"\n{'=' * 60}")
    print("Processamento concluído!")
    print(f"Empresas processadas: {len(empresas_alvo)}")
    print(f"Relatórios totais extraídos: {len(relatorios_totais)}")
    print(f"Tempo total de execução: {time.time() - inicio_geral:.2f} segundos")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    processar_empresa("Gerdau", apenas_extrair=True)