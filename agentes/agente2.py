import json
import csv
import pandas as pd
from openai import AzureOpenAI
import time
import logging
from typing import List, Dict, Any
import re
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_INFERENCE_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_API_VERSION,
)

# === Configuração de logging ===
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinancialDataNormalizer:
    def __init__(self):
        self.setup_azure_client()
        
        # === Definir schema completo de colunas ===
        self.csv_columns = [

            # Identificação
            "Ano", "Trimestre", "Arquivo",

            # Financeiro
            "Receita", "EBITDA", "Lucro_liquido", "Lucro_bruto", "Margem_EBITDA", "Margem_liquida",
            "Despesas", "Divida_liquida", "Investimento_capital", "Receita_perdida", "ROE", "ROA",
            "Fluxo_Caixa_Operacional", "Fluxo_Caixa_Livre", "Fluxo_Caixa_Investimento", "Fluxo_Caixa_Financiamento",
            "Divida_Bruta", "Divida_Curto_Prazo", "Divida_Longo_Prazo", "Dividendos"

            # Produção / Operacional
            "Producao", "Capacidade", "Falha_maquina", "Horas_paradas", "Unidades_perdidas",
            "Energia_consumida_kwh", "Tipo_evento", "Descricao_falha", "Responsavel", "Linha_producao",

            # Híbrido financeiro + produção
            "Custo_manutencao", "Receita_impactada", "Perda_eficiencia", "Capacidade_utilizada"
        ]

    def setup_azure_client(self):
        """Configurar cliente Azure OpenAI com validação"""
        try:
            self.llm = AzureOpenAI(
                api_key=AZURE_OPENAI_API_KEY,
                azure_endpoint=AZURE_INFERENCE_ENDPOINT,
                api_version=AZURE_API_VERSION
            )
            logger.info("Cliente Azure OpenAI configurado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar Azure OpenAI: {e}")
            raise

    def load_agent1_data(self, filepath: str) -> List[Dict[Any, Any]]:
        """Carregar dados do Agente 1 com validação"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Carregados {len(data)} registros do Agente 1")
            return data
        except FileNotFoundError:
            logger.error(f"Arquivo {filepath} não encontrado")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
            raise

    def create_enhanced_prompt(self, batch_data: List[Dict]) -> str:
        """Criar prompt melhorado para normalização"""
        batch_str = json.dumps(batch_data, ensure_ascii=False, indent=2)
        
        return f"""
        Você é um especialista em normalização de dados financeiros e operacionais da Gerdau.
        
        TAREFA: Transformar dados extraídos de relatórios em uma tabela normalizada para análise.
        
        SCHEMA DE COLUNAS OBRIGATÓRIAS:
        {', '.join(self.csv_columns)}
        
        DADOS DE ENTRADA:
        {batch_str}
        
        REGRAS DE NORMALIZAÇÃO:
        
        1. IDENTIFICAÇÃO:
        - Extrair Ano (formato: YYYY)
        - Extrair Trimestre (formato: 1T, 2T, 3T, 4T)
        - Usar nome do arquivo fonte quando disponível
        
        2. VALORES FINANCEIROS:
        - Converter para formato consistente: "X.XXX milhões R$"
        - Receita: receita líquida ou receita bruta
        - EBITDA: lucro antes de juros, impostos, depreciação e amortização
        - Lucro_liquido: resultado líquido do período
        - Margem_EBITDA: EBITDA/Receita * 100 (formato: "X.X%")
        - Margem_liquida: Lucro_liquido/Receita * 100 (formato: "X.X%")
        - ROE e ROA: retornar percentual ou "Não informado"
        - Fluxos de Caixa e Dividendos: retornar valor numérico ou "Não informado"
        - Dívidas (Liquida, Bruta, Curto Prazo, Longo Prazo): normalizar para milhões ou bilhões
        
        3. PRODUÇÃO:
        - Producao: volume em "X.XXX mil toneladas"
        - Capacidade: utilização em "XX%" ou capacidade instalada
        - Campos textuais: usar "Não informado" se ausente
        
        4. VALIDAÇÕES:
        - EBITDA deve ser ≥ Lucro_liquido (logicamente)
        - Margens devem estar entre 0-100%
        - Valores negativos são aceitáveis (prejuízos)
        
        5. DADOS AUSENTES:
        - Use "Não informado" para campos sem dados
        - NÃO invente valores
        
        FORMATO DE SAÍDA:
        Retorne APENAS um JSON array válido, sem texto adicional.
        Exemplo de objeto JSON:
        [
            {{
                "Ano": "2025",
                "Trimestre": "1T",
                "Arquivo": "nome_arquivo.txt",
                "Receita": "7.494 milhões R$",
                "EBITDA": "817 milhões R$",
                "Lucro_liquido": "758 milhões R$",
                "Lucro_bruto": "Não informado",
                "Margem_EBITDA": "10.9%",
                "Margem_liquida": "10.1%",
                "Despesas": "Não informado",
                "Divida_liquida": "Não informado",
                "Investimento_capital": "Não informado",
                "Receita_perdida": "Não informado",
                "Producao": "1.431 mil toneladas",
                "Capacidade": "73%",
                "Falha_maquina": "Não informado",
                "Horas_paradas": "Não informado",
                "Unidades_perdidas": "Não informado",
                "Energia_consumida_kwh": "Não informado",
                "Tipo_evento": "Não informado",
                "Descricao_falha": "Não informado",
                "Responsavel": "Não informado",
                "Linha_producao": "Não informado",
                "Custo_manutencao": "Não informado",
                "Receita_impactada": "Não informado",
                "Perda_eficiencia": "Não informado",
                "Capacidade_utilizada": "Não informado",
                "ROE": "Não informado",
                "ROA": "Não informado",
                "Fluxo_Caixa_Operacional": "Não informado",
                "Fluxo_Caixa_Livre": "Não informado",
                "Fluxo_Caixa_Investimento": "Não informado",
                "Fluxo_Caixa_Financiamento": "Não informado",
                "Divida_Bruta": "Não informado",
                "Divida_Curto_Prazo": "Não informado",
                "Divida_Longo_Prazo": "Não informado",
                "Dividendos": "Não informado"
            }}
        ]
        """

    def normalize_json_llm(self, ag1_data: List[Dict], batch_size: int = 3) -> List[Dict]:
        """Normalizar dados usando LLM com processamento em lotes"""
        results = []
        total_batches = (len(ag1_data) - 1) // batch_size + 1
        
        logger.info(f"Iniciando normalização de {len(ag1_data)} registros em {total_batches} lotes")
        
        for i in range(0, len(ag1_data), batch_size):
            batch = ag1_data[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            try:
                logger.info(f"Processando lote {batch_num}/{total_batches}")
                
                prompt = self.create_enhanced_prompt(batch)
                
                response = self.llm.chat.completions.create(
                    model=AZURE_OPENAI_DEPLOYMENT_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,  # Baixa temperatura para consistência
                    max_tokens=4000
                )
                
                # Extrair conteúdo da resposta
                content = response.choices[0].message.content
                
                # Limpar e parsear JSON
                content = self.clean_json_response(content)
                batch_results = json.loads(content)
                
                # Validar estrutura
                validated_batch = self.validate_batch_data(batch_results)
                results.extend(validated_batch)
                
                logger.info(f"Lote {batch_num} processado com sucesso: {len(validated_batch)} registros")
                
                # Pausa para evitar rate limiting
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Erro no lote {batch_num}: {e}")
                # Continuar com próximo lote em caso de erro
                continue
                
        logger.info(f"Normalização concluída: {len(results)} registros processados")
        return results

    def clean_json_response(self, content: str) -> str:
        """Limpar resposta do LLM para extrair JSON válido"""
        # Remover markdown e texto extra
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*$', '', content)
        
        # Encontrar início e fim do array JSON
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx != -1 and end_idx != -1:
            return content[start_idx:end_idx]
        
        return content

    def validate_batch_data(self, batch_data: List[Dict]) -> List[Dict]:
        """Validar e corrigir dados do lote"""
        validated = []
        
        for row in batch_data:
            # Garantir que todas as colunas existam
            validated_row = {}
            for col in self.csv_columns:
                validated_row[col] = row.get(col, "Não informado")
            
            # Validações específicas
            validated_row = self.apply_business_rules(validated_row)
            validated.append(validated_row)
            
        return validated

    def apply_business_rules(self, row: Dict) -> Dict:
        """Aplicar regras de negócio e validações"""
        # Validar formato de ano
        if row.get("Ano") and row["Ano"] != "Não informado":
            try:
                ano = int(str(row["Ano"]).strip())
                if 2010 <= ano <= 2030:
                    row["Ano"] = str(ano)
                else:
                    row["Ano"] = "Não informado"
            except:
                row["Ano"] = "Não informado"
        
        # Validar trimestre
        if row.get("Trimestre") and row["Trimestre"] != "Não informado":
            trimestre = str(row["Trimestre"]).strip().upper()
            if trimestre not in ["1T", "2T", "3T", "4T"]:
                row["Trimestre"] = "Não informado"
        
        # Calcular margens se possível
        row = self.calculate_margins(row)
        
        return row

    def calculate_margins(self, row: Dict) -> Dict:
        """Calcular margens financeiras quando possível"""
        try:
            # Extrair valores numéricos
            receita = self.extract_numeric_value(row.get("Receita", ""))
            ebitda = self.extract_numeric_value(row.get("EBITDA", ""))
            lucro_liquido = self.extract_numeric_value(row.get("Lucro_liquido", ""))
            
            if receita and receita > 0:
                if ebitda:
                    margem_ebitda = (ebitda / receita) * 100
                    row["Margem_EBITDA"] = f"{margem_ebitda:.1f}%"
                
                if lucro_liquido:
                    margem_liquida = (lucro_liquido / receita) * 100
                    row["Margem_liquida"] = f"{margem_liquida:.1f}%"
                    
        except Exception as e:
            logger.warning(f"Erro ao calcular margens: {e}")
            
        return row

    def extract_numeric_value(self, value_str: str) -> float:
        """Extrair valor numérico de string formatada"""
        if not value_str or value_str == "Não informado":
            return None
            
        # Remover texto e manter apenas números e pontos/vírgulas
        numeric_part = re.findall(r'[\d.,]+', str(value_str))
        if numeric_part:
            # Converter vírgula para ponto e remover pontos de milhares
            num_str = numeric_part[0].replace('.', '').replace(',', '.')
            try:
                return float(num_str)
            except:
                return None
        return None

    def save_to_csv(self, normalized_data: List[Dict], output_file: str = "gerdau_normalizado.csv"):
        """Salvar dados normalizados em CSV com validação"""
        try:
            with open(output_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_columns)
                writer.writeheader()
                
                for row in normalized_data:
                    # Garantir que todas as colunas estejam presentes
                    complete_row = {}
                    for col in self.csv_columns:
                        complete_row[col] = row.get(col, "Não informado")
                    writer.writerow(complete_row)
                    
            logger.info(f"CSV salvo com sucesso: {output_file}")
            
            # Gerar relatório de qualidade
            self.generate_quality_report(normalized_data, output_file)
            
        except Exception as e:
            logger.error(f"Erro ao salvar CSV: {e}")
            raise

    def generate_quality_report(self, data: List[Dict], csv_file: str):
        """Gerar relatório de qualidade dos dados"""
        df = pd.DataFrame(data)
        
        report = {
            "total_registros": len(data),
            "anos_cobertos": sorted(df["Ano"].unique().tolist()),
            "trimestres_por_ano": df.groupby("Ano")["Trimestre"].count().to_dict(),
            "completude_dados": {},
            "estatisticas_financeiras": {}
        }
        
        # Analisar completude
        for col in ["Receita", "EBITDA", "Lucro_liquido", "Producao"]:
            informados = df[df[col] != "Não informado"].shape[0]
            report["completude_dados"][col] = f"{informados}/{len(data)} ({informados/len(data)*100:.1f}%)"
        
        # Estatísticas financeiras básicas
        for col in ["Receita", "EBITDA", "Lucro_liquido"]:
            valores_numericos = []
            for valor in df[col]:
                num = self.extract_numeric_value(valor)
                if num:
                    valores_numericos.append(num)
            
            if valores_numericos:
                report["estatisticas_financeiras"][col] = {
                    "min": min(valores_numericos),
                    "max": max(valores_numericos),
                    "media": sum(valores_numericos) / len(valores_numericos)
                }
        
        # Salvar relatório
        report_file = csv_file.replace(".csv", "_relatorio_qualidade.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Relatório de qualidade salvo: {report_file}")
        return report

    def process_financial_data(self, input_file: str, output_file: str = "gerdau_normalizado.csv", batch_size: int = 3):
        """Processo principal de normalização"""
        try:
            # 1. Carregar dados do Agente 1
            ag1_data = self.load_agent1_data(input_file)
            
            # 2. Normalizar via LLM
            normalized_data = self.normalize_json_llm(ag1_data, batch_size)
            
            # 3. Salvar CSV
            self.save_to_csv(normalized_data, output_file)
            
            # 4. Retornar estatísticas
            return {
                "registros_processados": len(normalized_data),
                "arquivo_saida": output_file,
                "colunas": len(self.csv_columns)
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
            raise

    def normalize_json_llm(self, ag1_data: List[Dict], batch_size: int = 3) -> List[Dict]:
        """Normalizar dados usando LLM com tratamento robusto de erros"""
        results = []
        total_batches = (len(ag1_data) - 1) // batch_size + 1
        
        logger.info(f"Iniciando normalização: {len(ag1_data)} registros → {total_batches} lotes")
        
        for i in range(0, len(ag1_data), batch_size):
            batch = ag1_data[i:i+batch_size]
            batch_num = i // batch_size + 1
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Lote {batch_num}/{total_batches} - Tentativa {attempt + 1}")
                    
                    prompt = self.create_enhanced_prompt(batch)
                    
                    response = self.llm.chat.completions.create(
                        model=AZURE_OPENAI_DEPLOYMENT_NAME,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=6000
                    )
                    
                    content = response.choices[0].message.content
                    content = self.clean_json_response(content)
                    
                    batch_results = json.loads(content)
                    validated_batch = self.validate_batch_data(batch_results)
                    results.extend(validated_batch)
                    
                    logger.info(f"✓ Lote {batch_num} processado: {len(validated_batch)} registros")
                    break
                    
                except Exception as e:
                    logger.warning(f"Erro na tentativa {attempt + 1} do lote {batch_num}: {e}")
                    if attempt == max_retries - 1:
                        logger.error(f"✗ Lote {batch_num} falhou após {max_retries} tentativas")
                    else:
                        time.sleep(2)  # Pausa antes da próxima tentativa
            
            time.sleep(1)  # Pausa entre lotes
        
        logger.info(f"Normalização concluída: {len(results)} registros válidos")
        return results


# === FUNÇÃO PRINCIPAL ===
def main():
    """Executar normalização completa"""
    try:
        # Inicializar normalizador
        normalizer = FinancialDataNormalizer()
        
        # Processar dados
        resultado = normalizer.process_financial_data(
            input_file="analise_financeira_gerdau.json",
            output_file="gerdau_normalizado_v2.csv",
            batch_size=3
        )
        
        print("\n=== NORMALIZAÇÃO CONCLUÍDA ===")
        print(f"Registros processados: {resultado['registros_processados']}")
        print(f"Arquivo gerado: {resultado['arquivo_saida']}")
        print(f" Colunas estruturadas: {resultado['colunas']}")
        
        # Mostrar preview dos dados
        df = pd.read_csv(resultado['arquivo_saida'])
        print(f"\n=== PREVIEW DOS DADOS ===")
        print(df.head())
        print(f"\nShape: {df.shape}")
        
    except Exception as e:
        logger.error(f"Erro na execução principal: {e}")
        raise


if __name__ == "__main__":
    main()