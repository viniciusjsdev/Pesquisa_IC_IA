import os
from langchain_community.document_loaders import TextLoader, PythonLoader, NotebookLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import time
from langchain_community.document_loaders import TextLoader, PythonLoader, NotebookLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import AzureOpenAI
import json

# === 1. Definir chave da API===
os.environ["AZURE_OPENAI_API_KEY"] = "2RqPmZXkJFTihAPvhpr4UQtLWLeIeCgj4u7VUIcXJMo2651D3ZneJQQJ99BFACHYHv6XJ3w3AAAAACOGtmyP"
os.environ["AZURE_INFERENCE_ENDPOINT"] =  "https://chatgpt-resourc.openai.azure.com/"
os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4.1"  

# === 2. Inicializar LLM ===
llm = AzureOpenAI(
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_INFERENCE_ENDPOINT"],
    api_version="2025-01-01-preview"
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
        - Ignore textos institucionais, gráficos e informações irrelevantes.
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
        }}
        """

        try:
            response = llm.chat.completions.create(
                model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            data = response.content if hasattr(response, "content") else str(response)
            all_results.append({"batch": i//batch_size + 1, "data": data})
            print(f"✓ Processado batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")
            time.sleep(1)
        except Exception as e:
            print(f"✗ Erro no batch {i//batch_size + 1}: {e}")
            all_results.append({"batch": i//batch_size + 1, "data": None})

    return all_results

def main():
    base_folder = r"C:\Users\welli\OneDrive\Documentos\GitHub\Pesquisa_IC_DataSciente_4SM\crawler-relacao-investidor\pdfs\Gerdau"
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