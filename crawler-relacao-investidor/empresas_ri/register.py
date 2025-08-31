# empresas_ri/register.py

from empresas_ri.registry import EMPRESAS_RI
from model import EmpresaRI

def registrar_empresa(empresa: EmpresaRI) -> EmpresaRI:
    EMPRESAS_RI[empresa.nome] = empresa
    return empresa
