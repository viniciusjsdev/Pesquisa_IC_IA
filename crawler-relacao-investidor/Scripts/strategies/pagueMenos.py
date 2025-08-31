# Scripts/strategies/pagueMenos.py

from typing import List
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from .interface import RaspagemStrategy
from model import RelatorioFinanceiro
from empresas_ri.registry import EMPRESAS_RI
from Scripts.services.context import preparar_pastas_base
import requests
from concurrent.futures import ThreadPoolExecutor
import requests

class PagueMenosStrategy(RaspagemStrategy):
    """Estratégia específica para raspagem do RI da Pague Menos."""

    def __init__(self):
        self._empresa = "PagueMenos"

    @property
    def empresa(self) -> str:
        return self._empresa

    @staticmethod
    def baixar_arquivo(href, caminho_arquivo, empresa, categoria, ano, trimestre):
        try:
            response = requests.get(href)
            with open(caminho_arquivo, "wb") as f:
                f.write(response.content)
            print(f"Download concluído: {caminho_arquivo.name}")
            return True, (href, caminho_arquivo, empresa, categoria, ano, trimestre)

        except Exception as e:
            print(f"Erro ao baixar {href}: {e}")
            return False, (href, caminho_arquivo, empresa, categoria, ano, trimestre)

    def baixar_relatorios(self) -> List[RelatorioFinanceiro]:
        empresa_cfg = EMPRESAS_RI[self.empresa]
        link = empresa_cfg.url
        relatorios = []

        
        with sync_playwright() as p:
            navegador = p.firefox.launch(headless=True)
            pagina = navegador.new_page()

            # Bloquear imagens, fontes, etc. para acelerar
            pagina.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "font"] else route.continue_())
            pagina.goto(link)

            pagina.wait_for_selector('#tabela_1')
            pagina.wait_for_selector("#fano")

            cabecalhos = pagina.locator("#tabela_1 thead tr th")
            trimestres = [
                th.inner_text().strip()[:2]
                for th in cabecalhos.all()
                if "T" in th.inner_text()
            ]

            anos_disponiveis = pagina.eval_on_selector_all(
                "#fano option",
                "elements => elements.map(el => el.value)"
            )

            ano_atual = int(anos_disponiveis[0])
            anos_filtrados = [str(ano) for ano in range(ano_atual - 5, ano_atual + 1)]

            downloads = []

            for ano in anos_filtrados:
                print(f"\nSelecionando ano: {ano}")
                pagina.select_option("#fano", value=ano)
                pagina.wait_for_selector("#tabela_1")  # Espera real ao invés de timeout

                base_pasta = preparar_pastas_base(self.empresa, ano)
                pasta_originais = base_pasta / "originais"

                for tipo in empresa_cfg.tipos_relatorios:
                    linha = pagina.locator(f"//td[@class='first titulo' and contains(., '{tipo.nome_site}')]/..")
                    icones = linha.locator("td.icone")

                    for i in range(len(trimestres)):
                        trimestre = trimestres[i]
                        a = icones.nth(i).locator("a")
                        if a.count() > 0:
                            href = a.get_attribute("href")
                            if href:
                                info = empresa_cfg.obter_categoria_e_sigla(tipo.nome_site, trimestre)
                                sigla = info["sigla"].replace("/", "-").replace("\\", "-")
                                categoria = info["categoria"]
                                nome_arquivo = f"{ano}_{trimestre}_{sigla}.pdf"
                                caminho_arquivo = pasta_originais / nome_arquivo

                                print(f"Agendando download: {nome_arquivo}")
                                downloads.append((href, caminho_arquivo, self.empresa, categoria, ano, trimestre))

            navegador.close()

        #Paraleliza os downloads com ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(self.baixar_arquivo, href, caminho, empresa, categoria, ano, trimestre): (href, caminho, empresa, categoria, ano, trimestre)
                for href, caminho, empresa, categoria, ano, trimestre in downloads
            }

            for future in futures:
                success, _ = future.result()
                if success:
                    href, caminho, empresa, categoria, ano, trimestre = futures[future]
                    relatorios.append(RelatorioFinanceiro(
                        empresa=empresa,
                        categoria=categoria,
                        ano=ano,
                        trimestre=trimestre,
                        download_url=href,
                        caminho_arquivo=str(caminho)
                    ))

        return relatorios