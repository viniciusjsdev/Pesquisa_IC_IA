from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "reference" / "template_original.docx"
OUTPUT = ROOT / "ResumoExpandido_Nicoli_Vinicius_FineTuning.docx"
FIGURE = ROOT / "figura_1_desempenho_dominios.png"

RED = "ED1C24"
LIGHT_RED = "FDE9EA"
LIGHT_GRAY = "E7E6E6"
WHITE = "FFFFFF"
BLACK = "000000"


def shade(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=35, start=55, bottom=35, end=55) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_text(cell, text: str, *, bold=False, size=8.0, color=BLACK, align=WD_ALIGN_PARAGRAPH.CENTER) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor.from_string(color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_margins(cell)


def remove_document_body(doc: Document) -> None:
    body = doc._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)


def set_keep_with_next(paragraph, value=True) -> None:
    paragraph.paragraph_format.keep_with_next = value


def configure_styles(doc: Document) -> None:
    styles = doc.styles
    if "Title" not in [style.name for style in styles]:
        styles.add_style("Title", WD_STYLE_TYPE.PARAGRAPH)
    if "Subtitle" not in [style.name for style in styles]:
        styles.add_style("Subtitle", WD_STYLE_TYPE.PARAGRAPH)
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    normal.paragraph_format.first_line_indent = Cm(1.25)
    normal.paragraph_format.line_spacing = 1.0
    normal.paragraph_format.space_after = Pt(4)
    for style_name in ("Title", "Subtitle", "Heading 1", "Heading 2"):
        style = styles[style_name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")
    styles["Title"].font.size = Pt(14)
    styles["Title"].font.bold = True
    styles["Title"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    styles["Title"].paragraph_format.space_after = Pt(8)
    styles["Subtitle"].font.size = Pt(12)
    styles["Subtitle"].font.bold = True
    styles["Subtitle"].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    styles["Subtitle"].paragraph_format.space_after = Pt(10)
    for name in ("Heading 1", "Heading 2"):
        style = styles[name]
        style.font.bold = True
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.page_break_before = False
    styles["Heading 1"].font.size = Pt(12)
    styles["Heading 1"].paragraph_format.space_before = Pt(8)
    styles["Heading 1"].paragraph_format.space_after = Pt(4)
    styles["Heading 2"].font.size = Pt(11)
    styles["Heading 2"].paragraph_format.space_before = Pt(5)
    styles["Heading 2"].paragraph_format.space_after = Pt(3)


def add_text(doc: Document, text: str, *, align=WD_ALIGN_PARAGRAPH.JUSTIFY, first_line=True, size=12.0, bold=False, italic=False, after=3) -> None:
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.first_line_indent = Cm(1.0) if first_line else Cm(0)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(after)
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(size)
    r.bold = bold
    r.italic = italic


def add_heading(doc: Document, text: str, level=1) -> None:
    p = doc.add_paragraph(style=f"Heading {level}")
    p.paragraph_format.left_indent = Cm(0)
    p.paragraph_format.first_line_indent = Cm(0)
    p.add_run(text)


def add_caption(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(9)
    r.bold = True


def add_source(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(1)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    r.font.name = "Arial"
    r.font.size = Pt(8)


def add_table(doc: Document, headers, rows, widths=None, font_size=7.3) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    for idx, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[idx], header, bold=True, size=font_size, color=WHITE)
        shade(table.rows[0].cells[idx], RED)
    for ridx, row in enumerate(rows):
        cells = table.add_row().cells
        for cidx, value in enumerate(row):
            set_cell_text(cells[cidx], str(value), size=font_size, align=WD_ALIGN_PARAGRAPH.LEFT if cidx == 0 else WD_ALIGN_PARAGRAPH.CENTER)
            if ridx % 2 == 1:
                shade(cells[cidx], LIGHT_GRAY)
    if widths:
        for row in table.rows:
            for idx, width in enumerate(widths):
                row.cells[idx].width = Cm(width)
    table.rows[0]._tr.get_or_add_trPr().append(OxmlElement("w:tblHeader"))
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(1)


def make_figure() -> None:
    labels = ["Base", "FT-FinQA", "FT-Failure", "FT-Híbrido"]
    finqa_1024 = [1.49, 10.45, 8.29, 10.61]
    failure_1024 = [12.52, 12.88, 96.63, 80.39]
    finqa_4096 = [1.82, 15.42, 2.32, 6.47]
    failure_4096 = [18.29, 11.55, 21.54, 12.03]
    canvas = Image.new("RGB", (1980, 650), "white")
    draw = ImageDraw.Draw(canvas)
    font_dir = Path("C:/Windows/Fonts")
    regular = ImageFont.truetype(str(font_dir / "arial.ttf"), 25)
    small = ImageFont.truetype(str(font_dir / "arial.ttf"), 21)
    bold = ImageFont.truetype(str(font_dir / "arialbd.ttf"), 29)
    panels = [
        (55, "Bateria A — 1.024 tokens", finqa_1024, failure_1024),
        (1010, "Bateria B — 4.096 tokens", finqa_4096, failure_4096),
    ]
    for left, title, finqa, failure in panels:
        top, bottom, right = 80, 515, left + 865
        draw.text((left + 430, 18), title, font=bold, fill="#111111", anchor="ma")
        for tick in range(0, 101, 20):
            y = bottom - (tick / 100) * (bottom - top)
            draw.line((left, y, right, y), fill="#D9D9D9", width=2)
            draw.text((left - 12, y), str(tick), font=small, fill="#333333", anchor="rm")
        draw.line((left, top, left, bottom), fill="#333333", width=3)
        draw.line((left, bottom, right, bottom), fill="#333333", width=3)
        group_w = (right - left) / len(labels)
        bar_w = 58
        for idx, label in enumerate(labels):
            center = left + group_w * (idx + 0.5)
            for offset, value, color in ((-bar_w / 2, finqa[idx], "#ED1C24"), (bar_w / 2, failure[idx], "#6E7781")):
                x0 = center + offset - bar_w / 2
                x1 = center + offset + bar_w / 2
                y0 = bottom - (value / 100) * (bottom - top)
                draw.rectangle((x0, y0, x1, bottom), fill=color)
                draw.text((center + offset, y0 - 8), f"{value:.1f}", font=small, fill="#111111", anchor="ms")
            draw.text((center, bottom + 18), label, font=small, fill="#222222", anchor="ma")
        draw.text((left, top - 7), "Acurácia (%)", font=small, fill="#222222", anchor="ls")
    legend_y = 610
    draw.rectangle((700, legend_y - 12, 728, legend_y + 16), fill="#ED1C24")
    draw.text((742, legend_y), "FinQA", font=small, fill="#222222", anchor="lm")
    draw.rectangle((990, legend_y - 12, 1018, legend_y + 16), fill="#6E7781")
    draw.text((1032, legend_y), "FailureSensorIQ", font=small, fill="#222222", anchor="lm")
    canvas.save(FIGURE, dpi=(220, 220))


def add_image_alt_text(doc: Document) -> None:
    descriptions = {
        "Picture 1": "Gráfico de barras comparando a acurácia dos quatro modelos no FinQA e no FailureSensorIQ nas baterias de 1.024 e 4.096 tokens.",
        "Imagem 9": "Logotipo do SENAI.",
        "Forma Livre 3": "Elemento gráfico decorativo cinza do template.",
        "docshape2": "Elemento gráfico decorativo vermelho com a numeração da página.",
    }
    parts = [doc.part]
    for section in doc.sections:
        parts.extend([section.header.part, section.footer.part])
    seen = set()
    for part in parts:
        if id(part) in seen:
            continue
        seen.add(id(part))
        for node in part.element.xpath(".//wp:docPr"):
            name = node.get("name", "")
            description = descriptions.get(name, "Elemento visual do artigo.")
            node.set("descr", description)
            node.set("title", description)


def add_author_block(doc: Document) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(2)
    authors = [
        ("Jéssica Franzon Cruz do Espírito Santo", "i"),
        ("Nicoli Felipe", "ii"),
        ("Vinicius de Jesus Silva", "iii"),
    ]
    for idx, (name, marker) in enumerate(authors):
        if idx:
            p.add_run("; ")
        r = p.add_run(name)
        r.font.name = "Arial"
        r.font.size = Pt(10.5)
        r.bold = True
        sup = p.add_run(marker)
        sup.font.name = "Arial"
        sup.font.size = Pt(7)
        sup.font.superscript = True
    affiliations = [
        "i Mestranda em Engenharia da Informação (UFABC) e docente do Centro Universitário SENAI-SP, Campus São Caetano do Sul – Centro.",
        "ii Graduanda em Ciência de Dados pelo Centro Universitário SENAI-SP, Campus São Caetano do Sul – Centro.",
        "iii Graduado em Ciência de Dados pelo Centro Universitário SENAI-SP, Campus São Caetano do Sul – Centro.",
    ]
    for line in affiliations:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(line)
        r.font.name = "Arial"
        r.font.size = Pt(8)


def build() -> None:
    make_figure()
    doc = Document(TEMPLATE)
    remove_document_body(doc)
    configure_styles(doc)

    section = doc.sections[0]
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.8)
    section.left_margin = Cm(2.3)
    section.right_margin = Cm(2.3)

    title = doc.add_paragraph(style="Title")
    title.add_run("FINE-TUNING MULTIDOMÍNIO COM QLORA EM LLMS PARA RACIOCÍNIO FINANCEIRO E DIAGNÓSTICO INDUSTRIAL")
    subtitle = doc.add_paragraph(style="Subtitle")
    subtitle.add_run("MULTIDOMAIN QLORA FINE-TUNING OF LLMS FOR FINANCIAL REASONING AND INDUSTRIAL DIAGNOSIS")
    add_author_block(doc)

    add_heading(doc, "RESUMO")
    add_text(doc, "Este estudo investiga a especialização do Qwen2.5-7B-Instruct para raciocínio financeiro e diagnóstico industrial por meio de QLoRA. Foram comparados o modelo base, dois ajustes especializados e um ajuste híbrido em duas baterias experimentais: a primeira com limite de 1.024 tokens e taxa de aprendizado de 2×10⁻⁴; a segunda com limite de 4.096 tokens e taxas distintas entre os ajustes. No FinQA, a maior acurácia numérica foi obtida pelo FT-FinQA de 4.096 tokens (15,42%). No FailureSensorIQ, reavaliado como tarefa multirrótulo, o FT-Failure de 1.024 tokens atingiu 96,63% de acurácia de correspondência exata e F1 macro de 0,989. O FT-Híbrido de 1.024 tokens apresentou 10,61% no FinQA e 80,39% no domínio industrial, constituindo o melhor compromisso dentro da bateria comparável. Os resultados mostram benefícios da especialização, mas não permitem atribuir diferenças da segunda bateria apenas à janela de contexto, pois taxa de aprendizado e microbatch também variaram.", size=9.2, first_line=False)
    add_text(doc, "Palavras-chave: modelos de linguagem; QLoRA; FinQA; diagnóstico de falhas; aprendizado multidomínio.", size=9.2, first_line=False, bold=True)

    add_heading(doc, "ABSTRACT")
    add_text(doc, "This study investigates QLoRA-based specialization of Qwen2.5-7B-Instruct for financial reasoning and industrial diagnosis. The base model, two domain-specialized models, and a hybrid model were compared in two experimental batteries: one limited to 1,024 tokens with a 2×10⁻⁴ learning rate, and an exploratory 4,096-token battery with model-dependent learning rates. FT-FinQA at 4,096 tokens achieved the highest FinQA numerical accuracy (15.42%). On FailureSensorIQ, correctly evaluated as a multilabel task, FT-Failure at 1,024 tokens reached 96.63% exact-set accuracy and 0.989 macro F1. The 1,024-token hybrid reached 10.61% on FinQA and 80.39% on the industrial benchmark, representing the best balance within the comparable battery. Because more than context length changed, the second battery is reported separately rather than as a controlled truncation ablation.", size=9.2, first_line=False)
    add_text(doc, "Keywords: large language models; QLoRA; FinQA; fault diagnosis; multidomain learning.", size=9.2, first_line=False, bold=True)

    add_heading(doc, "1 INTRODUÇÃO")
    add_text(doc, "Decisões industriais e financeiras são interdependentes: falhas elevam custos de manutenção, paradas reduzem produção e receita, problemas de qualidade geram retrabalho e desperdício, e investimentos em automação alteram produtividade, custo e retorno. A análise conjunta desses efeitos pode melhorar o planejamento e a priorização de recursos, sobretudo em ambientes com grande volume de dados operacionais e contábeis.")
    add_text(doc, "Embora modelos de linguagem de grande porte processem linguagem e números, versões generalistas ainda apresentam limitações em cálculos multietapas, interpretação de tabelas financeiras e diagnóstico técnico específico. Trabalhos sobre FinQA e manutenção baseada em condição evidenciam que cada domínio demanda conhecimento e padrões de resposta próprios (CHEN et al., 2021; JARDINE; LIN; BANJEVIC, 2006). Ainda é pouco explorada a especialização de um único modelo capaz de preservar capacidades nos dois domínios sem favorecer indevidamente apenas um deles.")
    add_text(doc, "O objetivo é avaliar o Qwen2.5-7B-Instruct, ajustado com QLoRA, em quatro configurações — Base, FT-FinQA, FT-Failure e FT-Híbrido — e em duas baterias com limites de 1.024 e 4.096 tokens. As contribuições são: comparação cruzada sob protocolos documentados; correção da avaliação multirrótulo do FailureSensorIQ; e análise do efeito conjunto de contexto, taxa de aprendizado e composição dos dados. Cenários sintéticos que relacionem ocorrências industriais a consequências financeiras não são reportados como resultado, por ainda não terem execução documentada.")

    add_heading(doc, "2 FUNDAMENTAÇÃO TEÓRICA")
    add_heading(doc, "2.1 LLMs para raciocínio financeiro e diagnóstico industrial", level=2)
    add_text(doc, "O FinQA combina textos, tabelas e perguntas numéricas que exigem localizar valores e executar programas matemáticos (CHEN et al., 2021). No domínio industrial, o FailureSensorIQ reúne questões de múltipla escolha, inclusive multirrótulo, sobre sensores, condições operacionais e modos de falha. Enquanto o primeiro enfatiza raciocínio quantitativo contextual, o segundo exige distinção entre alternativas técnicas semanticamente próximas. A avaliação conjunta permite observar especialização e transferência, mas não substitui um teste integrado de causalidade econômico-operacional.")
    add_heading(doc, "2.2 Fine-tuning eficiente com LoRA e QLoRA", level=2)
    add_text(doc, "LoRA introduz matrizes de baixa dimensão em módulos selecionados e mantém congelados os pesos principais (HU et al., 2021). QLoRA combina essa adaptação com quantização NF4 de 4 bits para reduzir memória durante o ajuste (DETTMERS et al., 2023). No Qwen2.5-7B-Instruct (YANG et al., 2024), essa estratégia viabilizou os experimentos em uma única GPU H100 de 80 GB. A taxa de aprendizado controla a magnitude de cada atualização: valores altos aceleram a adaptação, mas podem desestabilizar o treinamento ou apagar capacidades; valores baixos favorecem estabilidade, porém podem resultar em subajuste.")

    add_heading(doc, "3 METODOLOGIA")
    add_text(doc, "Foram utilizados o FinQA no domínio financeiro e o FailureSensorIQ no domínio industrial. Os registros foram normalizados para formato de instrução, tokenizados com o tokenizer do Qwen2.5 e separados em treino, validação e teste. Os conjuntos de teste contêm 617 e 831 exemplos, respectivamente. Uma verificação por texto exato não encontrou prompts idênticos entre treino e teste, reduzindo o risco de vazamento direto, embora não exclua similaridade semântica.")
    add_text(doc, "As quatro configurações foram derivadas do mesmo modelo base: sem ajuste, especializado em FinQA, especializado em FailureSensorIQ e híbrido. A Bateria A limita treinamento e inferência a 1.024 tokens e usa taxa de 2×10⁻⁴ em todos os ajustes. A Bateria B aplica 4.096 tokens, preserva 2×10⁻⁴ no FT-FinQA e usa 5×10⁻⁵ no FT-Failure e no FT-Híbrido. Como microbatch e taxa também mudaram, as baterias representam protocolos distintos, não uma ablação controlada exclusivamente do truncamento.")
    add_caption(doc, "Tabela 1 – Datasets, configurações e hiperparâmetros principais")
    add_table(
        doc,
        ["Item", "Bateria A", "Bateria B"],
        [
            ("Limite treino/inferência", "1.024 / 1.024", "4.096 / 4.096"),
            ("LR FT-FinQA", "2×10⁻⁴", "2×10⁻⁴"),
            ("LR FT-Failure/Híbrido", "2×10⁻⁴", "5×10⁻⁵"),
            ("Microbatch × acumulação", "4 × 8", "2 × 16"),
            ("Batch efetivo; épocas; seed", "32; 3; 42", "32; 3; 42"),
            ("QLoRA / LoRA", "NF4; r=8; α=16; dropout=0,1", "NF4; r=8; α=16; dropout=0,1"),
            ("Avaliação", "FinQA n=617; Failure n=831", "FinQA n=617; Failure n=831"),
        ],
        widths=[5.2, 5.1, 5.1],
        font_size=7.5,
    )
    add_source(doc, "Fonte: elaboração própria a partir dos manifestos de execução preservados.")
    add_text(doc, "Os ajustes foram executados com QLoRA/NF4, LoRA nos módulos de atenção e MLP e precisão mista. O FinQA foi medido por acurácia numérica. O FailureSensorIQ foi reprocessado a partir das predições salvas como tarefa multirrótulo: a métrica principal é a correspondência exata do conjunto de alternativas e a complementar é o F1 macro por rótulo. A geração foi determinística, e cada configuração foi comparada apenas dentro da bateria correspondente.")

    add_heading(doc, "4 RESULTADOS E DISCUSSÃO")
    add_text(doc, "A Tabela 2 consolida os resultados. Na Bateria A, o FT-Híbrido obteve a maior acurácia financeira (10,61%) por pequena margem sobre o FT-FinQA (10,45%) e preservou desempenho industrial elevado (80,39%). O FT-Failure foi superior no FailureSensorIQ (96,63%). Portanto, o híbrido apresenta o melhor equilíbrio na matriz comparável, mas não supera o especialista industrial em seu próprio domínio.")
    add_caption(doc, "Tabela 2 – Resultados dos quatro modelos nas duas baterias")
    add_table(
        doc,
        ["Bateria", "Modelo", "FinQA\nAcur. num.", "Failure\nAcur. conjunto", "Failure\nF1 macro"],
        [
            ("1.024", "Base", "1,49%", "12,52%", "0,318"),
            ("1.024", "FT-FinQA", "10,45%", "12,88%", "0,384"),
            ("1.024", "FT-Failure", "8,29%", "96,63%", "0,989"),
            ("1.024", "FT-Híbrido", "10,61%", "80,39%", "0,928"),
            ("4.096", "Base", "1,82%", "18,29%", "0,408"),
            ("4.096", "FT-FinQA", "15,42%", "11,55%", "0,336"),
            ("4.096", "FT-Failure", "2,32%", "21,54%", "0,535"),
            ("4.096", "FT-Híbrido", "6,47%", "12,03%", "0,449"),
        ],
        widths=[2.1, 3.6, 3.2, 3.7, 3.0],
        font_size=7.4,
    )
    add_source(doc, "Fonte: elaboração própria. FailureSensorIQ reavaliado em 14 set. 2026 a partir das predições persistidas.")
    add_text(doc, "Na Bateria B, o FT-FinQA alcançou o melhor resultado financeiro de todo o estudo (15,42%), consistente com a redução do truncamento de entradas longas. Em contraste, FT-Failure e FT-Híbrido perderam desempenho industrial. Isso reforça que uma janela maior não beneficia uniformemente os domínios: as entradas industriais já eram curtas, e a redução da taxa de aprendizado para 5×10⁻⁵ pode ter produzido adaptação insuficiente. Como os fatores variaram juntos, essa explicação é uma hipótese, não uma relação causal demonstrada.")
    add_caption(doc, "Figura 1 – Desempenho por domínio e bateria experimental")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(1)
    p.add_run().add_picture(str(FIGURE), width=Cm(15.7))
    add_source(doc, "Fonte: elaboração própria. Acurácia FinQA é numérica; acurácia FailureSensorIQ exige correspondência exata do conjunto de rótulos.")
    add_text(doc, "A correção multirrótulo altera a interpretação anterior. A métrica antiga selecionava apenas o primeiro rótulo, subestimava modelos com falhas de parsing e superestimava previsões parcialmente corretas. Com a regra de conjunto exato, o Base sobe de 0,12% para 12,52% na Bateria A, enquanto o FT-Híbrido passa de 96,15% para 80,39%. O F1 macro mostra que o híbrido ainda reconhece bem os rótulos (0,928), embora erre combinações completas em parte dos exemplos.")
    add_text(doc, "Os erros financeiros concentram-se em extração de valores, cálculo multietapas e respostas interrompidas; os industriais, em conjuntos incompletos de alternativas e confusões semânticas. A rodada de 4.096 tokens do FT-FinQA apresentou melhor checkpoint cedo no treinamento e piora posterior da perda de validação, sinal de instabilidade. Assim, o artigo não recomenda adotar um único truncamento por favorecer o FinQA: a escolha deve considerar a distribuição de comprimentos de cada domínio e ser testada com taxa de aprendizado controlada.")

    add_heading(doc, "5 CONCLUSÃO")
    add_text(doc, "O fine-tuning eficiente especializou o Qwen2.5-7B-Instruct nos dois domínios, mas os resultados dependem da configuração experimental. A Bateria A oferece a comparação mais limpa: o FT-Híbrido apresenta o melhor equilíbrio geral, enquanto o FT-Failure domina o diagnóstico industrial. A Bateria B elevou o desempenho do especialista financeiro, porém não sustenta a conclusão de que 4.096 tokens sejam universalmente superiores, pois outros hiperparâmetros também mudaram.")
    add_text(doc, "As limitações incluem uma única semente, dois benchmarks, protocolo de resposta curta, instabilidade do FT-FinQA de 4.096 tokens e ausência de avaliação integrada documentada. Trabalhos futuros devem executar uma ablação controlada de contexto e taxa de aprendizado, testar truncamento ou agrupamento por domínio, repetir o treinamento com múltiplas sementes e criar cenários que liguem falhas, produção, custos e impacto financeiro. Somente após essa etapa será possível avaliar diretamente a capacidade multidomínio pretendida.")

    add_heading(doc, "REFERÊNCIAS")
    references = [
        "CHEN, Z. et al. FinQA: A dataset of numerical reasoning over financial data. In: PROCEEDINGS OF EMNLP. Association for Computational Linguistics, 2021.",
        "DETTMERS, T. et al. QLoRA: Efficient finetuning of quantized LLMs. 2023.",
        "HU, E. J. et al. LoRA: Low-Rank Adaptation of Large Language Models. 2021.",
        "JARDINE, A. K. S.; LIN, D.; BANJEVIC, D. A review on machinery diagnostics and prognostics implementing condition-based maintenance. Mechanical Systems and Signal Processing, v. 20, n. 7, p. 1483–1510, 2006.",
        "YANG, A. et al. Qwen2.5 technical report. arXiv:2412.15115, 2024.",
    ]
    for ref in references:
        add_text(doc, ref, size=8.5, first_line=False, align=WD_ALIGN_PARAGRAPH.LEFT, after=2)
    add_heading(doc, "SOBRE O(S) AUTOR(ES)")
    bios = [
        ("i JÉSSICA FRANZON CRUZ DO ESPÍRITO SANTO", "Graduação em Ciência da Computação (UNIP, 2018–2021); pós-graduada em Gestão Educacional na Perspectiva Inclusiva (UFPEL, 2022) e em Psicopedagogia (FAM, 2024); mestranda em Engenharia da Informação (UFABC). Docente no Centro Universitário SENAI-SP, Campus São Caetano do Sul – Centro, no curso de Ciência de Dados. ORCID: 0000-0002-2812-3673."),
        ("ii NICOLI FELIPE", "Graduanda em Ciência de Dados (2025–2026) pelo Centro Universitário SENAI-SP, Campus São Caetano do Sul – Centro. ORCID não informado."),
        ("iii VINICIUS DE JESUS SILVA", "Graduado em Ciência de Dados (2024–2025) pelo Centro Universitário SENAI-SP, Campus São Caetano do Sul – Centro. ORCID: 0009-0002-8151-9439."),
    ]
    for name, bio in bios:
        add_text(doc, name, size=9.0, first_line=False, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT, after=1)
        add_text(doc, bio, size=8.7, first_line=False, after=4)

    # Prevent an accidental extra blank page created by a final empty paragraph.
    for p in doc.paragraphs:
        for r in p.runs:
            r.font.name = "Arial"
    doc.core_properties.title = "Fine-Tuning Multidomínio com QLoRA em LLMs"
    doc.core_properties.subject = "Raciocínio financeiro e diagnóstico industrial"
    doc.core_properties.author = "Jéssica Franzon Cruz do Espírito Santo; Nicoli Felipe; Vinicius de Jesus Silva"
    add_image_alt_text(doc)
    doc.save(OUTPUT)


if __name__ == "__main__":
    build()
