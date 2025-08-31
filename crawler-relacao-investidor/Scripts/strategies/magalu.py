# Scripts/strategies/magalu.py
from typing import List
from playwright.sync_api import sync_playwright
import requests
from .interface import RaspagemStrategy
from model import RelatorioFinanceiro
from Scripts.services.context import preparar_pastas_base
from empresas_ri.registry import EMPRESAS_RI

class MagaluStrategy(RaspagemStrategy):
    """Estratégia específica para raspagem do RI da Magazine Luiza."""

    def __init__(self):
        self._empresa = "MAGALU"

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

            pagina.wait_for_selector(
                "div[id^='ContentInternal_ContentPlaceHolderConteudo_rptResultados_divResultados_'][ano]",
                timeout=10000
            )

            divs_de_tabelas = pagina.locator(
                "div[id^='ContentInternal_ContentPlaceHolderConteudo_rptResultados_divResultados_'][ano]"
            )
            total_divs = divs_de_tabelas.count()
            print(f"Total de tabelas encontradas: {total_divs}")

            tabelas_por_ano = []
            for i in range(total_divs):
                div = divs_de_tabelas.nth(i)
                ano = int(div.get_attribute("ano"))
                tabelas_por_ano.append((ano, div))

            tabelas_por_ano.sort(reverse=True)
            tabelas_filtradas = tabelas_por_ano[:5]

            tipos_config = {tipo.nome_site.upper(): tipo for tipo in empresa_cfg.tipos_relatorios}

            for ano, div in tabelas_filtradas:
                print(f"\nProcessando ano: {ano}")
                base_pasta = preparar_pastas_base(self.empresa, str(ano))
                pasta_originais = base_pasta / "originais"

                tabela = div.locator("table.results-center-table")
                cabecalhos = tabela.locator("thead tr th").all()
                linhas = tabela.locator("tbody tr").all()

                print(f"Total de linhas para {ano}: {len(linhas)}")

                tipos_colunas = [th.inner_text().strip().upper() for th in cabecalhos[1:]]

                for linha in linhas:
                    colunas = linha.locator("td").all()
                    if len(colunas) < 2:
                        continue

                    trimestre = colunas[0].inner_text().strip()
                    print(f"Trimestre identificado: {trimestre}")

                    for tipo_site, coluna in zip(tipos_colunas, colunas[1:]):
                        if tipo_site not in tipos_config:
                            print(f"Ignorado tipo não configurado: {tipo_site}")
                            continue

                        tipo_cfg = tipos_config[tipo_site]
                        link_element = coluna.locator("a")
                        if link_element.count() == 0:
                            continue

                        href = link_element.get_attribute("href")
                        if not href:
                            continue

                        if not href.startswith("http"):
                            href = f"https://ri.magazineluiza.com.br/{href.lstrip('/')}"

                        try:
                            info = empresa_cfg.obter_categoria_e_sigla(tipo_cfg.nome_site, trimestre)
                        except Exception as e:
                            print(f"Erro ao obter categoria/sigla para {tipo_cfg.nome_site}, {trimestre}: {e}")
                            continue

                        sigla = info["sigla"].replace("/", "-").replace("\\", "-")
                        categoria = info["categoria"]
                        nome_arquivo = f"{ano}_{trimestre}_{sigla}.pdf"
                        caminho_arquivo = pasta_originais / nome_arquivo

                        print(f"Baixando {nome_arquivo} de {href}")
                        try:
                            headers = {"User-Agent": "Mozilla/5.0"}
                            r = requests.get(href, headers=headers, timeout=20)
                            r.raise_for_status()

                            with open(caminho_arquivo, "wb") as f:
                                f.write(r.content)

                            relatorios.append(RelatorioFinanceiro(
                                empresa=self.empresa,
                                categoria=categoria,
                                ano=ano,
                                trimestre=trimestre,
                                download_url=href,
                                caminho_arquivo=str(caminho_arquivo)
                            ))
                        except Exception as e:
                            print(f"Erro ao baixar {href}: {e}")

            navegador.close()

        return relatorios
