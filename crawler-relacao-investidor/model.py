from datetime import datetime, timezone
from pathlib import Path
import json
import os
from dataclasses import dataclass
from typing import Dict, List

class RelatorioFinanceiro:
    """
    Representa um relatório financeiro de uma empresa, incluindo dados de processamento do PDF.
    """
    
    def __init__(self, empresa, categoria, ano, trimestre, download_url, caminho_arquivo):
        self.empresa = empresa
        self.categoria = categoria
        self.ano = int(ano)
        self.trimestre = trimestre
        self.download_url = download_url
        self.caminho_arquivo = caminho_arquivo
        self.data_extracao = datetime.now(timezone.utc).isoformat()
        
        # Campos extras para processamento do PDF
        self.texto = None
        self.checksum = None
        self.num_paginas = None
        
        # Cache para desempenho
        self._caminho_pdf = Path(self.caminho_arquivo)
        self._nome_base = self._caminho_pdf.stem
    
    def preencher_dados_processamento(self, texto, checksum, num_paginas):
        """Preenche os dados de processamento do relatório"""
        self.texto = texto
        self.checksum = checksum
        self.num_paginas = num_paginas
        return self
    
    def to_dict(self):
        """Converte o relatório para dicionário"""
        return {
            "empresa": self.empresa,
            "categoria": self.categoria,
            "ano": self.ano,
            "trimestre": self.trimestre,
            "download_url": self.download_url,
            "data_extracao": self.data_extracao,
            "num_pages": self.num_paginas,
            "raw_text": self.texto, 
            "checksum": self.checksum
        }
    
    def salvar_json(self, pasta_destino, salvar_texto_no_json=False):
        """
        Salva o relatório como JSON.
        
        Args:
            pasta_destino: Diretório onde salvar o arquivo
            salvar_texto_no_json: Se False, omite o texto do PDF para economizar espaço
        """
        # Garantir que a pasta existe
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Determinar qual versão do dicionário usar
        dados = self.to_dict() if salvar_texto_no_json else self.to_dict()
        
        # Caminho do arquivo de saída
        caminho_saida = pasta_destino / f"{self._nome_base}.json"
        
        # Salvar o JSON
        with open(caminho_saida, "w", encoding="utf-8") as f_json:
            json.dump(dados, f_json, indent=2, ensure_ascii=False)
            
        return caminho_saida
    
    def salvar_texto(self, pasta_destino):
        """Salva o texto extraído do PDF em um arquivo .txt"""
        # Garantir que a pasta existe
        os.makedirs(pasta_destino, exist_ok=True)
        
        # Caminho do arquivo de saída
        caminho_saida = pasta_destino / f"{self._nome_base}.txt"
        
        # Salvar o texto (se houver)
        with open(caminho_saida, "w", encoding="utf-8") as f_txt:
            f_txt.write(self.texto or "")
            
        return caminho_saida
    
    def __repr__(self):
        return f"<Relatorio {self.empresa} {self.ano}-{self.trimestre} [{self.categoria}]>"

@dataclass
class TipoRelatorio:
    """
    Representa um tipo de relatório financeiro publicado no portal de RI de uma empresa.

    Atributos:
        nome_site (str): Nome do relatório conforme aparece no site.
        sigla (str): Sigla interna utilizada para categorização e padronização.

    Constantes de siglas padronizadas:
        SIGLA_AP: Apresentações
        SIGLA_RR: Release de Resultados
        SIGLA_ITR: Informações Trimestrais
        SIGLA_DFP: Demonstrações Financeiras Padronizadas
        SIGLA_ITR_DFP: Categoria mista, depende do trimestre
    """
    nome_site: str
    sigla: str

    # Siglas padronizadas
    SIGLA_AP = "AP"
    SIGLA_RR = "RR"
    SIGLA_ITR = "ITR"
    SIGLA_DFP = "DFP"
    SIGLA_ITR_DFP = "ITR/DFP"

    @property
    def categoria_padrao(self) -> str:
        """
        Retorna a categoria padronizada com base na sigla do relatório.
        """
        match self.sigla:
            case self.SIGLA_AP:
                return "Apresentações"
            case self.SIGLA_RR:
                return "Release de Resultados"
            case self.SIGLA_ITR | self.SIGLA_DFP | self.SIGLA_ITR_DFP:
                return "Demonstrações Financeiras"
            case _:
                return "Outros"

@dataclass
class EmpresaRI:
    """
    Representa uma empresa com seus dados de RI e os tipos de relatórios disponíveis.

    Atributos:
        nome (str): Nome da empresa.
        url (str): URL da central de resultados no site de RI.
        tipos_relatorios (List[TipoRelatorio]): Lista de tipos de relatórios disponibilizados.
    """
    nome: str
    url: str
    tipos_relatorios: List[TipoRelatorio]

    def obter_categoria_e_sigla(self, nome_site: str, trimestre: str) -> Dict[str, str]:
        """
        Retorna a categoria e a sigla padronizadas para um relatório com base no nome do site e trimestre.

        Regras:
            - Se for '4T' e tipo for ITR/DFP, retorna como DFP.
            - Se for 1T, 2T ou 3T e tipo for ITR/DFP, retorna como ITR.
            - Caso contrário, utiliza a correspondência direta com base no nome_site.
        
        Parâmetros:
            nome_site (str): Nome do relatório conforme aparece no site da empresa.
            trimestre (str): Trimestre do relatório (ex: '1T', '2T', '3T', '4T').

        Retorna:
            dict: Contendo 'categoria' e 'sigla' padronizadas.
        """
        trimestre = trimestre.strip().upper()
        for tipo in self.tipos_relatorios:
            if tipo.nome_site == nome_site:
                if tipo.sigla in (
                    TipoRelatorio.SIGLA_ITR,
                    TipoRelatorio.SIGLA_DFP,
                    TipoRelatorio.SIGLA_ITR_DFP
                ) and "T" in trimestre:
                    if trimestre == "4T":
                        return {"categoria": "Demonstrações Financeiras", "sigla": TipoRelatorio.SIGLA_DFP}
                    else:
                        return {"categoria": "Demonstrações Financeiras", "sigla": TipoRelatorio.SIGLA_ITR}
                return {"categoria": tipo.categoria_padrao, "sigla": tipo.sigla}
        
        return {"categoria": "Desconhecido", "sigla": "UNK"}