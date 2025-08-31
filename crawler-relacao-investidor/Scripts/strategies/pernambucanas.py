# Scripts/strategies/pernambucanas.py

from typing import List
from playwright.sync_api import sync_playwright
import requests
from .interface import RaspagemStrategy
from model import RelatorioFinanceiro
from Scripts.services.context import preparar_pastas_base
from empresas_ri.registry import EMPRESAS_RI

class PernambucanasStrategy(RaspagemStrategy):
    """Estratégia específica para raspagem do RI da Pernambucanas."""

    def __init__(self):
        self._empresa = "Pernambucanas"

    @property
    def empresa(self) -> str:
        return self._empresa

    def baixar_relatorios(self) -> List[RelatorioFinanceiro]:
        empresa_cfg = EMPRESAS_RI[self.empresa]
        link = empresa_cfg.url
        relatorios = []

        with sync_playwright() as p:
            navegador = p.firefox.launch(headless=True)
            pagina = navegador.new_page()
            pagina.goto(link)
            pagina.wait_for_selector("#fano")

            anos_disponiveis = pagina.eval_on_selector_all(
                "#fano option",
                "elements => elements.map(el => el.value)"
            )

            ano_atual = int(anos_disponiveis[0])
            anos_filtrados = [str(ano) for ano in range(2019, ano_atual + 1)]

            for ano in anos_filtrados:
                print(f"\nSelecionando ano: {ano}")
                pagina.select_option("#fano", value=ano)
                pagina.wait_for_timeout(1000)

                # Ativa a seção de balanços
                headers = pagina.locator(".accordion__item__header")
                headers.first.click()
                pagina.wait_for_selector(".table-arquivos")

                linhas = pagina.locator(".table-arquivos tr")
                count_linhas = linhas.count()
                print(f"Linhas encontradas: {count_linhas}")

                for i in range(count_linhas):
                    linha = linhas.nth(i)
                    texto = linha.inner_text().strip()

                    # Tenta identificar o tipo de relatório baseado no nome_site configurado
                    tipo_relatorio_encontrado = None
                    for tipo in empresa_cfg.tipos_relatorios:
                        if tipo.nome_site in texto:
                            tipo_relatorio_encontrado = tipo
                            break

                    if not tipo_relatorio_encontrado:
                        continue

                    a_tag = linha.locator("a").first
                    if not a_tag:
                        print("Link não encontrado na linha, pulando...")
                        continue

                    href = a_tag.get_attribute("href")
                    if not href:
                        print("href vazio, pulando...")
                        continue

                    pdf_url = href if href.startswith("http") else empresa_cfg.url + href

                    print(f"Baixando PDF direto: {pdf_url}")

                    try:
                        r = requests.get(pdf_url)
                        r.raise_for_status()

                        nome_arquivo = f"{ano}_anual_{tipo_relatorio_encontrado.sigla}.pdf"

                        base_pasta = preparar_pastas_base(self.empresa, ano)
                        pasta_originais = base_pasta / "originais"
                        caminho_arquivo = pasta_originais / nome_arquivo

                        with open(caminho_arquivo, "wb") as f:
                            f.write(r.content)

                        relatorios.append(RelatorioFinanceiro(
                            empresa=self.empresa,
                            categoria="Demonstrações Financeiras",
                            ano=ano,
                            trimestre="anual",
                            download_url=pdf_url,
                            caminho_arquivo=str(caminho_arquivo)
                        ))
                    except Exception as e:
                        print(f"Erro ao baixar {pdf_url}: {e}")

            navegador.close()

        return relatorios