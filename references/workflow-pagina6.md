# Workflow Pagina6 (Capital Social) — Distribuição de Quotas

A Pagina6 lista os mesmos sócios da Pagina5, mas o formulário modal pede apenas três campos por sócio:
- `txtQtdQuotasocio` — Quantidade de quotas
- Radio `rdbCapitalIntegralizadoS` (Sim, totalmente integralizado) ou `rdbCapitalIntegralizadoN` (Não, parcialmente)
- Quando "Não": `txtValorIntegralizado` e `txtValoraIntegralizar`
- Quando "Sim": só quotas

## Extração dos valores da minuta

Use `scripts/extract_capital.py <minuta.pdf>` que parseia a tabela final "Sócio / Total de quotas / Capital integralizado / Capital a integralizar / %" e gera JSON agregado por CPF (somando múltiplas linhas do mesmo sócio).

## Identificar o link do sócio

```javascript
(() => {
  const links = document.querySelectorAll('a[href*="Linkbutton"]');
  for (const a of links) {
    const row = a.closest('tr');
    if (row && row.textContent.includes('<CPF_OR_CNPJ>')) {
      const m = a.getAttribute('href').match(/(ctl00\$ContentPlaceHolder\$listQuotasocio\$ctl\d+\$Linkbutton\d)/);
      if (m) { __doPostBack(m[1], ''); return 'clicked'; }
    }
  }
})()
```

Note o `listQuotasocio` (Pagina6) — diferente de `ListSocios` (Pagina5).

## Workflow padrão (parcialmente integralizado — caso mais comum)

### Chamada 1: Click no sócio
Espere 3s.

### Chamada 2: Quotas + radio "Não" (postback do radio)
```javascript
(() => {
  function sv(id, val) { const e = document.getElementById(id); if (!e) return '!'; e.value = val; e.dispatchEvent(new Event('change', {bubbles:true})); return 'ok'; }
  sv('ctl00_ContentPlaceHolder_txtQtdQuotasocio', '<QUOTAS_INTEIRAS>');
  document.getElementById('ctl00_ContentPlaceHolder_rdbCapitalIntegralizadoN').click();
})()
```
Espere 2s.

### Chamada 3: Integralizado + A Integralizar + GRAVAR
```javascript
(() => {
  function sv(id, val) { const e = document.getElementById(id); if (!e) return '!'; e.value = val; e.dispatchEvent(new Event('change', {bubbles:true})); return 'ok'; }
  sv('ctl00_ContentPlaceHolder_txtValorIntegralizado', '<INT_BR>');     // ex: '107175,97'
  sv('ctl00_ContentPlaceHolder_txtValoraIntegralizar', '<A_INT_BR>');   // ex: '94420,83'
  document.getElementById('ctl00_ContentPlaceHolder_btnConfirmaQuota').click();
})()
```
Espere 4s. Verifique que voltou ao grid e que a linha do sócio agora mostra os valores em vez de "00".

## Workflow especial — totalmente integralizado via bem imóvel

Raro mas acontece (ex: José Ricardo Momo na URUBICI). Quando o sócio integralizou 100% via bem:

```javascript
function sv(id, val) { const e = document.getElementById(id); e.value = val; e.dispatchEvent(new Event('change', {bubbles:true})); }
sv('ctl00_ContentPlaceHolder_txtQtdQuotasocio', '<QUOTAS>');
document.getElementById('ctl00_ContentPlaceHolder_rdbCapitalIntegralizadoS').click();  // SIM, totalmente
// não setar valor integralizado/a integralizar — não são pedidos quando S
document.getElementById('ctl00_ContentPlaceHolder_btnConfirmaQuota').click();
```

## Formato dos valores

- **Quotas**: inteiro sem pontuação. Ex: `20159680` (não `20.159.680`)
- **Valores monetários**: usar vírgula decimal e sem ponto de milhar. Ex: `107175,97` (não `107.175,97` nem `107175.97`)

O JUCESC/JUCEB aceita, mas em alguns casos é mais seguro mandar sem ponto de milhar para evitar parse errors.

## SAÍDA (sócio "Atual Baixa")

Sócios saindo da empresa aparecem com quotas zeradas (`00`, `00,00`, `00,00`) no grid e **NÃO devem ser editados**. Pular.

## Verificação final de totais

Ao terminar todos os sócios, verifique que os totais batem com a minuta:

```javascript
(() => {
  const rows = document.querySelectorAll('tr');
  let tQ = 0, tI = 0, tA = 0;
  for (const r of rows) {
    const cells = r.querySelectorAll('td');
    if (cells.length < 5) continue;
    const texts = Array.from(cells).map(c => c.textContent.trim());
    const hasCpf = texts.some(t => /^\d{11}$/.test(t) || /^\d{14}$/.test(t));
    if (!hasCpf) continue;
    const q = texts[texts.length - 3];
    const i = texts[texts.length - 2];
    const a = texts[texts.length - 1];
    tQ += parseInt(q.replace(/\./g, '').replace(/,.*/, '')) || 0;
    tI += parseFloat(i.replace(/\./g, '').replace(',', '.')) || 0;
    tA += parseFloat(a.replace(/\./g, '').replace(',', '.')) || 0;
  }
  return {totalQ: tQ, totalI: tI.toFixed(2), totalA: tA.toFixed(2), capital: (tI + tA).toFixed(2)};
})()
```

Compare com a Cláusula do Capital Social na minuta. Os três totais devem bater **exatamente**:
- Total de quotas
- Capital integralizado
- Capital a integralizar (e a soma deles = Capital Social total)

## Erros comuns

**"O capital integralizado da empresa não confere..."**
- Algum sócio teve 1 centavo de diferença. Reabra os sócios com valores que parecem suspeitos e ajuste. Frequentemente acontece com sócios convertidos de "Sim" para "Não" — re-aplicar o radio Não e re-setar os valores corrige.

**Linha do sócio continua com `00,00` após GRAVAR**
- O GRAVAR falhou silenciosamente. Reabra e re-execute as chamadas 2 e 3.

**Sessão expirou no meio**
- Peça ao usuário para refazer login. Os sócios já salvos persistem; continue de onde parou.
