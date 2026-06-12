# Workflow Pagina5 (QSA) — Roteiro detalhado

A Pagina5 lista todos os participantes do QSA. Cada sócio é editado em um formulário modal que substitui o grid quando você clica em sua linha. O grid mostra três situações:
- **Atual Atual**: sócio já existente que permanece — verifique se tem dados completos; geralmente só falta `ddlTipoIdentidade`
- **Novo Novo**: sócio ingressante — preenchimento completo necessário
- **Atual Baixa**: sócio que está saindo — **NÃO TOQUE**, deixe como está

## Como abrir um sócio para edição

Cada linha do grid tem um link `<a href="javascript:__doPostBack('ctl00$ContentPlaceHolder$ListSocios$ctlXX$LinkbuttonY','')">`. Os botões alternam entre 7 (ímpares) e 8 (pares), e mudam para 6 após salvar. A regra prática:

```javascript
(() => {
  const links = document.querySelectorAll('a[href*="Linkbutton"]');
  for (const a of links) {
    const row = a.closest('tr');
    if (row && row.textContent.includes('<CPF_OR_CNPJ>')) {
      const m = a.getAttribute('href').match(/(ctl00\$ContentPlaceHolder\$ListSocios\$ctl\d+\$Linkbutton\d)/);
      if (m) { __doPostBack(m[1], ''); return 'clicked'; }
    }
  }
})()
```

Sempre **espere 3 segundos** após o click para o postback do servidor renderizar o formulário.

## Sócio PF — Workflow completo (NOVO)

Sequência de 5 chamadas Browser MCP + waits:

### Chamada 1: Click no sócio
```javascript
__doPostBack('ctl00$ContentPlaceHolder$ListSocios$ctlNN$LinkbuttonM','');
```
Espere 3s.

### Chamada 2: Set Tipo de Identidade (postback)
```javascript
const e = document.getElementById('ctl00_ContentPlaceHolder_ddlTipoIdentidade');
e.value = '2076'; // ou 516 (CNH), 6562 (profissional), 6573 (RNE)
e.dispatchEvent(new Event('change', {bubbles:true}));
__doPostBack('ctl00$ContentPlaceHolder$ddlTipoIdentidade','');
```
Espere 3s. **Após este postback é que os campos personal info devem aparecer** (RG, DataNasc, EC, Sexo, Analfabeto). Se não aparecerem, faça um hard reload (`navigate(URL)`) e tente de novo.

### Chamada 3: Preenche dados pessoais + Estado Civil (postback)
```javascript
function sv(id, v) { 
  const e = document.getElementById(id); 
  if (!e) return '!'; 
  e.value = v; 
  e.dispatchEvent(new Event('change', {bubbles:true})); 
  return 'ok'; 
}
sv('ctl00_ContentPlaceHolder_txtSocioRG', '<RG>');
sv('ctl00_ContentPlaceHolder_txtSocioDataNascimento', '09/08/1980'); // default Seazone
sv('ctl00_ContentPlaceHolder_txtSocioProfissao', '<Profissão>');
sv('ctl00_ContentPlaceHolder_txtNomePai', '-');  // default Seazone
sv('ctl00_ContentPlaceHolder_txtNomeMae', '-');  // default Seazone

const ec = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioEstadoCivil');
ec.value = '<código>'; // 492/493/6574/6863 etc — usar tabela do estado correto (JUCESC vs JUCEB)
ec.dispatchEvent(new Event('change', {bubbles:true}));
__doPostBack('ctl00$ContentPlaceHolder$ddlSocioEstadoCivil','');
```
Espere 3s. Após EC ser CASADO ou União Estável, o campo `ddlSocioRegime` aparece.

### Chamada 4: Regime + Sexo + Analfabeto + Espólio + Órgão Expedidor (postback)
```javascript
const reg = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRegime');
if (reg) { reg.value = '991'; reg.dispatchEvent(new Event('change', {bubbles:true})); } // só se casado/união

document.getElementById('ctl00_ContentPlaceHolder_rdbSocioSexoM').click();  // ou rdbSocioSexoF
document.getElementById('ctl00_ContentPlaceHolder_rdbAnalfabetoN').click();
document.getElementById('ctl00_ContentPlaceHolder_rdbEspolioNao').click();

const org = document.getElementById('ctl00_ContentPlaceHolder_cbSocioOrgaoExpedidor');
org.value = 'SSP'; // ou DETRAN, CRM, OAB etc
org.dispatchEvent(new Event('change', {bubbles:true}));
__doPostBack('ctl00$ContentPlaceHolder$cbSocioOrgaoExpedidor','');
```
Espere 3s.

### Chamada 5: UF do Órgão + GRAVAR
```javascript
const reg = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRegime');
if (reg && !reg.value) { 
  reg.value = '991';   // re-seta porque postback do órgão às vezes limpa
  reg.dispatchEvent(new Event('change', {bubbles:true})); 
}

const uf = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioOrgaoExpedidorUF');
uf.value = 'SC'; // ou SP, RS, MG etc
uf.dispatchEvent(new Event('change', {bubbles:true}));

document.getElementById('ctl00_ContentPlaceHolder_btnSocioIncluir').click();
```
Espere 4s. Verifique se voltou ao grid:
```javascript
!!document.querySelector('table#ctl00_ContentPlaceHolder_ListSocios')
```

## Sócio PF — Workflow ATUAL (já tem dados, só falta TipoIdentidade)

Quando o sócio aparece como "Atual Atual" no grid, geralmente o sistema já trouxe os dados via DBE. Verifique primeiro:

```javascript
(() => {
  const ids = ['ddlTipoIdentidade','ddlSocioEstadoCivil','txtSocioDataNascimento','txtSocioRG','txtSocioProfissao','cbSocioOrgaoExpedidor','ddlSocioOrgaoExpedidorUF','rdbSocioSexoM','rdbSocioSexoF','rdbAnalfabetoN','rdbEspolioNao'];
  const out = {};
  for (const id of ids) {
    const e = document.getElementById('ctl00_ContentPlaceHolder_'+id);
    out[id] = e ? {val: e.value, checked: e.checked} : 'missing';
  }
  return out;
})()
```

Se a única coisa faltando for `ddlTipoIdentidade`, basta:
1. Setar TipoIdentidade conforme o `cbSocioOrgaoExpedidor` (deduzir pela tabela em `codigos-jucesc.md`)
2. Postback do TipoIdentidade
3. GRAVAR

**Não re-preencha campos que já estão certos** — você pode acidentalmente sobrescrever dados corretos da DBE.

## Sócio PJ — Workflow

PJ tem formulário muito mais curto:

```javascript
// Após clicar na PJ no grid
document.getElementById('ctl00_ContentPlaceHolder_rdbOrgaoRegJuntaSim').click();  // tem NIRE? Sim
// espere 2s
const nire = document.getElementById('ctl00_ContentPlaceHolder_txtNire');
nire.value = '<NIRE>';
nire.dispatchEvent(new Event('change', {bubbles:true}));
document.getElementById('ctl00_ContentPlaceHolder_btnSocioIncluir').click();
```

NIRE para empresas de SC tem 11 dígitos começando com `42`. Para outros estados varia.

Para **representante da PJ**, veja `workflow-representante.md`.

## Diagnóstico: "campos em vermelho" sem destaque visual

Quando o GRAVAR retorna a mensagem genérica mas você não vê nenhum campo em vermelho:

1. **Verifique se EC e Regime estão preenchidos** (postbacks de OrgaoExpedidor às vezes resetam):
```javascript
(() => {
  const ec = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioEstadoCivil')?.value;
  const reg = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRegime')?.value;
  return {ec, reg};
})()
```

2. **Encontre campos com borda vermelha CSS**:
```javascript
(() => {
  const all = document.querySelectorAll('input, select');
  const reds = [];
  for (const e of all) {
    if (e.offsetParent === null) continue;
    const s = window.getComputedStyle(e);
    if (s.borderColor.includes('220, 53, 69') || s.borderColor.includes('255, 0')) {
      reds.push({id: e.id.replace('ctl00_ContentPlaceHolder_',''), val: e.value, type: e.type});
    }
  }
  return reds;
})()
```

3. **Se nada aparecer**, suspeite de cache de postback — `navigate(URL)` e reabra o sócio do zero.

4. **Se o erro é específico ao código de Estado Civil**, verifique se você não trocou JUCESC×JUCEB. União Estável é o caso mais comum: 6863 (JUCESC) vs 7111 (JUCEB).
