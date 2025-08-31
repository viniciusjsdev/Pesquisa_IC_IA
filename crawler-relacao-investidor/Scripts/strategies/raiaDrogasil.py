# Scripts/strategies/raiaDrogasil.py

from turtle import down
import requests
import re
from typing import List
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from .interface import RaspagemStrategy
from model import RelatorioFinanceiro
from datetime import datetime
from Scripts.services.context import preparar_pastas_base
from empresas_ri.registry import EMPRESAS_RI

class RaiaDrogasilStrategy(RaspagemStrategy):
    """Estratégia específica para raspagem do RI da Raia Drogasil (RD Saúde)."""

    def __init__(self):
        self._empresa = "RaiaDrogasil"

    @property
    def empresa(self) -> str:
        return self._empresa

    def baixar_relatorios(self) -> List[RelatorioFinanceiro]:
        empresa_cfg = EMPRESAS_RI[self.empresa]
        url = empresa_cfg.url
        relatorios = []

        with sync_playwright() as p:
            navegador = p.firefox.launch(headless=True)
            pagina = navegador.new_page()
            pagina.route("**/*", lambda route, request: route.abort() if request.resource_type in ["image", "font", "stylesheet"] else route.continue_())
            print(f"[DEBUG] Indo para {url}")
            pagina.goto(url)
            pagina.wait_for_load_state("networkidle")

            try:
                pagina.locator("#onetrust-reject-all-handler").click(timeout=3000)
            except:
                print("[DEBUG] Banner de cookies não encontrado.")

            ano_atual = datetime.now().year

            for i, ano in enumerate(range(ano_atual, ano_atual - 6, -1)):
                id_tabela = f"tab{ano}"

                try:
                    pagina.evaluate(
                        """
                        (idTabela) => {
                            const todas = document.querySelectorAll('[id^="tab"]');
                            todas.forEach(div => {
                                if (div.id === idTabela) {
                                    div.className = "divCentral tab-pane fade active show";
                                } else {
                                    div.className = "divCentral tab-pane fade";
                                }
                            });
                        }
                        """,
                        id_tabela
                    )
                    pagina.wait_for_timeout(1000)

                    ids_trimestres = {
                        "1T": f"ContentInternal_ContentPlaceHolderConteudo_rptResultados_liPrimeiroTri_{i}",
                        "2T": f"ContentInternal_ContentPlaceHolderConteudo_rptResultados_liSegundoTri_{i}",
                        "3T": f"ContentInternal_ContentPlaceHolderConteudo_rptResultados_liTerceiroTri_{i}",
                        "4T": f"ContentInternal_ContentPlaceHolderConteudo_rptResultados_liQuartoTri_{i}",
                    }

                    for trimestre_sigla, trimestre_id in ids_trimestres.items():

                        try:
                            pagina.evaluate(
                                """
                                (idTrimestre) => {
                                    const tab = document.getElementById(idTrimestre);
                                    if (tab && tab.querySelector("a")) {
                                        tab.querySelector("a").click();
                                    }
                                }
                                """,
                                trimestre_id
                            )
                            pagina.wait_for_timeout(1000)

                            aba = pagina.locator(f"#{id_tabela}")
                            links = aba.locator(".itens-result a")
                            num_links = links.count()

                            for k in range(num_links):
                                tag = links.nth(k)
                                texto = tag.inner_text().strip()
                                href = tag.get_attribute("href")

                                if not href or not href.endswith(".pdf"):
                                    if "Download.aspx?Arquivo=" in href:
                                        href = f"https://ri.rdsaude.com.br/{href}"
                                    else:
                                        continue

                                texto_upper = texto.upper()
                                tipo_encontrado = None

                                # Detecta tipo com base em tipos_relatorios
                                for tipo in empresa_cfg.tipos_relatorios:
                                    if tipo.nome_site.upper() in texto_upper:
                                        tipo_encontrado = tipo
                                        break

                                if not tipo_encontrado:
                                    continue

                                match_trimestre = re.search(r"([1-4]T)(\d{2,4})", texto_upper)

                                match_dfp_ano = None
                                if tipo_encontrado.sigla == "DFP" and not match_trimestre:
                                    match_dfp_ano = re.search(r"DFP\s*(\d{4})", texto_upper)

                                if not match_trimestre and not match_dfp_ano:
                                    continue

                                if match_trimestre:
                                    trimestre = match_trimestre.group(1)
                                    ano_real = match_trimestre.group(2)
                                    if len(ano_real) == 2:
                                        ano_real = "20" + ano_real
                                elif match_dfp_ano:
                                    trimestre = "4T"
                                    ano_real = match_dfp_ano.group(1)

                                if ano_real != str(ano):
                                    continue

                                nome_pdf = f"{ano_real}_{trimestre}_{tipo_encontrado.sigla}.pdf"

                                try:
                                    pasta = preparar_pastas_base(self.empresa, ano_real)
                                    caminho = pasta / "originais" / nome_pdf

                                    print(f"[DEBUG] Baixando: {nome_pdf}")

                                    with pagina.expect_download() as download_info:
                                        tag.scroll_into_view_if_needed()
                                        tag.click()
                                    download = download_info.value
                                    download.save_as(str(caminho))

                                    relatorios.append(RelatorioFinanceiro(
                                        empresa=self.empresa,
                                        categoria=tipo_encontrado.nome_site,
                                        ano=ano_real,
                                        trimestre=trimestre,
                                        download_url=href,
                                        caminho_arquivo=str(caminho)
                                    ))
                                except Exception as e:
                                    print(f"[ERROR] Erro ao baixar {href}: {e}")

                        except Exception as e:
                            print(f"[ERROR] Erro ao ativar trimestre {trimestre_sigla} de {ano}: {e}")

                except Exception as e:
                    print(f"[ERROR] Erro ao processar ano {ano}: {e}")

            navegador.close()
            print(f"[DEBUG] Total de relatórios coletados: {len(relatorios)}")

        return relatorios