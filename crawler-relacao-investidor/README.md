# Projeto de Extração e Processamento de Relatórios Financeiros

Este projeto automatiza a **coleta**, **extração de texto** e **organização** de relatórios financeiros (ITR, DFP, AP, RL, etc.) publicados por empresas em seus portais de Relações com Investidores (RI).

## Funcionalidades

- **Raspagem automática** de arquivos PDF diretamente dos sites das empresas.
- **Extração de texto robusta**, inclusive de PDFs protegidos contra cópia.
- **Processamento paralelo** para ganho de performance em múltiplos núcleos.
- Geração de saídas estruturadas em **.txt**, **.json** e **.csv**.
- **Cache inteligente** para evitar reprocessamento desnecessário.
- Os arquivos `.json` gerados incluem metadados e texto completo, e são usados como **base de treinamento para LLMs (Large Language Models)**, facilitando aplicações de IA no domínio financeiro.

## Estrutura Modular

O projeto utiliza o **padrão Strategy**, permitindo integração fácil de múltiplas empresas com comportamentos distintos de raspagem. Cada empresa tem sua própria estratégia encapsulada, garantindo organização e flexibilidade.

## Como Adicionar Novas Empresas

A inclusão de novas empresas é feita em três passos simples:

### 1. Criar a Estratégia

Crie um novo arquivo dentro da pasta `Scripts/strategies/` com o nome da empresa, por exemplo:

```bash
Scripts/strategies/pernambucanas_strategy.py
```

Esse arquivo deve conter uma classe que herda de `RaspagemStrategy` e implementa o método `baixar_relatorios()` com a lógica de raspagem específica.

### 2. Registrar a Estratégia

No arquivo `Scripts/factory.py`, registre a nova estratégia no dicionário de fábricas, por exemplo:

```python
from Scripts.strategies.pernambucanas_strategy import PernambucanasStrategy

STRATEGY_FACTORY = {
    "Pernambucanas": PernambucanasStrategy,
    # outras empresas...
}
```

### 3. Configurar a Empresa

No `Scripts/config.py`, registre a empresa com os tipos de relatórios disponíveis:

```python
from Scripts.config_models import EmpresaRI, TipoRelatorio, registrar_empresa

pernambucanas = registrar_empresa(EmpresaRI(
    nome="Pernambucanas",
    url="https://ri.pernambucanas.com.br/central-de-resultados/",
    tipos_relatorios=[
        TipoRelatorio(nome_site="Arthur Lundgren Tecidos S.A. – Casas Pernambucanas", sigla="RA")
    ]
))
```

A sigla será utilizada no nome dos arquivos gerados, com o padrão:

```bash
<ano>_anual_<sigla>.pdf
# Exemplo: 2020_anual_RA.pdf
```

> Se houver relatórios trimestrais, a lógica pode ser expandida para incluir `_1T`, `_2T`, etc., conforme necessário.

---

Depois disso, a nova empresa poderá ser processada normalmente com os comandos e scripts existentes no pipeline, sem qualquer modificação adicional na lógica central.

## OBSERVAÇÃO

É necessário incluir a extração de tabelas no pipeline, utilizando o PaddleOCR. Essa funcionalidade será incorporada na função responsável pelo processamento dos arquivos PDF extraindo texto e tabela simultaneamente:

Coleta_e_Processamento_RI_Empresas\Scripts\services\context.py → _processar_pdf()
