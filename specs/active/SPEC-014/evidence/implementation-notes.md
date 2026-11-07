# Implementação local — 06/11/2026

Estado: em implementação; nenhum aceite ou ensaio remoto nesta etapa.

O baseline anterior ao código está em `implementation-baseline.json`, com cópia
externa verificável. O runtime efetivo do chat é `gpt-6-astra/high`, observado no
turn_context; o padrão do usuário substitui o executor documental indisponível.
A revisão será independente. Nenhum perfil científico foi trocado por isso.

O novo motor versionado compartilha os cinco papéis e reutiliza os schemas e a
leitura tipada da SPEC-013. O serviço interno usa os parsers SSE existentes,
centraliza serialização, orçamento e recibos e não faz retries. Perfis são
configuração confiável do servidor; autorizações antigas não são herdadas.
Para transmissão nova, a configuração exige recibo explícito ligado ao hash do
perfil, cenário, dados e limites. Testes injetam transporte fixture, sem rede externa.

Pacotes A continuam no formato imutável existente, selecionados por ID/hash.
Cada evidence_item é uma fonte do pacote; dados e metadados são projetados
integralmente. Não há descoberta, consulta ou fingerprint da pesquisa no A.
B usa o catálogo aprovado e o executor tipado, com fingerprints antes/depois.
Snapshots novos usam versão 7 e contrato de execução 1. Leitores de versões
anteriores continuam somente leitura; submissões legadas são recusadas.

O desenho corrigido permanece intacto. Não há mudança de layout ou proporções.
