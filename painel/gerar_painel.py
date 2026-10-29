# -*- coding: utf-8 -*-
"""Gera vagas.html a partir de vagas.json. Rode depois de cada busca."""
import json
from pathlib import Path

BASE = Path(__file__).parent
vagas = json.loads((BASE / "vagas.json").read_text(encoding="utf-8"))

LIXO = ("Esses resultados foram", "Veja as vagas", "Seu feedback")
vagas = [v for v in vagas if not any(x in v["titulo"] for x in LIXO)]

def tipo(v):
    t = (v["titulo"] + " " + v["busca"]).lower()
    if "estágio" in t or "estagio" in t or "estagiário" in t or "estagiario" in t:
        return "Estágio"
    if "pleno" in t or "senior" in t or "sênior" in t or "lead" in t:
        return "Pleno/Sênior"
    return "Júnior/Outros"

for v in vagas:
    v["tipo"] = tipo(v)

html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Vagas - Nilmar</title>
<style>
  :root { --azul:#1e2f4a; --cinza:#55677e; --bg:#f4f6f9; }
  * { box-sizing:border-box; margin:0; font-family:'Segoe UI',Arial,sans-serif; }
  body { background:var(--bg); padding:24px; }
  h1 { color:var(--azul); font-size:22px; }
  .sub { color:var(--cinza); font-size:13px; margin:4px 0 18px; }
  .filtros { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; }
  input,select { padding:8px 12px; border:1px solid #ccd3dd; border-radius:8px; font-size:14px; }
  input[type=text] { flex:1; min-width:220px; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:14px; }
  .card { background:#ffffff; border:1px solid #b9c4d4; border-radius:12px; padding:14px 16px;
          display:flex; flex-direction:column; gap:6px; }
  .card.oculto { display:none; }
  .card.descartado { background:#e8eaee; opacity:.5; }
  .card.candidatado { background:#d3f1e0; border:2px solid #177a4c; }
  .titulo { font-size:15px; font-weight:600; color:var(--azul); }
  .meta { font-size:13px; color:var(--cinza); }
  .tags { display:flex; gap:6px; flex-wrap:wrap; }
  .tag { font-size:11px; padding:2px 8px; border-radius:20px; background:#e8edf5; color:var(--azul); }
  .tag.estagio { background:#e0f2e9; color:#177a4c; }
  .tag.remoto { background:#e5eeff; color:#2c5ecb; }
  .tag.bh { background:#fff1de; color:#9a5b00; }
  .rodape { margin-top:auto; display:flex; gap:8px; align-items:center; padding-top:8px; flex-wrap:wrap; }
  .rodape a { font-size:13px; color:#fff; background:var(--azul); text-decoration:none;
              padding:6px 14px; border-radius:8px; }
  .btn-cand { font-size:12px; font-weight:600; padding:6px 12px; border-radius:8px;
              border:1px solid #177a4c; color:#177a4c; background:#e0f2e9; cursor:pointer; }
  .btn-cand.on { background:#177a4c; color:#fff; }
  .dt-cand { font-size:11px; color:#177a4c; }
  .rodape select { font-size:12px; padding:5px 8px; margin-left:auto; }
  .contador { font-size:13px; color:var(--cinza); margin-bottom:10px; }
  .stats { display:flex; gap:16px; font-size:13px; margin-bottom:14px; flex-wrap:wrap;
           align-items:center; }
  .stats b { color:var(--azul); }
  .btn-reset { font-size:12px; padding:5px 12px; border-radius:8px; border:1px solid #b3261e;
               color:#b3261e; background:#fff; cursor:pointer; margin-left:auto; }
</style>
</head>
<body>
<h1>Painel de vagas</h1>
<div class="sub">Gerado de vagas.json &mdash; status salvos no navegador (localStorage)</div>
<div class="filtros">
  <input type="text" id="q" placeholder="Buscar por título, empresa...">
  <select id="fBusca"><option value="">Origem: todas</option></select>
  <select id="fTipo"><option value="">Tipo: todos</option>
    <option>Estágio</option><option>Júnior/Outros</option><option>Pleno/Sênior</option></select>
  <select id="fOnde"><option value="">Local: todos</option>
    <option value="remoto">Remoto</option><option value="belo horizonte">Belo Horizonte</option></select>
  <select id="fStatus"><option value="">Status: todos</option>
    <option value="none">Sem status</option><option>Interesse</option>
    <option>Candidatado</option><option>Entrevista</option><option>Descartado</option></select>
</div>
<div class="stats" id="stats"></div>
<script>
function limparStatus() {
  if (confirm('Apagar todos os status salvos (candidatado, descartado etc)?')) {
    localStorage.removeItem('vagasStatus'); location.reload();
  }
}
</script>
<div class="contador" id="cont"></div>
<div class="grid" id="grid"></div>
<script>
const VAGAS = __JSON__;
const grid = document.getElementById('grid');
const st = JSON.parse(localStorage.getItem('vagasStatus') || '{}');
const save = () => localStorage.setItem('vagasStatus', JSON.stringify(st));

const buscas = [...new Set(VAGAS.map(v => v.busca))].sort();
const fBusca = document.getElementById('fBusca');
buscas.forEach(b => fBusca.insertAdjacentHTML('beforeend', `<option>${b}</option>`));

VAGAS.forEach(v => {
  const remoto = /remoto/i.test(v.local), bh = /belo horizonte|betim/i.test(v.local);
  const card = document.createElement('div');
  card.className = 'card';
  card.dataset.id = v.id;
  card.dataset.tipo = v.tipo;
  card.dataset.busca = v.busca;
  card.innerHTML = `
    <div class="titulo">${v.titulo}</div>
    <div class="meta">${v.empresa} &middot; ${v.local}</div>
    <div class="tags">
      <span class="tag ${v.tipo === 'Estágio' ? 'estagio' : ''}">${v.tipo}</span>
      ${remoto ? '<span class="tag remoto">Remoto</span>' : ''}
      ${bh ? '<span class="tag bh">BH</span>' : ''}
      <span class="tag">${v.busca}</span>
    </div>
    <div class="rodape">
      ${v.link ? `<a href="${v.link}" target="_blank">Ver vaga</a>` : ''}
      <button class="btn-cand" onclick="toggleCand('${v.id}', this.closest('.card'))">✓ Me candidatei</button>
      <span class="dt-cand"></span>
      <select onchange="setStatus('${v.id}', this.value, this.closest('.card'))">
        <option value="">— status —</option>
        <option>Interesse</option><option>Candidatado</option>
        <option>Entrevista</option><option>Descartado</option>
      </select>
    </div>`;
  grid.appendChild(card);
  refreshCard(card, v.id);
});

function getSt(id) { const s = st[id]; return typeof s === 'string' ? {s, d: null} : s; }

function refreshCard(card, id) {
  const s = getSt(id);
  const sel = card.querySelector('select');
  const btn = card.querySelector('.btn-cand');
  const dt = card.querySelector('.dt-cand');
  sel.value = (s && s.s) || '';
  card.classList.toggle('descartado', s && s.s === 'Descartado');
  card.classList.toggle('candidatado', s && s.s === 'Candidatado');
  btn.classList.toggle('on', s && s.s === 'Candidatado');
  dt.textContent = (s && s.s === 'Candidatado' && s.d) ? 'em ' + s.d : '';
}

function setStatus(id, val, card) {
  if (val) st[id] = {s: val, d: new Date().toLocaleDateString('pt-BR')};
  else delete st[id];
  save(); refreshCard(card, id); filtrar();
}

function toggleCand(id, card) {
  const s = getSt(id);
  setStatus(id, (s && s.s === 'Candidatado') ? '' : 'Candidatado', card);
}

function filtrar() {
  const q = document.getElementById('q').value.toLowerCase();
  const b = fBusca.value, t = document.getElementById('fTipo').value;
  const o = document.getElementById('fOnde').value, s = document.getElementById('fStatus').value;
  let n = 0;
  document.querySelectorAll('.card').forEach(c => {
    const txt = c.innerText.toLowerCase(), id = c.dataset.id;
    const cur = getSt(id);
    const ok = (!q || txt.includes(q)) && (!b || c.dataset.busca === b)
      && (!t || c.dataset.tipo === t) && (!o || txt.includes(o))
      && (!s || (s === 'none' ? !cur : (cur && cur.s === s)));
    c.classList.toggle('oculto', !ok);
    if (ok) n++;
  });
  document.getElementById('cont').textContent = n + ' vagas visíveis';
  const cont = {Candidatado: 0, Entrevista: 0, Interesse: 0, Descartado: 0};
  Object.values(st).forEach(v => { const s = (typeof v === 'string' ? v : v.s); if (s in cont) cont[s]++; });
  document.getElementById('stats').innerHTML =
    `<span><b>${cont.Candidatado}</b> candidaturas</span>` +
    `<span><b>${cont.Entrevista}</b> entrevistas</span>` +
    `<span><b>${cont.Interesse}</b> interesses</span>` +
    `<span><b>${cont.Descartado}</b> descartadas</span>` +
    `<button class="btn-reset" onclick="limparStatus()">Limpar status</button>`;
}
['q','fBusca','fTipo','fOnde','fStatus'].forEach(id =>
  document.getElementById(id).addEventListener('input', filtrar));
filtrar();
</script>
</body>
</html>"""

html = html.replace("__JSON__", json.dumps(vagas, ensure_ascii=False))
(BASE / "vagas.html").write_text(html, encoding="utf-8")
print("vagas.html gerado:", len(vagas), "vagas")
