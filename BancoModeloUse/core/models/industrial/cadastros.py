# core/models/industrial/cadastros.py
"""
Modelos de cadastros industriais
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL
from . import IndustrialBase

class Produto(IndustrialBase):
    __tablename__ = "produtos"
    produto_id = Column(Integer, primary_key=True, index=True)
    nome_produto = Column(String, nullable=False)
    descricao = Column(Text)
    unidade_medida = Column(String)

class Material(IndustrialBase):
    __tablename__ = "materiais"
    material_id = Column(Integer, primary_key=True, index=True)
    nome_material = Column(String, nullable=False)
    unidade_medida = Column(String)

class Maquina(IndustrialBase):
    __tablename__ = "maquinas"
    maquina_id = Column(Integer, primary_key=True, index=True)
    nome_maquina = Column(String, nullable=False)
    linha_producao = Column(String)
    capacidade_producao_max = Column(DECIMAL)

class Fornecedor(IndustrialBase):
    __tablename__ = "fornecedores"
    fornecedor_id = Column(Integer, primary_key=True, index=True)
    nome_fornecedor = Column(String, nullable=False)
