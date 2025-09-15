import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
from openai import AzureOpenAI
import json
from config import (
    AZURE_OPENAI_API_KEY,
    AZURE_INFERENCE_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_API_VERSION,
)

# === 2. Inicializar LLM ===
llm = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_INFERENCE_ENDPOINT,
    api_version=AZURE_API_VERSION
)

def load_txt_from_anos(base_folder: str):
    """Carrega todos os arquivos .txt da subpasta 'textos' de cada ano"""
    documents = []
    if not os.path.exists(base_folder):
        print(f"Pasta '{base_folder}' não encontrada!")
        return documents

    for ano in os.listdir(base_folder):
        ano_path = os.path.join(base_folder, ano)
        textos_path = os.path.join(ano_path, "textos")
        if os.path.exists(textos_path):
            for file_name in os.listdir(textos_path):
                if file_name.endswith(".txt"):
                    file_path = os.path.join(textos_path, file_name)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        doc = {
                            "page_content": content,
                            "metadata": {"source_file": os.path.relpath(file_path, base_folder)}
                        }
                        documents.append(doc)
                        print(f"Carregado: {doc['metadata']['source_file']}")
                    except Exception as e:
                        print(f"Erro ao carregar {file_name}: {e}")
    return documents

def analyze_documents_llm(documents, llm, chunk_size=2000, chunk_overlap=200, batch_size=3):
    """Analisa documentos usando LLM em chunks e retorna JSON-like"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    # Criar chunks de todos os documentos
    all_chunks = []
    for doc in documents:
        chunks = splitter.split_text(doc["page_content"])
        for c in chunks:
            all_chunks.append({"chunk": c, "source_file": doc["metadata"]["source_file"]})
    print(f"Total de chunks: {len(all_chunks)}")

    all_results = []

    # Processar em batches
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        combined_content = "\n\n---ARQUIVO---\n\n".join(
            [f"ARQUIVO: {b['source_file']}\n{b['chunk']}" for b in batch]
        )

        prompt = f"""
        Documentos financeiros da Gerdau:
        {combined_content}
        Ação:
        - Analise o conteúdo e extraia apenas dados financeiros relevantes: Receita, EBITDA, Lucro líquido,
          Produção, Capacidade instalada, Despesas operacionais, Dívida líquida.
        - Ignore textos institucionais e informações irrelevantes.
        - Retorne em JSON-like, incluindo o nome do arquivo:
        {{
            "Arquivo": "...",
            "Receita": "...",
            "EBITDA": "...",
            "Lucro_liquido": "...",
            "Producao": "...",
            "Capacidade": "...",
            "Despesas": "...",
            "Divida_liquida": "..."
            "Retorno sobre Patrimônio Líquido (ROE)": "..."
            "Retorno sobre Ativos (ROA)": "..."
            "Fluxo de Caixa Operacional": "..."
            "Fluxo de Caixa Livre": "..."
            "Fluxo de Caixa de Investimento": "..."
            "Fluxo de Caixa de Financiamento": "..."
            "Divida Bruta": "..."
            "Divida de Curto Prazo": "..."
            "Divida de Longo Prazo": "..."
            "Dividendos": "..."
        }}

        - Retorne apenas um objeto JSON válido por arquivo.
        - Se não encontrar dados financeiros, retorne null para esses campos.
        - Não inclua comentários, explicações ou texto adicional.
        """

        try:
            response = llm.chat.completions.create(
                model=AZURE_OPENAI_DEPLOYMENT_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            if hasattr(response, "content"):
                content = response.content
            elif hasattr(response, "choices") and len(response.choices) > 0:
                content = response.choices[0].message.content
            else:
                content = str(response)

            all_results.append({"batch": i//batch_size + 1, "data": content})
            print(f"Processado batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
            time.sleep(1)

        except Exception as e:
            print(f"Erro no batch {i//batch_size + 1}: {e}")
            all_results.append({"batch": i//batch_size + 1, "data": None})

    return all_results

def main():
    base_folder = r"E:\Projetos\Github_ViniciusJ\Pesquisa_IC_IA\crawler-relacao-investidor\pdfs\Gerdau"
    documents = load_txt_from_anos(base_folder)
    if not documents:
        print("Nenhum arquivo .txt encontrado na pasta 'textos'.")
        return

    analysis_results = analyze_documents_llm(documents, llm)

    # Salvar resultado final
    with open("analise_financeira_gerdau.json", "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)

    print(f"\nAnálise salva em 'analise_financeira_gerdau.json'")

if __name__ == "__main__":
    main()