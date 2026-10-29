# Guia de uso detalhado

## Fluxo semanal

1. `python bot/vagas_linkedin.py buscar` — atualiza `painel/vagas.json` e `vagas.csv` (deduplicado por ID)
2. `python painel/gerar_painel.py` — regenera `vagas.html`
3. Abrir `painel/vagas.html`, filtrar e marcar status nos cards
4. Para vaga boa: candidatar, marcar "✓ Me candidatei"
5. Formulário complexo? `python tools/mapear_form.py <url>` despeja campos e opções em JSON

## Personalizando as buscas

Edite `BUSCAS` em `bot/vagas_linkedin.py`:

```python
("descricao", "keywords", "location", "filtros")
("Estagio dev - remoto", "estagio desenvolvimento", "Brasil",
 "f_E=1&f_WT=2&f_TPR=r604800")
```

Filtros úteis do LinkedIn:
- `f_E=1` estágio · `f_E=2` júnior
- `f_WT=1` presencial · `f_WT=2` remoto · `f_WT=3` híbrido
- `f_TPR=r604800` última semana

## Painel

- Filtros: texto livre, origem da busca, tipo (Estágio/Júnior/Pleno),
  local, status
- Status por card: Interesse → Candidatado → Entrevista → Descartado
  (persistidos em `localStorage`, sobrevive a regenerações do HTML)
- "Limpar status" reseta tudo
- Arquivos de saída são gitignored — o painel é seu, local

## Segurança

- A sessão do navegador fica em `bot/li_profile_chrome/` — gitignored
  e nunca deve ser compartilhada (contém seus cookies de login)
- O script apenas **lê** resultados de busca; não clica em
  "candidatar-se" nem interage com vagas
