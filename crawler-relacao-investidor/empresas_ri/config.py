# empresas_ri/config.py

from model import EmpresaRI, TipoRelatorio
from empresas_ri.register import registrar_empresa

gpa = registrar_empresa(EmpresaRI(
    nome="GPA",
    url="https://www.gpari.com.br/informacoes-financeiras/resultados-trimestrais/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Apresentação", sigla=TipoRelatorio.SIGLA_AP),
        TipoRelatorio(nome_site="Demonstrações Financeiras", sigla=TipoRelatorio.SIGLA_ITR_DFP),
        TipoRelatorio(nome_site="Release de Resultados", sigla=TipoRelatorio.SIGLA_RR)
    ]
))

casas_bahia = registrar_empresa(EmpresaRI(
    nome="CasasBahia",
    url="https://ri.grupocasasbahia.com.br/informacoes-financeiras/central-de-resultados/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Resultados Trimestrais", sigla=TipoRelatorio.SIGLA_RR),
        TipoRelatorio(nome_site="ITR/DFP", sigla=TipoRelatorio.SIGLA_ITR),
        TipoRelatorio(nome_site="Apresentação", sigla=TipoRelatorio.SIGLA_AP)
    ]
))

magalu = registrar_empresa(EmpresaRI(
    nome="MAGALU",
    url="https://ri.magazineluiza.com.br/ListResultados/Central-de-Resultados?=0WX0bwP76pYcZvx+vXUnvg==&linguagem=pt",
    tipos_relatorios=[
        TipoRelatorio(nome_site="RELEASES", sigla=TipoRelatorio.SIGLA_RR),
        TipoRelatorio(nome_site="ITR/DFP", sigla=TipoRelatorio.SIGLA_ITR),
        TipoRelatorio(nome_site="APRESENTAÇÃO", sigla=TipoRelatorio.SIGLA_AP)
    ]
))

raia_drogasil = registrar_empresa(EmpresaRI(
    nome="RaiaDrogasil",
    url="https://ri.rdsaude.com.br/central-de-resultados",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Resultados", sigla=TipoRelatorio.SIGLA_RR),
        TipoRelatorio(nome_site="ITR", sigla=TipoRelatorio.SIGLA_ITR),
        TipoRelatorio(nome_site="DFP", sigla=TipoRelatorio.SIGLA_DFP),
        TipoRelatorio(nome_site="Apresentação", sigla=TipoRelatorio.SIGLA_AP)
    ]
))

americanas = registrar_empresa(EmpresaRI(
    nome="AmericanasSA",
    url="https://ri.americanas.io/informacoes-aos-investidores/central-de-resultados/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Release de Resultado", sigla=TipoRelatorio.SIGLA_RR),
        TipoRelatorio(nome_site="Relatórios Anuais", sigla="RA"),
        TipoRelatorio(nome_site="ITR", sigla=TipoRelatorio.SIGLA_ITR),
        TipoRelatorio(nome_site="DFP", sigla=TipoRelatorio.SIGLA_DFP),
        TipoRelatorio(nome_site="Apresentações", sigla=TipoRelatorio.SIGLA_AP)
    ]
))

pague_menos = registrar_empresa(EmpresaRI(
    nome="PagueMenos",
    url="https://ri.paguemenos.com.br/informacoes-aos-investores/central-de-resultados/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Apresentação da Teleconferência", sigla=TipoRelatorio.SIGLA_AP),
        TipoRelatorio(nome_site="Demonstrações Financeiras ITR/DFP", sigla=TipoRelatorio.SIGLA_ITR_DFP),
        TipoRelatorio(nome_site="Release de Resultados", sigla=TipoRelatorio.SIGLA_RR)
    ]
))

pernambucanas = registrar_empresa(EmpresaRI(
    nome="Pernambucanas",
    url="https://ri.pernambucanas.com.br/central-de-resultados/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Arthur Lundgren Tecidos S.A. – Casas Pernambucanas", sigla="RA")
    ]
))

gerdau = registrar_empresa(EmpresaRI(
    nome="Gerdau",
    url="https://ri.gerdau.com/informacoes-ao-mercado/central-de-resultados/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Resultados Trimestrais", sigla=TipoRelatorio.SIGLA_RR),
        TipoRelatorio(nome_site="Demonstrações Financeiras ITR/DFP", sigla=TipoRelatorio.SIGLA_ITR_DFP),
        TipoRelatorio(nome_site="Apresentação dos Resultados", sigla=TipoRelatorio.SIGLA_AP)
    ]
))