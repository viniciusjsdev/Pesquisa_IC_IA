#Scripts/services/context.py

from typing import List, Optional
import hashlib
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text as extract_text_pdfminer
from pathlib import Path
import multiprocessing
from functools import partial
from tqdm import tqdm
import fitz 
import tempfile
from ..strategies.interface import RaspagemStrategy
from model import RelatorioFinanceiro

# Função utilitária de preparação das pastas
def preparar_pastas_base(empresa: str, ano: str):
    base = Path(f"./pdfs/{empresa}/{ano}")
    (base / "originais").mkdir(parents=True, exist_ok=True)
    (base / "textos").mkdir(parents=True, exist_ok=True)
    (base / "jsons").mkdir(parents=True, exist_ok=True)
    return base

def _processar_pdf(relatorio: RelatorioFinanceiro, cache_dir: Optional[Path] = None) -> RelatorioFinanceiro:
    """
    Função separada para processar um único relatório PDF.
    Usada para processamento paralelo.
    """
    caminho_pdf = relatorio.caminho_arquivo
    
    # Verificar cache se habilitado
    if cache_dir:
        checksum_file = cache_dir / f"{Path(caminho_pdf).stem}.checksum"
        if checksum_file.exists():
            with open(checksum_file, "r") as f:
                cached_data = f.read().strip().split("|")
                if len(cached_data) == 2:
                    checksum, num_paginas = cached_data[0], int(cached_data[1])
                    
                    # Se temos checksum no cache, verificamos se o arquivo não mudou
                    try:
                        with open(caminho_pdf, "rb") as f:
                            current_checksum = hashlib.sha256(f.read()).hexdigest()
                        
                        if current_checksum == checksum:
                            # Carregar texto de arquivo salvo
                            texto_path = cache_dir / f"{Path(caminho_pdf).stem}.txt"
                            if texto_path.exists():
                                with open(texto_path, "r", encoding="utf-8") as f:
                                    texto = f.read()
                                relatorio.preencher_dados_processamento(texto, checksum, num_paginas)
                                return relatorio
                    except Exception:
                        pass  # Em caso de erro, continuar com processamento normal

    #Tenta PyPDF2 primeiro, depois PyMuPDF (se disponível), depois fallback para método alternativo
    
    checksum = ""
    texto_completo = ""
    num_paginas = 0
    
    try:
        # Método 1: PyPDF2
        try:
            leitor = PdfReader(caminho_pdf)
            num_paginas = len(leitor.pages)
        except Exception as e:
            if "PyCryptodome is required" in str(e):
                print(f"PDF criptografado detectado: {Path(caminho_pdf).name}. Tentando método alternativo...")

                try:
                    doc = fitz.open(caminho_pdf)
                    num_paginas = doc.page_count
                    doc.close()
                except ImportError:
                    
                    # Método 3: Fallback - Usar pdfminer para contar páginas também
                    from pdfminer.pdfparser import PDFParser
                    from pdfminer.pdfdocument import PDFDocument
                    with open(caminho_pdf, 'rb') as file:
                        parser = PDFParser(file)
                        document = PDFDocument(parser)
                        num_paginas = len(document.get_pages())
            else:
                raise e  
    except Exception as e:
        print(f"Erro ao contar páginas de {caminho_pdf}: {e}")
        num_paginas = 0

    # Extrair texto com pdfminer (mais robusto com PDFs protegidos)
    try:
        
        try:
            # Tentar pdfminer primeiro
            texto_completo = extract_text_pdfminer(caminho_pdf)
        except Exception as e_pdfminer:
            print(f"Erro com pdfminer em {caminho_pdf}: {e_pdfminer}. Tentando método alternativo...")
            
            # Tentar PyMuPDF se disponível
            try:
                doc = fitz.open(caminho_pdf)
                texto_completo = ""
                for pagina in doc:
                    texto_completo += pagina.get_text()
                doc.close()
            except ImportError:

                # Se PyMuPDF não estiver disponível
                raise e_pdfminer  # Propaga o erro original
    except Exception as e:
        print(f"Erro ao extrair texto de {caminho_pdf}: {e}")
        texto_completo = ""

    # Calcular o checksum a partir do texto extraído
    try:
        checksum = hashlib.sha256(texto_completo.encode("utf-8")).hexdigest()
    except Exception as e:
        print(f"Erro ao calcular checksum de {caminho_pdf}: {e}")
        checksum = ""
    
    # Salvar no cache se habilitado
    if cache_dir and checksum and num_paginas > 0:
        try:
            cache_dir.mkdir(exist_ok=True, parents=True)
            # Salvar checksum e número de páginas
            with open(cache_dir / f"{Path(caminho_pdf).stem}.checksum", "w") as f:
                f.write(f"{checksum}|{num_paginas}")
            # Salvar texto extraído
            with open(cache_dir / f"{Path(caminho_pdf).stem}.txt", "w", encoding="utf-8") as f:
                f.write(texto_completo)
        except Exception as e:
            print(f"Erro ao salvar cache para {caminho_pdf}: {e}")
    
    return relatorio.preencher_dados_processamento(texto_completo, checksum, num_paginas)


class RelatoriosFinanceirosContext:
    """
    Contexto que gerencia as estratégias de raspagem e o processamento dos relatórios.
    Implementa o padrão Strategy para permitir diferentes abordagens de raspagem.
    """
    
    def __init__(self, strategy: Optional[RaspagemStrategy] = None, 
                 max_workers: int = None, 
                 usar_cache: bool = True):
        self._strategy = strategy
        self._relatorios = []
        # Número de processos paralelos (default: núcleos disponíveis - 1)
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        # Habilitação do cache
        self.usar_cache = usar_cache
        self.cache_dir = Path("./cache/pdf_extractions") if usar_cache else None
        
    @property
    def strategy(self) -> Optional[RaspagemStrategy]:
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: RaspagemStrategy):
        self._strategy = strategy
    
    def executar_raspagem(self) -> List[RelatorioFinanceiro]:
        """
        Executa a estratégia de raspagem selecionada e retorna os relatórios coletados.
        """
        if not self._strategy:
            raise ValueError("Nenhuma estratégia de raspagem foi definida.")
        
        # Executar a estratégia de raspagem
        self._relatorios = self._strategy.baixar_relatorios()
        return self._relatorios
    
    def _salvar_arquivos_saida(self):
        """
        Salva os arquivos de saída (textos e jsons) para todos os relatórios processados.
        """
        for relatorio in tqdm(self._relatorios, desc="Salvando arquivos"):
            # Criar pastas de saída
            caminho_pdf = Path(relatorio.caminho_arquivo)
            ano = str(relatorio.ano)
            base = preparar_pastas_base(relatorio.empresa, ano)
            pasta_textos = base / "textos"
            pasta_jsons = base / "jsons"
            
            # Garantir que as pastas existam
            pasta_textos.mkdir(exist_ok=True, parents=True)
            pasta_jsons.mkdir(exist_ok=True, parents=True)
            
            # Salvar arquivos de saída
            relatorio.salvar_texto(pasta_textos)
            relatorio.salvar_json(pasta_jsons)    
    
    def _executar_processamento(self):
        """
        Executa o processamento dos relatórios PDF.
        """
        print(f"Processando {len(self._relatorios)} PDFs com {self.max_workers} workers...")

        if self.max_workers > 1:
            with multiprocessing.Pool(self.max_workers) as pool:
                processar_func = partial(_processar_pdf, cache_dir=self.cache_dir)
                self._relatorios = list(tqdm(
                    pool.imap(processar_func, self._relatorios),
                    total=len(self._relatorios),
                    desc="Extraindo texto dos PDFs"
                ))
        else:
            for i, relatorio in enumerate(tqdm(self._relatorios, desc="Extraindo texto dos PDFs")):
                self._relatorios[i] = _processar_pdf(relatorio, self.cache_dir)
    
    def processar_relatorios(self) -> List[RelatorioFinanceiro]:
        """
        Processa os relatórios coletados (extração de texto, geração de checksum, etc.)
        Utiliza processamento paralelo para melhorar o desempenho.
        """
        if not self._relatorios:
            print("Nenhum relatório para processar.")
            return []
            
        if self.usar_cache:
            # Cria diretório temporário com contexto
            with tempfile.TemporaryDirectory() as temp_dir:
                self.cache_dir = Path(temp_dir)
                self._executar_processamento()
                self._salvar_arquivos_saida()
        else:
            self.cache_dir = None
            self._executar_processamento()
            self._salvar_arquivos_saida()

        return self._relatorios

        # Processar PDFs em paralelo
        print(f"Processando {len(self._relatorios)} PDFs com {self.max_workers} workers...")
        
        if self.max_workers > 1:
            # Usar processamento paralelo
            with multiprocessing.Pool(self.max_workers) as pool:
                processar_func = partial(_processar_pdf, cache_dir=self.cache_dir)
                # Usar tqdm para mostrar progresso
                self._relatorios = list(tqdm(
                    pool.imap(processar_func, self._relatorios),
                    total=len(self._relatorios),
                    desc="Extraindo texto dos PDFs"
                ))
        else:
            # Processamento sequencial (para debug ou sistemas com poucos recursos)
            for i, relatorio in enumerate(tqdm(self._relatorios, desc="Extraindo texto dos PDFs")):
                self._relatorios[i] = _processar_pdf(relatorio, self.cache_dir)
                
        # Salvar os arquivos de saída (texto e json)
        print("Salvando arquivos de saída...")
        self._salvar_arquivos_saida()
        
        return self._relatorios