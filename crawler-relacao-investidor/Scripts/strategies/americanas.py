# Scripts/strategies/americanas.py

from typing import List
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from .interface import RaspagemStrategy
from model import RelatorioFinanceiro
from empresas_ri.registry import EMPRESAS_RI
from Scripts.services.context import preparar_pastas_base
import requests

class AmericanasStrategy(RaspagemStrategy):
    """Estratégia específica para raspagem do RI do Grupo Americanas SA."""

    def __init__(self):
        self._empresa = "AmericanasSA"

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
            pagina.route("**/*", lambda route, request: route.abort() if request.resource_type in ["image", "font", "stylesheet"] else route.continue_())
            pagina.goto(link)

            pagina.wait_for_selector('#tabela_1')
            pagina.wait_for_selector("#fano")

            cabecalhos = pagina.locator("#tabela_1 thead tr th").all()
            trimestres = [
                th.inner_text().strip()[:2]
                for th in cabecalhos if "T" in th.inner_text()
            ]

            anos_disponiveis = pagina.eval_on_selector_all(
                "#fano option",
                "elements => elements.map(el => el.value)"
            )

            ano_atual = int(anos_disponiveis[0])
            anos_filtrados = [str(ano) for ano in range(ano_atual - 5, ano_atual + 1)]

            for ano in anos_filtrados:
                print(f"\nSelecionando ano: {ano}")
                pagina.select_option("#fano", value=ano)
                pagina.wait_for_selector("table#tabela_1 td.icone >> nth=0", timeout=5000)

                base_pasta = preparar_pastas_base(self.empresa, ano)
                pasta_originais = base_pasta / "originais"

                for tipo in empresa_cfg.tipos_relatorios:
                    linha = pagina.locator(f"//td[@class='first titulo' and contains(., '{tipo.nome_site}')]/..")
                    icones = linha.locator("td.icone").all()

                    for i, icone in enumerate(icones[:len(trimestres)]):
                        trimestre = trimestres[i]
                        a = icone.locator("a")
                        if a.count() > 0:
                            href = a.get_attribute("href")
                            if href:
                                info = empresa_cfg.obter_categoria_e_sigla(tipo.nome_site, trimestre)
                                sigla = info["sigla"]
                                categoria = info["categoria"]

                                sigla_sanitizada = sigla.replace("/", "-").replace("\\", "-")
                                nome_arquivo = f"{ano}_{trimestre}_{sigla_sanitizada}.pdf"
                                caminho_arquivo = pasta_originais / nome_arquivo

                                print(f"Baixando {nome_arquivo}")
                                try:
                                    r = requests.get(href)
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
