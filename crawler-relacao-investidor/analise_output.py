import streamlit as st
import pandas as pd
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple


class RelatoriosAnalyzer:
    """Classe principal para análise de relatórios financeiros"""
    
    def __init__(self, caminho_base: str):
        self.caminho_base = caminho_base
        self.problemas_empresa = []
    
    @staticmethod
    def extrair_empresa(caminho: str) -> str:
        """Extrai o nome da empresa do caminho do arquivo"""
        partes = Path(caminho).parts
        try:
            textos_index = partes.index("textos")
            return partes[textos_index - 2]  # Empresa está 2 acima da pasta 'textos'
        except (ValueError, IndexError):
            return 'Desconhecida'
    
    def analisar_arquivos_json(self) -> pd.DataFrame:
        """Analisa arquivos JSON e identifica problemas"""
        dados_lista_json = []
        
        if not os.path.exists(self.caminho_base):
            return pd.DataFrame()
        
        for raiz, _, arquivos in os.walk(self.caminho_base):
            if 'jsons' not in raiz.lower():
                continue
                
            for nome_arquivo in arquivos:
                if not nome_arquivo.lower().endswith(".json"):
                    continue
                    
                caminho_completo = os.path.join(raiz, nome_arquivo)
                empresa = self.extrair_empresa(raiz)
                
                try:
                    dados = self._carregar_json(caminho_completo)
                    total_chars, campos_vazios_str = self._analisar_conteudo_json(dados)
                    
                    dados_lista_json.append({
                        "Empresa": empresa,
                        "Arquivo": nome_arquivo,
                        "Total_caracteres_JSON": total_chars,
                        "Campos_vazios": campos_vazios_str
                    })
                    
                    # Registrar problemas
                    if pd.isna(total_chars) or pd.notna(campos_vazios_str):
                        self._adicionar_problema(empresa, "JSON", nome_arquivo, 
                                               campos_vazios_str or "Sem caracteres")
                        
                except Exception as e:
                    dados_lista_json.append({
                        "Empresa": empresa,
                        "Arquivo": nome_arquivo,
                        "Total_caracteres_JSON": np.nan,
                        "Campos_vazios": f"Erro: {str(e)}"
                    })
                    self._adicionar_problema(empresa, "JSON", nome_arquivo, f"Erro: {str(e)}")
        
        return pd.DataFrame(dados_lista_json)
    
    def _carregar_json(self, caminho: str) -> Dict[str, Any]:
        """Carrega arquivo JSON"""
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _analisar_conteudo_json(self, dados: Dict[str, Any]) -> Tuple[int, str]:
        """Analisa o conteúdo do JSON"""
        raw_text = dados.get("raw_text")
        total_chars = len(str(raw_text).strip()) if raw_text else np.nan
        
        campos_vazios = [k for k, v in dados.items() 
                        if v in [None, "", [], {}] and k != "raw_text"]
        campos_vazios_str = ', '.join(campos_vazios) if campos_vazios else np.nan
        
        return total_chars, campos_vazios_str
    
    def analisar_arquivos_txt(self) -> pd.DataFrame:
        """Analisa arquivos TXT"""
        dados_txt = []
        
        for raiz, _, arquivos in os.walk(self.caminho_base):
            if 'textos' not in raiz.lower():
                continue
                
            for nome_arquivo in arquivos:
                if not nome_arquivo.endswith(".txt"):
                    continue
                    
                caminho_completo = os.path.join(raiz, nome_arquivo)
                empresa = self.extrair_empresa(raiz)
                
                try:
                    with open(caminho_completo, "r", encoding="utf-8") as f:
                        texto = f.read()
                    
                    total_chars = len(texto)
                    dados_txt.append([caminho_completo, nome_arquivo, total_chars])
                    
                    # Registrar problemas se arquivo muito pequeno
                    if total_chars < 3000:
                        self._adicionar_problema(empresa, "TXT", nome_arquivo, 
                                               f"Texto com {total_chars} caracteres")
                        
                except Exception as e:
                    dados_txt.append([caminho_completo, nome_arquivo, f"Erro: {e}"])
                    self._adicionar_problema(empresa, "TXT", nome_arquivo, f"Erro: {e}")
        
        df_txt = pd.DataFrame(dados_txt, columns=["Caminho", "Arquivo", "Total_caracteres_TXT"])
        df_txt["Empresa"] = df_txt["Caminho"].apply(self.extrair_empresa)
        
        return df_txt
    
    def _adicionar_problema(self, empresa: str, tipo: str, arquivo: str, problema: str):
        """Adiciona problema à lista de problemas por empresa"""
        self.problemas_empresa.append({
            "Empresa": empresa,
            "Tipo": tipo,
            "Arquivo": arquivo,
            "Problema": problema
        })
    
    def comparar_json_txt(self, df_json: pd.DataFrame, df_txt: pd.DataFrame) -> pd.DataFrame:
        """Compara caracteres entre arquivos JSON e TXT"""
        if df_json.empty or df_txt.empty:
            return pd.DataFrame()
        
        comparacao = pd.merge(
            df_json[["Arquivo", "Empresa", "Total_caracteres_JSON"]],
            df_txt[["Arquivo", "Total_caracteres_TXT"]],
            on="Arquivo", how="inner"
        )
        
        comparacao["Diferenca"] = abs(
            comparacao["Total_caracteres_JSON"] - comparacao["Total_caracteres_TXT"]
        )
        
        return comparacao[comparacao["Diferenca"] > 100]
    
    def analisar_csv(self, df_csv: pd.DataFrame) -> Dict[str, Any]:
        """Analisa problemas no CSV de saída"""
        resumo = {
            "anos_incompletos": 0,
            "colunas_zero": set(),
            "colunas_vazias": set()
        }
        
        # Análise de anos incompletos
        if 'arquivo_pdf' in df_csv.columns:
            self._analisar_anos_incompletos(df_csv, resumo)
        
        # Análise de colunas com zeros
        self._analisar_colunas_zero(df_csv, resumo)
        
        # Análise de campos vazios
        self._analisar_campos_vazios(df_csv, resumo)
        
        return resumo
    
    def _analisar_anos_incompletos(self, df_csv: pd.DataFrame, resumo: Dict[str, Any]):
        """Analisa anos com quantidade incorreta de relatórios"""
        anos = df_csv['arquivo_pdf'].dropna().apply(
            lambda x: ''.join(filter(str.isdigit, x))[:4]
        )
        contagem = anos.value_counts()
        
        for ano, qtd in contagem.items():
            if qtd != 12:
                resumo["anos_incompletos"] += 1
                self._adicionar_problema("-", "CSV", f"{ano}", 
                                       f"{qtd} PDFs encontrados (esperado: 12)")
    
    def _analisar_colunas_zero(self, df_csv: pd.DataFrame, resumo: Dict[str, Any]):
        """Analisa colunas com valores zero"""
        col_numericas = df_csv.select_dtypes(include=['int', 'float']).columns
        
        for col in col_numericas:
            zeros = df_csv[df_csv[col] == 0]
            if not zeros.empty:
                resumo["colunas_zero"].add(col)
                for _, row in zeros.iterrows():
                    empresa = self._extrair_empresa_csv(row.get("arquivo_pdf", ""))
                    self._adicionar_problema(empresa, "CSV", 
                                           row.get("arquivo_pdf", ""), 
                                           f"Valor 0 em '{col}'")
    
    def _analisar_campos_vazios(self, df_csv: pd.DataFrame, resumo: Dict[str, Any]):
        """Analisa campos vazios no CSV"""
        col_str = df_csv.select_dtypes(include=['object']).columns
        
        for col in col_str:
            vazios = df_csv[df_csv[col].isna() | (df_csv[col] == '')]
            if not vazios.empty:
                resumo["colunas_vazias"].add(col)
                for _, row in vazios.iterrows():
                    empresa = self._extrair_empresa_csv(row.get("arquivo_pdf", ""))
                    self._adicionar_problema(empresa, "CSV", 
                                           row.get("arquivo_pdf", ""), 
                                           f"Campo '{col}' vazio")
    
    @staticmethod
    def _extrair_empresa_csv(nome_pdf: str) -> str:
        """Extrai empresa do nome do PDF"""
        try:
            return nome_pdf.split("_")[0]
        except:
            return "Desconhecida"
    
    def gerar_relatorios_esperados(self, config_path: str) -> pd.DataFrame:
        """Gera lista de relatórios esperados baseado no config.py"""
        if not os.path.exists(config_path):
            return pd.DataFrame()
        
        try:
            # Ler o arquivo config.py como texto
            with open(config_path, "r", encoding="utf-8") as f:
                config_content = f.read()
            
            # Extrair empresas usando regex
            import re
            empresas_registradas = self._extrair_empresas_do_config(config_content)
            
            if not empresas_registradas:
                return pd.DataFrame()
            
        except Exception as e:
            st.error(f"Erro ao carregar config.py: {str(e)}")
            return pd.DataFrame()
        
        relatorios_esperados = []
        
        # Anos disponíveis para análise (pode ser configurado)
        anos_disponiveis = [2020, 2021, 2022, 2023, 2024]
        
        for empresa_nome, tipos_relatorios in empresas_registradas.items():
            for tipo_relatorio in tipos_relatorios:
                # Determinar trimestres baseado no tipo
                if tipo_relatorio in ["DFP", "SIGLA_DFP"]:
                    trimestres = ["4T"]  # DFP só no 4T
                elif tipo_relatorio in ["ITR", "SIGLA_ITR", "SIGLA_ITR_DFP"]:
                    trimestres = ["1T", "2T", "3T"]  # ITR nos 3 primeiros trimestres
                else:
                    # Para outros tipos (RR, AP), considerar todos os trimestres
                    trimestres = ["1T", "2T", "3T", "4T"]
                
                for ano in anos_disponiveis:
                    for trimestre in trimestres:
                        base_nome = f"{empresa_nome}_{tipo_relatorio}_{trimestre}{ano}"
                        relatorios_esperados.append({
                            "Empresa": empresa_nome,
                            "Tipo": tipo_relatorio,
                            "Ano": ano,
                            "Trimestre": trimestre,
                            "Arquivo_JSON": f"{base_nome}.json",
                            "Arquivo_TXT": f"{base_nome}.txt"
                        })
        
        return pd.DataFrame(relatorios_esperados)
    
    def _extrair_empresas_do_config(self, config_content: str) -> Dict[str, List[str]]:
        """Extrai empresas e tipos de relatórios do conteúdo do config.py"""
        import re
        
        empresas = {}
        
        # Padrão para encontrar registros de empresas
        pattern_empresa = r'(\w+)\s*=\s*registrar_empresa\(EmpresaRI\(\s*nome="([^"]+)"'
        matches_empresas = re.findall(pattern_empresa, config_content)
        
        for var_name, empresa_nome in matches_empresas:
            # Encontrar a seção completa desta empresa
            pattern_secao = rf'{var_name}\s*=\s*registrar_empresa\(EmpresaRI\((.*?)\)\)'
            match_secao = re.search(pattern_secao, config_content, re.DOTALL)
            
            if match_secao:
                secao_empresa = match_secao.group(1)
                
                # Extrair tipos de relatórios
                pattern_tipos = r'TipoRelatorio\([^)]*sigla=([^)]+)\)'
                tipos_matches = re.findall(pattern_tipos, secao_empresa)
                
                tipos_relatorios = []
                for tipo_match in tipos_matches:
                    # Limpar o tipo (remover TipoRelatorio. e aspas)
                    tipo_limpo = tipo_match.replace('TipoRelatorio.', '').replace('"', '').strip()
                    tipos_relatorios.append(tipo_limpo)
                
                if tipos_relatorios:
                    empresas[empresa_nome] = tipos_relatorios
        
        return empresas


class StreamlitUI:
    """Classe para interface do Streamlit"""
    
    def __init__(self):
        self.setup_page()
    
    def setup_page(self):
        """Configura a página do Streamlit"""
        st.set_page_config(page_title="Análise dos Relatórios Baixados", layout="wide")
        st.title("📊 Análise dos Relatórios Financeiros de RI")
    
    def obter_caminho_base(self) -> str:
        """Obtém o caminho base dos arquivos"""
        return st.text_input(
            "📁 Caminho base dos arquivos (json/textos):", 
            r"C:\Users\Usuario\Desktop\Repositorios_Bitbucket\crawer-ri-gpa\pdfs"
        )
    
    def exibir_analise_json(self, df_json: pd.DataFrame):
        """Exibe análise dos arquivos JSON"""
        with st.expander("📄 Análise dos arquivos JSON (Problemas)", expanded=True):
            if df_json.empty:
                st.info("Nenhum arquivo JSON encontrado.")
                return
            
            problemas_json = df_json[
                df_json["Total_caracteres_JSON"].isna() | 
                df_json["Campos_vazios"].notna()
            ]
            
            if not problemas_json.empty:
                st.dataframe(problemas_json)
            else:
                st.success("✅ Todos os arquivos JSON estão completos.")
    
    def exibir_analise_txt(self, df_txt: pd.DataFrame):
        """Exibe análise dos arquivos TXT"""
        st.subheader("📃 Análise da saída dos arquivos TXT")
        
        if df_txt.empty:
            st.info("Nenhum arquivo TXT encontrado.")
            return
        
        st.dataframe(df_txt.drop(columns=["Caminho"]))
        
        limite = 3000
        vazios = df_txt[
            df_txt["Total_caracteres_TXT"].apply(
                lambda x: isinstance(x, int) and x < limite
            )
        ]
        
        with st.expander("📝 Análise dos arquivos TXT (Problemas)"):
            st.markdown(f"🔎 Exibindo arquivos com **menos de {limite:,} caracteres**.")
            
            if vazios.empty:
                st.success("✅ Nenhum arquivo TXT com menos de 3.000 caracteres.")
            else:
                st.warning(f"⚠️ {len(vazios)} arquivos com menos de {limite:,} caracteres:")
                st.dataframe(vazios[["Empresa", "Arquivo", "Total_caracteres_TXT"]])
    
    def exibir_comparacao(self, discrepantes: pd.DataFrame):
        """Exibe comparação entre JSON e TXT"""
        with st.expander("📐 Comparação entre JSON e TXT (Caracteres)", expanded=True):
            if discrepantes.empty:
                st.success("✅ Diferenças entre JSON e TXT estão dentro do esperado.")
            else:
                st.warning("📏 Arquivos com diferença de caracteres maior que 100:")
                st.dataframe(discrepantes)
    
    def exibir_problemas_empresa(self, problemas: List[Dict[str, str]]):
        """Exibe problemas agrupados por empresa"""
        st.subheader("🛠️ Problemas detectados por empresa")
        
        if not problemas:
            st.success("✅ Nenhum problema detectado por empresa.")
            return
        
        df_problemas = pd.DataFrame(problemas)
        st.dataframe(df_problemas)
        st.download_button(
            "📥 Baixar erros como CSV", 
            df_problemas.to_csv(index=False), 
            file_name="erros_por_empresa.csv", 
            mime="text/csv"
        )
    
    def exibir_relatorios_esperados(self, analyzer: RelatoriosAnalyzer, config_path: str):
        """Exibe relatórios esperados vs encontrados"""
        st.header("📋 Relatórios Esperados vs Encontrados")
        
        if not os.path.exists(config_path):
            st.error(f"❌ Arquivo config.py não encontrado: {config_path}")
            return
        
        df_esperados = analyzer.gerar_relatorios_esperados(config_path)
        
        if df_esperados.empty:
            st.warning("⚠️ Nenhuma empresa encontrada no config.py ou erro ao processar.")
            return
        
        # Mostrar resumo das empresas encontradas
        empresas_unicas = df_esperados['Empresa'].unique()
        tipos_unicos = df_esperados['Tipo'].unique()
        
        with st.expander("📊 Resumo das Empresas Configuradas", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Empresas encontradas:**")
                for empresa in sorted(empresas_unicas):
                    st.write(f"• {empresa}")
            
            with col2:
                st.markdown("**Tipos de relatórios:**")
                for tipo in sorted(tipos_unicos):
                    st.write(f"• {tipo}")
        
        # Obter diretórios de JSON e TXT baseados no caminho base
        diretorio_json = None
        diretorio_txt = None
        
        # Procurar diretórios jsons e textos
        for raiz, dirs, _ in os.walk(analyzer.caminho_base):
            if 'jsons' in [d.lower() for d in dirs] and diretorio_json is None:
                diretorio_json = os.path.join(raiz, next(d for d in dirs if d.lower() == 'jsons'))
            if 'textos' in [d.lower() for d in dirs] and diretorio_txt is None:
                diretorio_txt = os.path.join(raiz, next(d for d in dirs if d.lower() == 'textos'))
        
        if not diretorio_json or not diretorio_txt:
            st.warning("⚠️ Diretórios 'jsons' ou 'textos' não encontrados no caminho base.")
            st.info("📋 Lista de relatórios esperados:")
            st.dataframe(df_esperados[["Empresa", "Tipo", "Ano", "Trimestre"]])
            return
        
        # Verificar se os arquivos realmente existem
        def checar_arquivo_json(arquivo):
            for raiz, _, arquivos in os.walk(diretorio_json):
                if arquivo in arquivos:
                    return True
            return False
        
        def checar_arquivo_txt(arquivo):
            for raiz, _, arquivos in os.walk(diretorio_txt):
                if arquivo in arquivos:
                    return True
            return False
        
        # Aplicar verificação (pode ser lento para muitos arquivos)
        with st.spinner("🔍 Verificando existência dos arquivos..."):
            df_esperados["JSON_existente"] = df_esperados["Arquivo_JSON"].apply(checar_arquivo_json)
            df_esperados["TXT_existente"] = df_esperados["Arquivo_TXT"].apply(checar_arquivo_txt)
        
        # Calcular estatísticas
        total_esperados = len(df_esperados)
        json_encontrados = df_esperados["JSON_existente"].sum()
        txt_encontrados = df_esperados["TXT_existente"].sum()
        ambos_encontrados = (df_esperados["JSON_existente"] & df_esperados["TXT_existente"]).sum()
        
        # Mostrar estatísticas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Total Esperado", total_esperados)
        with col2:
            st.metric("📊 JSON Encontrados", f"{json_encontrados}/{total_esperados}")
        with col3:
            st.metric("📝 TXT Encontrados", f"{txt_encontrados}/{total_esperados}")
        with col4:
            st.metric("✅ Completos", f"{ambos_encontrados}/{total_esperados}")
        
        # Mostrar relatórios faltantes
        df_faltantes = df_esperados[~(df_esperados["JSON_existente"] & df_esperados["TXT_existente"])]
        
        st.subheader("📌 Análise de Relatórios Faltantes")
        
        if df_faltantes.empty:
            st.success("🎉 Todos os relatórios esperados foram encontrados!")
        else:
            st.warning(f"⚠️ {len(df_faltantes)} relatórios faltantes de {total_esperados} esperados")
            
            # Agrupar por empresa
            faltantes_por_empresa = df_faltantes.groupby('Empresa').size().sort_values(ascending=False)
            
            if len(faltantes_por_empresa) > 0:
                st.markdown("**Relatórios faltantes por empresa:**")
                for empresa, qtd in faltantes_por_empresa.items():
                    st.write(f"• {empresa}: {qtd} relatórios")
            
            # Mostrar tabela detalhada
            with st.expander("📋 Lista Detalhada de Relatórios Faltantes"):
                st.dataframe(
                    df_faltantes[["Empresa", "Tipo", "Ano", "Trimestre", "JSON_existente", "TXT_existente"]],
                    use_container_width=True
                )
            
            # Download
            st.download_button(
                "📥 Baixar lista completa de faltantes", 
                df_faltantes.to_csv(index=False), 
                file_name="relatorios_faltantes.csv", 
                mime="text/csv"
            )
    
    def exibir_analise_csv(self, analyzer: RelatoriosAnalyzer):
        """Exibe análise do CSV"""
        with st.expander("📈 Análise do CSV de saída (Problemas)", expanded=True):
            arquivo_csv = st.file_uploader("📥 Carregue um arquivo CSV de saída:", type=["csv"])
            
            if arquivo_csv:
                df_csv = pd.read_csv(arquivo_csv)
                st.dataframe(df_csv)
                
                resumo = analyzer.analisar_csv(df_csv)
                
                if any([resumo["anos_incompletos"], resumo["colunas_zero"], resumo["colunas_vazias"]]):
                    mensagem_geral = f"""
                    ⚠️ **Resumo dos problemas detectados no CSV**:
                    - {resumo['anos_incompletos']} ano(s) com quantidade incorreta de relatórios (≠ 12).
                    - {len(resumo['colunas_zero'])} coluna(s) com valores 0: {', '.join(resumo['colunas_zero']) or 'Nenhuma'}.
                    - {len(resumo['colunas_vazias'])} coluna(s) com campos vazios: {', '.join(resumo['colunas_vazias']) or 'Nenhuma'}.
                    """
                    st.markdown(mensagem_geral)
                else:
                    st.success("✅ Nenhum problema detectado no CSV.")


def main():
    """Função principal da aplicação"""
    ui = StreamlitUI()
    caminho_base = ui.obter_caminho_base()
    
    if not caminho_base:
        st.info("Por favor, insira o caminho base dos arquivos.")
        return
    
    analyzer = RelatoriosAnalyzer(caminho_base)
    
    # Relatórios esperados vs encontrados
    config_path = r"C:\Users\Usuario\Desktop\Repositorios_Bitbucket\crawer-ri-gpa\Coleta_e_Processamento_RI_Empresas\empresas_ri\config.py"
    ui.exibir_relatorios_esperados(analyzer, config_path)

    # Análise dos arquivos JSON
    df_json = analyzer.analisar_arquivos_json()
    ui.exibir_analise_json(df_json)
    
    # Análise dos arquivos TXT
    df_txt = analyzer.analisar_arquivos_txt()
    ui.exibir_analise_txt(df_txt)
    
    # Comparação JSON vs TXT
    discrepantes = analyzer.comparar_json_txt(df_json, df_txt)
    ui.exibir_comparacao(discrepantes)
    
    # Problemas por empresa
    ui.exibir_problemas_empresa(analyzer.problemas_empresa)
    
    # Análise do CSV
    ui.exibir_analise_csv(analyzer)


if __name__ == "__main__":
    main()