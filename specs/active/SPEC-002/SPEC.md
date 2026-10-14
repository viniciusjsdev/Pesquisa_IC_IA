---
id: SPEC-002
title: Serving vLLM reproduzivel para Qwen e adapters
status: ready
contract_version: 1
---

# SPEC-002: Serving vLLM reproduzivel para Qwen e adapters

## Goal

Preparar em `runpod/serving/` uma forma verificável de iniciar a base Qwen e os
adapters escolhidos como modelos distintos na API vLLM, sem executar um Pod.

## Context

O checkout possui seis adapters PEFT/LoRA e seus manifests em `FineTuning/`.
A base `Qwen/Qwen2.5-7B-Instruct` é obtida separadamente. A API local já possui
sete aliases candidatos em `inference_api/src/inference_api/models.py`, mas não
há serving remoto, revisão fixada da base nem confirmação de `/v1/models`.

## Scope

- Criar um manifesto de serving versionado com alias, bateria A/B, caminho do
  adapter, run de origem, SHA-256 do peso e campo obrigatório para a revisão
  exata da base. O código recusa iniciar enquanto essa revisão não for
  fornecida; não escolhe automaticamente o estado `latest`.
- Criar validação local que recusa caminhos ausentes, hash divergente, aliases
  duplicados, base incompatível e segredo em arquivo versionado.
- Criar comando/script de inicialização estática do vLLM com `--enable-lora` e
  `--lora-modules`, derivado do manifesto, e procedimento de teste de
  `/v1/models` e `chat/completions` sem disparar automaticamente o Pod.
- Alinhar o catálogo da API local aos aliases do manifesto e registrar no
  snapshot a revisão da base, run e hash do adapter efetivamente selecionado.
- Documentar dependências, transferência mínima de artefatos, configuração de
  porta protegida, início, inspeção, parada e remoção após a sessão curta.

## Non-scope

- Criar/iniciar Pod, baixar pesos, transferir arquivos, gastar créditos,
  habilitar carregamento dinâmico de LoRA, treinar ou avaliar modelos.
- Alterar manifests/resultados científicos ou mover `runpod/*.sh` existentes.
- Escolher definitivamente GPU, preço ou provedor alternativo sem teste real.

## Requirements

- REQ-001: O manifesto mapeia exatamente o repositório da base e os seis
  adapters inventariados; aliases coincidem com o campo `model` esperado pelo
  backend. A revisão exata da base é entrada operacional obrigatória e deve
  aparecer no registro da sessão, pois os manifests de treino não a fixaram.
- REQ-002: O comando de serving é gerado de dados validados, sem shell montar
  comandos com texto não confiável e sem usar endpoint administrativo de LoRA.
- REQ-003: O serviço vLLM deve escutar apenas atrás de uma camada que exija
  credencial e permita somente os endpoints de inferência necessários. O
  cliente local nunca expõe token ao navegador nem grava segredo no snapshot.
- REQ-004: O catálogo da aplicação distingue candidato, disponível em
  `/v1/models` e confirmado por geração real; disponibilidade não se infere de
  arquivos locais ou de `status: completed` no manifest de treino.
- REQ-005: O script de verificação reporta versão do vLLM, revisão da base,
  aliases retornados, hashes e resultado de uma geração curta por alias, mas
  só roda contra um endpoint explicitamente informado pelo operador.

## Business or domain rules

- BR-001: Um adapter é overlay de uma base compatível, não modelo completo.
- BR-002: Baterias A e B não são equivalentes; snapshot preserva sua origem.
- BR-003: Trocar o alias em uma chamada não muda a seleção de outro usuário.

## Decisions already made

- A base e os seis adapters estão no catálogo `FineTuning/docs/modelos_disponiveis.md`.
- O serving é estático na inicialização; carregamento dinâmico é excluído por
  `docs/arquitetura_inferencia_compartilhada.md`.
- O Pod só será acionado em uma sessão futura explicitamente autorizada.
- Os manifests de treino identificam a base por nome, sem revisão dos pesos.
  A revisão escolhida para serving será registrada como tal, sem alegar ser
  idêntica à usada no treino até haver evidência independente.

## Constraints

- Não imprimir tokens, URLs com credenciais ou conteúdo integral dos pesos.
- Preservar Git LFS, dados, checkpoints, manifests e resultados históricos.
- Scripts devem falhar antes de lançar vLLM se qualquer arquivo declarado não
  for encontrado ou não corresponder ao hash esperado.

## Acceptance criteria

- AC-001: Manifesto contém sete aliases únicos e proveniência dos seis
  adapters, validada contra o catálogo científico sem modificar seus arquivos.
- AC-002: Um hash adulterado ou um adapter ausente faz o verificador falhar.
- AC-003: A inicialização gerada usa somente módulos LoRA estáticos e o alias
  solicitado pela API local coincide com o nome anunciado em `/v1/models`.
- AC-004: Sem endpoint remoto configurado, testes locais não iniciam Pod e a
  aplicação mostra modelos indisponíveis.
- AC-005: O runbook distingue validação estática, futura geração remota e custo
  de Pod; não afirma inferência real com base apenas na validação estática.

## Affected areas

- `runpod/serving/`, `runpod/README.md`, `inference_api/src/inference_api/models.py`,
  `inference_api/README.md`, documentação de arquitetura afetada.

## References

- `FineTuning/docs/modelos_disponiveis.md`: paths, hashes, baterias e limites.
- `FineTuning/docs/protocol_v1.md`: compatibilidade e template de inferência.
- `docs/arquitetura_inferencia_compartilhada.md`: topologia e decisão de LoRA estático.
- `inference_api/src/inference_api/models.py`: aliases e cliente existentes.
- `runpod/README.md`: scripts históricos e limites da frente remota.

## Skills

- Nenhum skill especializado de implementação é necessário; seguir o contrato
  desta SPEC e o `AGENTS.md` da raiz.

## Validation requirements

- VAL-001: `git diff --check` na raiz do projeto.
- VAL-002: Teste local automatizado do manifesto e dos erros de hash/path,
  sem conexão à RunPod.
- VAL-003: Conferência read-only dos seis caminhos e hashes do catálogo.
- VAL-004: Verificação remota manual somente quando a sessão paga for
  explicitamente autorizada; registrar resultado sem promovê-lo a benchmark.

## Review requirements

Revisão independente Sol/high da superfície remota, proveniência, proteção do
endpoint e preservação dos artefatos científicos.

## Execution and runtime

Executar conforme `SPEC.execution.json`. A thread da frente prepara e valida o
código local; não liga o Pod. Dependências e sequência estão em `specs/README.md`.
