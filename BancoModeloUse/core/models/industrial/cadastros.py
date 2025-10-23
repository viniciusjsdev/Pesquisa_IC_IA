# core/models/industrial/cadastros.py
"""
Modelos de cadastros industriais
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from infrastructure.database.connections.industrial_connection import Base

class Produto(Base):
    __tablename__ = "produtos"
    produto_id = Column(Integer, primary_key=True, index=True)
    nome_produto = Column(String, nullable=False)
    descricao = Column(Text)
    unidade_medida = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)

class Material(Base):
    __tablename__ = "materiais"
    material_id = Column(Integer, primary_key=True, index=True)
    nome_material = Column(String, nullable=False)
    unidade_medida = Column(String)
    data_registro = Column(DateTime, default=datetime.utcnow)

class Maquina(Base):
    __tablename__ = "maquinas"
    maquina_id = Column(Integer, primary_key=True, index=True)
    nome_maquina = Column(String, nullable=False)
    linha_producao = Column(String)
    capacidade_producao_max = Column(DECIMAL)
    data_registro = Column(DateTime, default=datetime.utcnow)

class Fornecedor(Base):
    __tablename__ = "fornecedores"
    fornecedor_id = Column(Integer, primary_key=True, index=True)
    nome_fornecedor = Column(String, nullable=False)
    data_registro = Column(DateTime, default=datetime.utcnow)
