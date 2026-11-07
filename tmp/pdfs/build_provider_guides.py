from pathlib import Path
from html import escape
import json, re, zipfile
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/pdf/candidaturas_nicoli_2026-11-03'
OUT.mkdir(parents=True, exist_ok=True)
TMP = Path(__file__).resolve().parent
pdfmetrics.registerFont(TTFont('Arial', 'C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('Arial-Bold', 'C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial', boldItalic='Arial-Bold')
NAVY = colors.HexColor('#12344A')
TEAL = colors.HexColor('#087E8B')
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX', fontName='Arial-Bold', fontSize=25, leading=29, textColor=NAVY, spaceAfter=13))
styles.add(ParagraphStyle(name='SubX', fontName='Arial', fontSize=11, leading=16, textColor=TEAL, spaceAfter=16))
styles.add(ParagraphStyle(name='BodyX', fontName='Arial', fontSize=10.5, leading=15, spaceAfter=9, textColor=colors.HexColor('#243746')))
styles.add(ParagraphStyle(name='SmallX', fontName='Arial', fontSize=9, leading=13, spaceAfter=7, textColor=colors.HexColor('#526473')))
styles.add(ParagraphStyle(name='HeadX', fontName='Arial-Bold', fontSize=15, leading=19, textColor=NAVY, spaceBefore=10, spaceAfter=10, keepWithNext=True))
styles.add(ParagraphStyle(name='FieldX', fontName='Arial-Bold', fontSize=11.5, leading=15, textColor=TEAL, spaceBefore=10, spaceAfter=6, keepWithNext=True))
styles.add(ParagraphStyle(name='CopyX', fontName='Arial', fontSize=10.4, leading=15.2, spaceAfter=9, leftIndent=10, rightIndent=10, borderPadding=9, backColor=colors.HexColor('#F0F6F8')))
styles.add(ParagraphStyle(name='NoticeX', fontName='Arial', fontSize=10, leading=14, spaceAfter=12, borderPadding=10, backColor=colors.HexColor('#FFF2D9'), textColor=colors.HexColor('#654400')))

def p(s, sty='BodyX'):
    return Paragraph(escape(s).replace('\n','<br/>'), styles[sty])

def link(title,url):
    return Paragraph(f'<link href="{escape(url, quote=True)}" color="#087E8B"><u>{escape(title)}</u></link>', styles['BodyX'])

def field(title, value, note=None):
    a=[p(title,'FieldX')]
    if note: a.append(p(note,'SmallX'))
    for part in value.split('\n\n'): a.append(p(part,'CopyX'))
    return a

def page(title, intro=None):
    a=[PageBreak(),p(title,'HeadX')]
    if intro: a.append(p(intro))
    return a

def footer(c, doc):
    w,h=doc.pagesize
    c.setStrokeColor(colors.HexColor('#D8E4E9')); c.line(42,43,w-42,43)
    c.setFont('Arial',8); c.setFillColor(colors.HexColor('#526473'))
    c.drawString(42,29,'Nicoli Felipe | Guia de candidatura | 03/11/2026')
    c.drawRightString(w-42,29,f'{doc.page}')

DOCS=[]
def build(slug, provider, status, sources, body, scope):
    story=[p(provider,'TitleX'),p('Guia de preenchimento para Nicoli Felipe','SubX'),p(status,'NoticeX'),p(scope)]
    story += [p('Como usar','HeadX'),p('As orientações estão em português. Copie apenas os blocos de resposta em inglês para o campo correspondente. Os campos marcados "NICOLI PREENCHE" dependem dos dados dela. Nenhuma candidatura foi enviada nesta preparação.')]
    story += [p('Dados comuns','HeadX')]
    for k,v in [('Candidata','Nicoli Felipe'),('Instituição','SENAI São Caetano do Sul - Cyber e IA'),('Curso','Ciências de Dados'),('Orientadora','Jéssica Franzon Cruz do Espírito Santo - coordenadora do curso de Ciências de Dados e orientadora do projeto'),('Prazo','2 meses após a disponibilização dos recursos')]:
        story.append(p(f'{k}: {v}'))
    story += body
    story += [p('Fontes e alcance da conferência','HeadX')]
    for name,url in sources: story.append(link(name,url))
    story.append(p('Conferência em 03/11/2026. Os sites podem alterar campos e critérios. O documento distingue campos observados de textos de apoio. Não é comprovante de elegibilidade, concessão ou submissão.','SmallX'))
    path=OUT/f'{slug}.pdf'
    SimpleDocTemplate(str(path),pagesize=(595.28,841.89),rightMargin=44,leftMargin=44,topMargin=45,bottomMargin=58,title=f'{provider} - guia de candidatura - Nicoli Felipe',author='Equipe de pesquisa',pageCompression=1).build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(path)
    text='\n'.join(pg.extract_text() or '' for pg in reader.pages)
    assert 'Nicoli Felipe' in text and len(text)>500
    assert '\ufffd' not in text
    DOCS.append({'file':str(path),'provider':provider,'pages':len(reader.pages),'characters':len(text),'status':status})

INSTITUTION='SENAI São Caetano do Sul - Cyber e IA'
TEAM='I am Nicoli Felipe, an undergraduate Data Science student at SENAI São Caetano do Sul - Cyber e IA, Brazil. This project is supervised by Jéssica Franzon Cruz do Espírito Santo, coordinator of the Data Science course and project advisor, and includes Vinicius de Jesus Silva as a research collaborator and graduate of the institution.'
QUESTION='How do OpenAI API models compare with Qwen2.5-7B-Instruct and its financial, industrial, and hybrid fine-tuned variants on analytical questions over synthetic financial and industrial databases and an integrated data warehouse? We will examine answer correctness, numerical accuracy, support from the available evidence, and the trade-offs between accuracy, latency, and inference cost. A further question is whether domain specialization transfers to database-grounded tasks involving both domains, and where models make unsupported inferences, including treating missing observations as zero or inferring financial consequences of an industrial event without sufficient evidence.'
DESIGN='This undergraduate research project builds on Qwen2.5-7B-Instruct variants previously fine-tuned with QLoRA on FinQA, FailureSensorIQ, and a combination of both datasets. We will compare the base and fine-tuned models with selected OpenAI API models on a versioned set of financial, industrial, and cross-domain analytical questions using fictitious databases and an integrated data warehouse.\n\nBefore scoring, each case will receive human review of the question, data semantics, reference query, calculation, numerical tolerance, and acceptable conclusions. Reference answers will remain separate from model inputs. Fixed-evidence tasks and tool-assisted retrieval will be evaluated as separate conditions. Within each condition, questions, evidence access, and execution limits will be made comparable. Model identifiers, prompts, parameters, evidence versions, tool calls, failures, token usage, and latency will be recorded.\n\nScoring will distinguish evidence retrieval, numerical calculation, and the validity of the conclusion. Human review will assess responses against approved references; an LLM judge will not be the sole authority. Failed or incomplete runs will remain visible. A pilot will calibrate token consumption, feasible model choices, and repetitions within the requested USD 1,000 API-credit ceiling. OpenAI credits will support API inference only; GPU compute for Qwen will be sought separately. The formal comparative evaluation remains pending.'
OUTCOMES='The study is intended to characterize where OpenAI models succeed or fail on financial and industrial questions grounded in structured evidence. Expected outputs include comparisons of answer correctness, numerical accuracy, unsupported conclusions, latency, and cost per evaluated question, with fixed-evidence and tool-assisted conditions reported separately. An error analysis will distinguish calculation mistakes, retrieval failures, misinterpretation of units or coverage, and unsupported causal or cross-domain claims.\n\nWe plan to produce a reproducible evaluation report documenting prompts, model configurations, case provenance, scoring criteria, and limitations. Research materials will be shared where licensing and permissions allow. Results from fictitious databases will be described as controlled benchmark evidence; they will not establish performance in a real company or validate financial or maintenance decisions. We do not assume that either OpenAI models or specialized models will be superior.'
FINETUNE='Not applicable. This proposal requests API credits for inference and comparative evaluation of publicly available OpenAI models. It does not request access to GPT-4 fine-tuning or GPT-3.5 fine-tuning. The specialized models in our comparison are Qwen2.5-7B-Instruct variants already fine-tuned separately using QLoRA with financial and industrial datasets. The role of the OpenAI API is to provide comparison models under a documented evaluation protocol, with no additional training of OpenAI models proposed.'
PAST='Our team prepared the manuscript "Fine-tuning multidomínio com QLoRA para raciocínio financeiro e análise de falhas industriais", by Nicoli Felipe, Vinicius de Jesus Silva, and Jéssica Franzon Cruz do Espírito Santo. It has been submitted to a conference; acceptance is not confirmed. It compares Qwen2.5-7B-Instruct with financial, industrial, and hybrid QLoRA adaptations using FinQA and FailureSensorIQ. Findings are limited to the evaluated protocols; differences between experimental settings cannot be attributed solely to context length because other hyperparameters also varied. The proposed database-grounded comparison is a subsequent phase. A local workbench and exploratory inference integrations have been developed, but successful technical runs do not establish scientific validity of the new comparison.'
ROADMAP='The project is planned for two months after resources become available. Weeks 1-2: freeze the pilot cases and evidence versions, verify reference calculations with human reviewers, and record measured inference resource use. Weeks 3-6: run the planned comparisons under documented conditions, retaining traces and recording failures. Weeks 7-8: complete human review of eligible model responses, analyze errors and resource use, and prepare a report with reproducibility materials where permitted. Only responses with the required evidence and review will receive scientific scores; incomplete runs will be reported separately.'
GPU='We seek GPU compute to serve Qwen2.5-7B-Instruct and its existing financial, industrial, and hybrid QLoRA adapters for controlled evaluation. The scope is inference and evaluation, not training a foundation model. A single GPU will be used at a time, with configurations evaluated sequentially. We will record GPU-active time, token throughput, latency, failures, and configuration details. Database preparation and human review do not require continuously running GPU instances. Compute will be stopped between sessions and results exported for analysis.'
ESTIMATE='Proposed planning allocation: 100 single-GPU hours across two months, with 10 hours for deployment and pilot measurements, 70 hours for comparative inference, and 20 hours reserved for documented reruns and technical failures. This is a planning estimate, not a measured workload. The pilot will determine achievable case and repetition counts, and we will reduce scope to stay within the granted allocation. No continuous two-month GPU reservation is requested.'
GENERAL='We propose a two-month evaluation of evidence-grounded language-model reasoning over fictitious financial and industrial databases and an integrated data warehouse. The study compares a Qwen2.5-7B-Instruct base model, existing domain-specific and hybrid QLoRA adapters, and selected API models where separately supported. Questions, reference calculations, and evidence will be versioned and reviewed by humans. We will assess numerical correctness, evidential support, latency, and inference cost, distinguishing fixed-evidence and tool-assisted conditions. The formal scientific comparison is pending; earlier exploratory runs are not treated as validated results.'

# OPENAI: full form read in the user's saved draft, without editing it.
b=page('1. Identificação e acesso')
b += [p('Nicoli deve abrir sua própria candidatura. O rascunho anterior permanece na conta de Vinicius e não foi alterado. Os textos abaixo já apresentam Nicoli como candidata.','NoticeX')]
for title,value,note in [
('First Name','Nicoli',None),('Last Name','Felipe',None),
('Institutional Email Address','NICOLI PREENCHE: seu e-mail institucional.',None),
('Email address associated with your OpenAI API account','NICOLI PREENCHE: e-mail da sua conta na plataforma de API.', 'Pode ser diferente do institucional. Não informar senha ou chave de API.'),
('Institution or organization',INSTITUTION,None),
('Professional profiles','NICOLI PREENCHE: URL do seu LinkedIn, Google Scholar, GitHub ou perfil institucional.','Rótulo resumido do campo de links profissionais.'),
('Country','Brazil','Confirmar que corresponde ao país da candidata.'),
('Educational Stage','Undergraduate Studies','Corresponde à graduação em andamento de Nicoli.'),
('Gender Identity','NICOLI PREENCHE: selecionar a opção que corresponde à sua identidade.','Não foi inferida a partir do nome.'),
('Research Areas','Model exploration','Selecionar a categoria; não copiar este texto em outro campo.')]: b += field(title,value,note)
b += page('2. Pergunta e desenho da pesquisa','Project Description é o agrupamento dos campos abaixo, não um campo adicional observado para digitação.')
b += field('Research Question',QUESTION,f'{len(QUESTION)} caracteres. Limite observado: 500 a 1.500 caracteres.')
b += field('Research Design',DESIGN,'Texto proposto para revisão final da equipe. Sem limite de caracteres exibido na inspeção.')
b += page('3. Resultados esperados e fine-tuning')
b += field('Expected outcomes',OUTCOMES,'Campo sobre contribuição ao entendimento dos modelos e seus impactos.')
b += field('Justificativa de GPT-4 fine-tuning',FINETUNE,f'Campo legado que menciona GPT-4 e GPT-3.5. Responder que não se aplica; não declarar necessidade de treinamento OpenAI. {len(FINETUNE)} caracteres; limite observado: 500 a 1.500.')
b += page('4. Prazo, orçamento e colaboradores')
b += field('Anticipated timeline','2 months after the API credits become available.','Campo de prazo. Os dois meses não são prazo de análise da candidatura.')
b += field('Anticipated budget in API credits (USD)','1000','Valor definido pela equipe. É exclusivamente para créditos OpenAI, não para GPU ou outros provedores.')
b += field('Organization ID','NICOLI PREENCHE: org-ID da organização da plataforma OpenAI que receberá os créditos.','Não é CNPJ, código da faculdade, senha ou chave de API. Conferir a organização de destino na conta de API.')
b += [link('Abrir configurações de organização da API','https://platform.openai.com/account/organization')]
b += field('Names and emails of additional collaborators','Vinicius de Jesus Silva - NICOLI PREENCHE: e-mail associado à conta de API do colaborador.\nJéssica Franzon Cruz do Espírito Santo - NICOLI PREENCHE: e-mail associado à conta de API da colaboradora.','O formulário informa que os colaboradores listados devem ter contas de API. Incluir apenas quem satisfaz essa condição; não inventar e-mails.')
b += page('5. Histórico e comentários')
b += field('Past research',PAST,'Rótulo resumido da pergunta sobre trabalhos anteriores. Se houver link público autorizado do trabalho, acrescentá-lo; não usar links privados do chat.')
b += field('Any other comments',TEAM+' The requested USD 1,000 will support API inference during a two-month study. GPU hosting for the independently fine-tuned models is a separate resource requirement. The proposed evaluation will use fictitious research data, human-reviewed references, and explicit limitations.')
b += [p('Antes do envio','HeadX'),p('Revisar os textos, completar os campos pessoais e de conta, conferir o destino dos créditos e os colaboradores. O formulário completo foi consultado, mas esta preparação não valida regras adicionais da conta da Nicoli nem envia a candidatura.')]
assert 500<=len(QUESTION)<=1500 and 500<=len(FINETUNE)<=1500
build('01_OpenAI','OpenAI | Researcher Access','TEXTOS COMPLETOS PARA REVISÃO. Faltam apenas os campos pessoais e de conta indicados.', [('Programa e nova candidatura','https://openai.smapply.org/prog/openai_researcher_access_program/')],b,'Formulário completo conferido no portal. Textos ajustados à candidata Nicoli; valor solicitado: US$ 1.000 em API. Não usar o link privado do rascunho de Vinicius como candidatura da Nicoli.')

# LAMBDA: all 14 questions traversed via ordinary next-question navigation.
b=page('1. Contato e referências')
b+=field('1. Contact Information','First name: Nicoli\nLast name: Felipe\nEmail: NICOLI PREENCHE\nPhone number: NICOLI PREENCHE, se desejar\nCompany: SENAI São Caetano do Sul - Cyber e IA','Nome, sobrenome e e-mail obrigatórios. Telefone e Company não estavam marcados como obrigatórios.')
b+=field('2. Related Publications (if any)','NICOLI PREENCHE: link público autorizado do artigo, página do projeto, demonstração ou protótipo, se houver.','Opcional. Este campo pede links próprios; não é necessário inventar uma publicação. O manuscrito está submetido, sem aceite confirmado. Pode ficar vazio se não houver material público.')
b+=field('3. Research Problem','Language models may produce fluent but numerically incorrect or insufficiently supported answers when reasoning across financial and industrial records. We will test whether specialization with financial, industrial, or hybrid QLoRA adapters transfers to questions grounded in structured databases. The study uses fictitious data and an integrated data warehouse, comparing the base Qwen2.5-7B-Instruct model, its adapters, and separately supported API models. Success means a reproducible, human-reviewed comparison that identifies errors and resource trade-offs, rather than assuming that a particular model will win. The study will take two months after compute becomes available.','Obrigatório. Explica problema, importância e critério de sucesso.')
b+=page('2. Relevância, desafios e GPU')
b+=field('4. Relevance and Novelty','QLoRA (Dettmers et al., 2023) provides a memory-efficient method for adapting language models, while FinQA (Chen et al., 2021) studies numerical reasoning over financial evidence. Our prior work applies QLoRA to financial, industrial, and combined training data. This next phase examines whether that specialization transfers to versioned database-grounded tasks, including cross-domain questions where missing observations, coverage, units, and unsupported causal conclusions matter. The intended contribution is a controlled comparison that separates evidence retrieval, numerical calculation, and conclusion validity, with human-reviewed references and explicit resource measurements. We do not claim a new foundation-model architecture or that this is the first study of this kind.','Obrigatório. Referências primárias estão ao final do PDF.')
b+=field('5. Challenges','Technical challenges include context-window limits, numerical reasoning errors, inconsistent retrieval, and differences between API and self-hosted inference capabilities. We will report fixed-evidence and tool-assisted conditions separately, preserve prompts and evidence versions, and record failures instead of dropping them. Non-technical challenges include the time needed for human review, resource availability, and permissions to share materials. A pilot will calibrate workload size and repetitions. Findings from fictitious data will not be presented as validation of real-company decisions.','Obrigatório.')
b+=field('6. GPU Compute Needs','100','OBRIGATÓRIO, CAMPO NUMÉRICO. Unidade indicada pelo formulário: horas de H100. Valor sugerido para revisão da equipe, não medido nem previamente aprovado. Confirmar ou ajustar antes de enviar.')
b+=[p('Justificativa da estimativa - apoio à revisão','HeadX'),p(ESTIMATE),p('O formulário mostra um campo numérico, embora a descrição também pergunte como o recurso ajuda a pesquisa. Não colar prosa nesse campo. A finalidade está contemplada nas respostas científicas e no roadmap. Não converter automaticamente este número em US$ 1.000 ou em duas máquinas simultâneas.','NoticeX')]
b+=page('3. Resultados anteriores e perfis')
b+=field('7. Notable Achievements',PAST,'Obrigatório. Descreve trabalho feito sem afirmar publicação aceita ou avaliação científica já concluída.')
for n,title in [(8,'Github Profile'),(9,'Google Scholar Profile'),(10,'Social Media Profile')]: b+=field(f'{n}. {title}','NICOLI PREENCHE: URL do seu perfil, se aplicável.','Opcional. Pode ficar vazio se não houver perfil correspondente.')
b+=field('11. Partnerships and Support','NICOLI PREENCHE apenas se houver colaboração anterior com outra organização que queira declarar.','Opcional. Não declarar provedores prospectados como parceiros ou financiadores já confirmados.')
b+=page('4. Cronograma, publicação e blog')
b+=field('12. Roadmap',ROADMAP,'Obrigatório. Cronograma proposto, organizado dentro dos dois meses informados.')
b+=field('13. Publishing Plan','We plan to prepare a research manuscript or technical report describing the protocol, comparative results, errors, and limitations. Reproducibility materials such as evaluation code, prompts, configuration details, and synthetic-data documentation will be shared where institutional permissions and licenses allow. We will distinguish exploratory engineering results from human-reviewed scientific results. We do not promise acceptance at a conference or unrestricted release of all model weights or datasets.','Obrigatório. Plano de divulgação, sem promessa de aceite ou liberação irrestrita.')
b+=field('14. Willingness to co-write a blog for Lambda','Yes','Obrigatório. Resposta autorizada por Vinicius nesta conversa em 03/11/2026; Nicoli deve revisar antes de enviar. Trata-se de post para o blog da Lambda, não de coautoria automática no artigo científico.')
b+=[p('Pendências para enviar','HeadX'),p('Preencher contato e revisar a proposta de 100 horas de H100. Os perfis e trabalhos públicos são opcionais. Todas as 14 perguntas foram consultadas sem inserir dados nem clicar em Submit answers.')]
build('02_Lambda','Lambda | Research Grant','14 PERGUNTAS CONFERIDAS. Textos prontos; dados de contato e revisão das horas de GPU pendentes.', [('Programa','https://lambda.ai/research'),('Formulário','https://form.typeform.com/to/Wn8YWMIj'),('QLoRA - Dettmers et al. (2023)','https://arxiv.org/abs/2305.14314'),('FinQA - Chen et al. (2021)','https://aclanthology.org/2021.emnlp-main.300/')],b,'O formulário foi percorrido até a pergunta 14 usando a navegação normal, sem preencher respostas. A tela inicial anuncia até US$ 5.000; isso não é concessão garantida nem valor solicitado por esta proposta.')

# RUNPOD: only page 1 accessible with required contacts missing.
b=page('1. Campos confirmados - etapa 1 de 6')
for title,val,note in [
('Runpod Account Email','NICOLI PREENCHE: e-mail da conta RunPod que utilizará.','Sem indicação de obrigatoriedade na primeira etapa; não criar conta apenas para preencher este PDF.'),
('First Name','Nicoli','Obrigatório.'),('Last Name','Felipe','Obrigatório.'),
('Email','NICOLI PREENCHE: e-mail para contato.','Obrigatório.'),('Phone Number','NICOLI PREENCHE: telefone com código do país.','Obrigatório.')]:b+=field(title,val,note)
b += [p('As etapas 2 a 6 não foram expostas: o botão Next estava desabilitado enquanto faltavam os contatos obrigatórios. Não foram usados dados fictícios. Os blocos seguintes são textos de apoio, não nomes de campos confirmados.','NoticeX')]
b+=page('2. Textos de apoio para as próximas etapas','Usar cada bloco apenas se aparecer uma pergunta correspondente. Se houver campos com escolhas fechadas ou limites diferentes, a redação deverá ser adaptada.')
b+=field('Apresentação da equipe - texto de apoio',TEAM)
b+=field('Descrição do projeto - texto de apoio',GENERAL)
b+=field('Finalidade do apoio em nuvem - texto de apoio',GPU+' We would like to be considered for sponsored academic compute credits for this evaluation. We are not requesting a paid deployment through this application.')
b+=page('3. Recursos e prazo - proposta para revisão')
b+=field('Plano de recursos - texto de apoio',ESTIMATE,'Proposta estimativa, não um campo obrigatório confirmado. Não informar 100 horas como consumo medido. GPU e armazenamento exatos deverão corresponder à configuração aprovada e à oferta do provedor.')
b+=field('Prazo e entregas - texto de apoio',ROADMAP)
b+=[p('Pendências e condições','HeadX'),p('Nicoli deve completar os contatos para visualizar as próximas etapas. Ainda podem aparecer exigências não cobertas por este guia. A rota acadêmica recebe solicitações de estudantes caso a caso e não garante créditos gratuitos. Se a resposta for uma oferta comercial, será necessária uma decisão separada da equipe.')]
build('03_RunPod','RunPod | Academic Research','GUIA PARCIAL DO FORMULÁRIO + TEXTOS DE APOIO. Etapas 2 a 6 dependem dos contatos da candidata.', [('Programa e formulário Get in touch','https://www.runpod.io/academic-research')],b,'A primeira etapa foi conferida no formulário HubSpot da página oficial. O documento permite preparar a proposta, mas não afirma que todos os campos de envio já foram mapeados.')

# NEBIUS
b=page('1. Candidata e elegibilidade')
b+=[p('A lista pública contempla pós-graduandos, doutorandos, pós-doutorandos, docentes e pesquisadores. O formulário também oferece Other. Não foi confirmada a aceitação de graduação por si só; a opção Other não prova elegibilidade.','NoticeX'),p('O texto-base mantém Nicoli como candidata, conforme decisão da equipe. Se o programa exigir uma docente responsável, Jéssica deverá concordar e a identificação deverá ser reescrita para ela. Não selecionar Faculty para Nicoli nem trocar a candidata silenciosamente.')]
for title,val,note in [
('First name','Nicoli','Obrigatório, se Nicoli for a candidata elegível.'),('Last name','Felipe','Obrigatório.'),
('Email','NICOLI PREENCHE: e-mail da candidata.','Obrigatório.'),('Country/region','Brazil','Obrigatório; confirmar o país da candidata.'),
('Academic rank','Other','Categoria mais transparente para graduação entre as opções vistas. Não confirma elegibilidade. Opções vistas: Faculty, PhD Student, Postdoctoral researcher, Postgraduate student, Other.'),
('Organization name',INSTITUTION,'Obrigatório.'),
('Google Scholar / institutional faculty profile','NICOLI PREENCHE: link do perfil exigido do titular da candidatura.','Obrigatório. Não substituir pelo perfil de Jéssica mantendo Nicoli como titular, nem afirmar que LinkedIn satisfaz este campo.')]:b+=field(title,val,note)
b+=[p('Next estava desabilitado sem os dados obrigatórios. As etapas 2 e 3 não foram consultadas. Os textos seguintes respondem aos critérios públicos do programa; seus títulos não são rótulos de campos confirmados.','NoticeX')]
b+=page('2. Proposta de pesquisa - textos de apoio')
b+=field('Equipe e vínculo',TEAM)
b+=field('Problema e contribuição',GENERAL+' The project focuses on the reliability of evidence-grounded analytical reasoning and on the evaluation of domain-adapted models, rather than on deploying a commercial product.')
b+=field('Viabilidade e experiência anterior',PAST)
b+=page('3. Plano de utilização - estimativa para revisão')
b+=field('Uso proposto da infraestrutura','We request GPU compute to serve Qwen2.5-7B-Instruct and its existing QLoRA adapters for inference and evaluation. Configurations will run sequentially on one GPU at a time. We will log active GPU hours, throughput, latency, and failures, and stop compute between sessions. API-model comparisons will use separately funded resources; the same workload will not be presented as requiring duplicate allocations.')
b+=field('Dimensionamento inicial',ESTIMATE,'Plano quantitativo sugerido. Validar antes do envio. Não converter em horas equivalentes entre GPUs sem medir throughput; a configuração final depende de memória, contexto e oferta disponível.')
b+=field('Cronograma','Two months after resources become available: weeks 1-2 for human-reviewed reference checks and a measured pilot; weeks 3-6 for comparative inference with versioned evidence and traces; weeks 7-8 for response review, error analysis, and reporting. Only reviewed responses with the required evidence will receive scientific scores; incomplete runs will be reported separately.')
b+=field('Resultados e compartilhamento','We intend to report numerical accuracy, evidence support, failure modes, latency, and resource use under documented conditions. Evaluation code and permitted research materials are intended for release where licensing and institutional permissions allow. The main output will be a research report or manuscript with clear limitations; no publication acceptance or real-world deployment performance is promised.')
b+=[p('Decisões que continuam pendentes','HeadX'),p('Confirmar a elegibilidade da titular e completar seu perfil acadêmico. A Nebius inclui divulgação conjunta entre os critérios; a autorização dada para o blog da Lambda não foi estendida automaticamente à Nebius. A equipe deve revisar o compromisso específico apresentado. As prioridades mencionam colaboração científica quando apropriada; não há promessa de coautoria em troca de créditos neste texto.')]
build('04_Nebius','Nebius | Research Grants','GUIA PARCIAL. Elegibilidade da titular, perfil acadêmico e etapas 2 a 3 ainda pendentes.', [('Programa e formulário','https://nebius.com/nebius-research-grants'),('Prioridades oficiais','https://nebius.science/stories/grant-priorities')],b,'A etapa 1 e todas as opções do campo Academic rank foram conferidas. O plano de recursos abaixo é uma proposta de redação estimativa para revisão, não um consumo já medido.')

# ANTHROPIC
b=page('1. Campos confirmados - página 1 de 3')
b+=field('Email','NICOLI PREENCHE: e-mail de contato, preferencialmente acadêmico.','Obrigatório. O formulário recomenda credenciais e e-mails acadêmicos quando possível.')
b+=field('Which program are you applying to?','Standard AI for Science program','Obrigatório; única opção visível na primeira página.')
b+=[p('As páginas 2 e 3 exigem o preenchimento da primeira página para avançar. Como não temos o e-mail de Nicoli, seus campos não foram verificados. Não inserir o e-mail de Vinicius apenas para desbloquear uma candidatura em nome dela.','NoticeX')]
b+=page('2. Textos científicos de apoio','Estes blocos não são um mapeamento de campos das páginas 2 e 3. Usar somente quando o formulário apresentar a pergunta correspondente e após revisar o enquadramento no programa.')
b+=field('Equipe e instituição',TEAM)
b+=field('Proposta de uso de Claude','We would use Claude API credits as one comparison arm in a two-month study of evidence-grounded analytical reasoning over fictitious financial and industrial databases. We will compare API-based inference with Qwen2.5-7B-Instruct and its existing financial, industrial, and hybrid QLoRA adapters. Versioned cases, reference queries, numerical calculations, and acceptable conclusions will receive human review. The study examines numerical accuracy, evidence support, unsupported cross-domain claims, latency, and cost. Fixed-evidence tasks and tool-assisted retrieval will be reported separately. We do not assume Claude or the specialized models will be superior.')
b+=field('Resultado esperado','The intended output is a reproducible comparative report documenting error types, model and prompt configurations, evidence provenance, and resource use. Human review will distinguish retrieval errors, calculation errors, and unsupported conclusions. Findings on fictitious data will be presented as controlled evidence, not as validation of real financial or maintenance decisions. Permitted materials will be shared subject to licensing and institutional approval.')
b+=page('3. Prazo e limites da candidatura')
b+=field('Prazo proposto',ROADMAP)
b+=field('Histórico relacionado',PAST)
b+=[p('Enquadramento ainda não confirmado','HeadX'),p('O formulário descreve apoio a ciências naturais e matemática, com destaque para biologia e ciências da vida. O projeto aqui descrito é uma avaliação de modelos com dados financeiros e industriais. Não basta renomeá-lo como pesquisa em matemática ou biologia para estabelecer aderência. A equipe deverá verificar esse enquadramento antes de enviar.'),p('Orçamento','HeadX'),p('Não há um valor de créditos Anthropic definido pela equipe, e o campo de orçamento não foi observado. Os US$ 1.000 informados são exclusivos da OpenAI. Se aparecer uma pergunta quantitativa nas próximas páginas, preparar uma estimativa específica para Claude.')]
build('05_Anthropic','Anthropic | AI for Science','GUIA PARCIAL E CONDICIONAL. Enquadramento científico e páginas 2 a 3 ainda não confirmados.', [('Formulário oficial','https://docs.google.com/forms/d/e/1FAIpQLSfwDGfVg2lHJ0cc0oF_ilEnjvr_r4_paYi7VLlr5cLNXASdvA/viewform')],b,'A primeira página foi conferida. Os textos de apoio preservam o projeto real; não afirmam elegibilidade nem prometem uma descoberta em ciências naturais que não faz parte da pesquisa.')

# MODAL
b=page('1. Formulário atual: lista de interesse')
b+=field('Name','Nicoli Felipe','Obrigatório.')
b+=field('Academic email','NICOLI PREENCHE: e-mail acadêmico.','Obrigatório.')
b+=[p('O que este envio significa','HeadX'),p('O formulário informa que o programa geral de concessão de créditos não está em funcionamento e serve para receber avisos. Cita oportunidades específicas relacionadas a ICLR, ICML e NeurIPS, sem demonstrar que o artigo da equipe se enquadra. Não há campo de proposta, orçamento ou cronograma nessa lista.'),p('Não é necessário enviar um texto científico','HeadX'),p('Não colar a proposta OpenAI em um campo de nome ou e-mail. Não apresentar o cadastro como pedido de créditos aprovado ou bolsa solicitada. Uma candidatura científica futura dependerá de edital e formulário próprios.'),p('Contato informado pelo formulário','HeadX'),link('Dúvidas sobre bolsas: academics@modal.com','mailto:academics@modal.com'),p('O contato é apenas uma referência. Nenhuma mensagem foi enviada.')]
build('06_Modal','Modal | Lista de interesse','SEM PROGRAMA GERAL DE BOLSAS ABERTO NO FORMULÁRIO CONSULTADO. Apenas dois campos cadastrais.', [('Modal for Academics','https://modal.com/academics'),('Lista de interesse','https://embed.fillout.com/t/2czD8LNaiJus')],b,'Este PDF cobre integralmente o pequeno formulário atualmente disponível. Ele não é uma proposta de concessão de créditos.')

# HF and GOOGLE: informational status sheets, not fabricated grant forms.
b=page('1. Situação da rota discutida')
b+=[p('Não há formulário de concessão confirmado para esta candidatura','HeadX'),p('A rota verificada foi Spaces ZeroGPU, infraestrutura compartilhada para aplicações e demonstrações. Isso não estabelece um programa de créditos de nuvem dedicado à avaliação completa da equipe. Não foi confirmado um formulário de apoio específico ao qual Nicoli deva enviar o texto científico.'),p('O que pode ser preparado agora','HeadX'),p('A descrição abaixo pode ser reutilizada em uma página pública do projeto ou em uma futura solicitação de apoio, caso a equipe escolha essa rota. Não corresponde a um campo obrigatório confirmado e não exige publicar o projeto agora.')]
b+=field('Descrição curta - apoio para uso futuro','This research project studies numerical reasoning and evidence-grounded analysis with Qwen2.5-7B-Instruct and financial, industrial, and hybrid QLoRA adapters. It uses fictitious financial and industrial databases and an integrated data warehouse. The aim is to compare correctness, evidence support, latency, and resource use under a human-reviewed evaluation protocol. A demonstration, if published, will be clearly distinguished from scientifically validated benchmark results.')
b+=[p('Pendência real','HeadX'),p('Escolher um programa de apoio com condições e canal de candidatura identificados, caso o objetivo continue sendo obter recursos para a avaliação. Não há, neste guia, um pedido a enviar ou valor de bolsa confirmado. Uma demonstração pública também exige decidir materiais e licenças que podem ser divulgados.')]
build('07_Hugging_Face','Hugging Face | Situação da rota','INFORMATIVO. Nenhum formulário de concessão específico confirmado.', [('Documentação oficial de Spaces ZeroGPU','https://huggingface.co/docs/hub/en/spaces-zerogpu')],b,'Incluído para que a lista de provedores não confunda uma alternativa de demonstração com uma candidatura pronta para créditos ou GPU dedicada.')

b=page('1. Gemini API e a camada gratuita')
b+=[p('A rota discutida não é uma bolsa','HeadX'),p('A página oficial consultada descreve uma camada gratuita com acesso limitado a determinados modelos, além de opções pagas. Não apresenta nesse fluxo um formulário acadêmico para enviar a proposta. O uso gratuito e uma candidatura a apoio em nuvem são ações diferentes.'),p('O que a Nicoli precisa preencher','HeadX'),p('Não há campos de proposta científica confirmados neste fluxo. Credenciais de acesso e eventual configuração de projeto são pessoais; não devem ser colocadas neste PDF. Este documento não cria conta, chave ou projeto nem ativa faturamento.'),p('Condições relevantes para a pesquisa','HeadX'),p('A tabela oficial informa uso de conteúdo para melhoria de produtos na camada gratuita. A proposta trabalha com dados fictícios, mas a equipe ainda deve conferir exatamente o que será transmitido. Cotas, modelos disponíveis e eventual migração para a camada paga deverão ser verificados na conta antes de executar experimentos.')]
b+=field('Descrição de uso - apoio interno','Gemini may be considered as an additional API comparison arm in the two-month study, subject to model availability, quotas, and the project data-sharing decision. Results will be collected with model identifiers, prompts, evidence versions, token use, latency, and failures. Free-tier availability is not treated as a guaranteed research grant or a commitment to cover the entire evaluation.','Não é campo de formulário de bolsa; texto de planejamento para eventual inclusão no estudo.')
b+=[p('Se o objetivo for Google Cloud','HeadX'),p('Será necessário identificar um programa específico de apoio acadêmico ou de créditos de nuvem. A página de preços da Gemini API, sozinha, não confirma essa candidatura. Não foi preparado um pedido de Google Cloud com campos inventados.')]
build('08_Google_Gemini','Google / Gemini | Situação da rota','INFORMATIVO. Camada gratuita de API; não há candidatura acadêmica mapeada neste fluxo.', [('Preços e condições da Gemini API','https://aistudio.google.com/docs/pricing')],b,'Incluído para distinguir o uso da Gemini API de um pedido de bolsa ou de créditos Google Cloud. Nenhum serviço pago foi ativado.')

(TMP/'manifest.json').write_text(json.dumps(DOCS,ensure_ascii=False,indent=2),encoding='utf-8')
with zipfile.ZipFile(OUT/'PDFs_por_provedor_Nicoli.zip','w',zipfile.ZIP_DEFLATED) as z:
    for item in DOCS: z.write(item['file'],Path(item['file']).name)
print(json.dumps(DOCS,ensure_ascii=False,indent=2))
