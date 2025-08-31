import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List
from model import RelatorioFinanceiro  

def gerar_csv_consolidado(relatorios: List[RelatorioFinanceiro], caminho_saida: str):
    if not relatorios:
        print("Nenhum relatório foi processado. CSV não gerado.")
        return

    df = pd.DataFrame([{
        "empresa": r.empresa,
        "categoria": r.categoria,
        "ano": r.ano,
        "trimestre": r.trimestre,
        "url": r.download_url,
        "arquivo": r.caminho_arquivo,
        "paginas": r.num_paginas,
        "data_extracao": r.data_extracao,
        "checksum": r.checksum
    } for r in relatorios])

    df.to_csv(caminho_saida, index=False)
    print(f"\nCSV consolidado gerado com sucesso: {caminho_saida}")
    print(f"Total de relatórios: {len(relatorios)}")

def salvar_relatorios_csv(empresa, pasta_base="pdfs", caminho_saida=None):
    
    """
    Gera um CSV resumido com 1 linha por PDF extraído.

    Args:
        empresa (str): Nome da empresa (corresponde à pasta dentro de 'pdfs/')
        pasta_base (str): Pasta base onde estão os dados.
        caminho_saida (str, optional): Caminho do arquivo CSV a ser gerado.
    """
    empresa_path = Path(pasta_base) / empresa
    if not empresa_path.exists():
        print(f"Pasta da empresa '{empresa}' não encontrada em {pasta_base}.")
        return

    registros = []

    # Busca todos os JSONs
    for json_path in empresa_path.glob("**/jsons/*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                dados = json.load(f)

            file_name = json_path.name

            registro = {
                "empresa": empresa,
                "ano": dados.get("ano", ""),
                "trimestre": dados.get("trimestre", ""),
                "tipo_documento": dados.get("categoria", ""),
                "file_name": file_name,
                "checksum": dados.get("checksum", ""),
                "download_date": dados.get("data_download", datetime.now().strftime("%Y-%m-%d")),
                "status_parse": "OK" if dados.get("raw_text") else "Erro"
            }
            registros.append(registro)

        except Exception as e:
            print(f"Erro ao ler {json_path}: {e}")

    if not registros:
        print(f"Nenhum relatório processado para a empresa '{empresa}'.")
        return

    # Define caminho de saída
    if caminho_saida is None:
        caminho_saida = f"csv's/RI_{empresa.replace(' ', '_')}_relatorios_resumo.csv"

    Path(caminho_saida).parent.mkdir(parents=True, exist_ok=True)  # Garante que a pasta exista

    campos = [
        "empresa", "ano", "trimestre", "tipo_documento", "file_name", "checksum",
        "download_date", "status_parse"
    ]

    try:
        with open(caminho_saida, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=campos, delimiter=';')
            writer.writeheader()
            writer.writerows(registros)

        print(f"CSV resumido salvo com sucesso em: {caminho_saida}")
    except Exception as e:
        print(f"Erro ao salvar CSV: {e}")