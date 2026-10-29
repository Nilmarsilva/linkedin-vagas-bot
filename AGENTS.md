# AGENTS.md — linkedin-vagas-bot

Este projeto é desenvolvido com agentes de código no fluxo diário.
Este arquivo serve como instrução de projeto para agentes e
documenta as convenções do repositório.

## Contexto

Pipeline de automação para busca de emprego:

1. `bot/vagas_linkedin.py` — navega o LinkedIn logado (sessão
   persistente), executa buscas parametrizadas, extrai vagas
   e grava `painel/vagas.json` + `vagas.csv`
2. `painel/gerar_painel.py` — transforma o JSON em um painel
   HTML estático com filtros e status (localStorage)
3. `tools/mapear_form.py` — mapeia campos e opções de
   formulários de candidatura (útil para preencher com
   precisão)

## Convenções

- Nunca commitar `li_profile*` (sessão/cookies) — ver .gitignore
- Nenhum dado pessoal hardcoded: caminhos sempre relativos
  ou parametrizados
- Output gerado (`vagas.*`) é gitignored; `examples/` guarda
  amostras
- Pausas aleatórias entre ações no bot — ritmo de uso humano

## Detalhe técnico

A extração de vagas não depende de classes CSS (o LinkedIn usa
nomes ofuscados que mudam). O ID da vaga vem do atributo
`componentkey="job-card-component-ref-<id>"` presente em cada
card — estável e não requer cliques.

## Como contribuir

Issues → branch `feat/...` → PR com "Closes #N" → merge.
