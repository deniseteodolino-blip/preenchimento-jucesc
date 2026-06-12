# Workflow Representante (de sócia PJ)

Toda sócia PJ precisa ter um representante PF cadastrado. O sub-formulário do representante é acessado pelo botão `btnRepresentatesAbrirAba` dentro do form da PJ na Pagina5.

## Acessar o sub-form de Representante

1. Abrir a PJ no QSA (Pagina5) — `__doPostBack` no Linkbutton da PJ
2. Aguardar 3s
3. Clicar em "Representante":
```javascript
document.getElementById('ctl00_ContentPlaceHolder_btnRepresentatesAbrirAba').click();
```
4. Aguardar 3s

## IDs do sub-form (note os typos do JUCESC)

⚠ O JUCESC tem typo nos IDs: alguns campos usam `Representate` (sem o segundo `n`) e outros `Representante`. Use uma função helper para evitar erro:

```javascript
function findByContains(s) {
  const all = document.querySelectorAll('input, select');
  for (const e of all) {
    if (e.id && e.id.toLowerCase().includes(s.toLowerCase())) return e;
  }
  return null;
}
```

IDs principais:
- `txtSocioRepresentanteCpfCnpj` — CPF do representante
- `txtSocioRepresentanteNome` — Nome
- `ddlSocioRepresentateTipoIdentidade` — Tipo de Doc (typo: "Representate")
- `txtSocioRepresentanteRG` — RG
- `cbSocioRepresentanteOrgaoExpedidor` — Órgão
- `ddlSocioRepresentanteOrgaoExpedidorUF` — UF
- `ddlSocioRepresentanteNacionalidade` — Nacionalidade
- `txtSocioRepresentanteDataNascimento` — Data Nasc
- `ddlSocioRepresentanteEstadoCivil` — EC
- `ddlSocioRepresentanteRegime` — Regime
- `rdbSocioRepresentateSexoM` / `rdbSocioRepresentateSexoF` — Sexo (typo)
- `txtSocioRepresentanteProfissao` — Profissão
- `ddlSocioRepresentanteTipoAssistidoRepresentado` — **Tipo Assistido = 304 (Representante)** para PJ
- `txtDDDRepresentanteSocio` / `txtTelefoneRepresentanteSocio` / `txtEmailRepresentanteSocio`
- `txtSocioRepresentanteCep` — CEP
- `Button1` — BUSCAR CEP do representante
- `ddlSocioRepresentanteUF` / `ddlSocioRepresentanteMunicipio` / `ddlSocioRepresentanteBairro`
- `cbSocioRepresentanteTipoLogradouro` / `ddlSocioRepresentanteLogradouro`
- `txtSocioRepresentanteNumero` / `txtSocioRepresentanteComplemento`
- `btnSocioRepresentanteIncluir` — GRAVAR Representante
- `btnRepresentatesVoltar` — Voltar para o form da PJ (não salva)

## Workflow recomendado (JUCESC — funciona)

### Chamada 1: CPF + Nome + TipoIdentidade (postback)
```javascript
function sv(id, v) { const e = document.getElementById(id); if (!e) return '!'; e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); return 'ok'; }
sv('ctl00_ContentPlaceHolder_txtSocioRepresentanteCpfCnpj', '<CPF>');
sv('ctl00_ContentPlaceHolder_txtSocioRepresentanteNome', '<NOME>');
const tipo = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRepresentateTipoIdentidade');
tipo.value = '2076';
tipo.dispatchEvent(new Event('change',{bubbles:true}));
__doPostBack('ctl00$ContentPlaceHolder$ddlSocioRepresentateTipoIdentidade','');
```
Espere 3s.

### Chamada 2: Dados pessoais + EC (postback)
```javascript
function sv(id, v) { const e = document.getElementById(id); if (!e) return '!'; e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); return 'ok'; }
sv('ctl00_ContentPlaceHolder_txtSocioRepresentanteRG', '<RG>');
sv('ctl00_ContentPlaceHolder_txtSocioRepresentanteDataNascimento', '<DD/MM/YYYY>');
sv('ctl00_ContentPlaceHolder_txtSocioRepresentanteProfissao', '<Profissão>');

const ec = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRepresentanteEstadoCivil');
ec.value = '<código>';
ec.dispatchEvent(new Event('change',{bubbles:true}));
__doPostBack('ctl00$ContentPlaceHolder$ddlSocioRepresentanteEstadoCivil','');
```
Espere 3s.

### Chamada 3: Sexo + Tipo Assistido + Órgão (postback)
```javascript
const reg = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRepresentanteRegime');
if (reg) { reg.value = '991'; reg.dispatchEvent(new Event('change',{bubbles:true})); }

document.getElementById('ctl00_ContentPlaceHolder_rdbSocioRepresentateSexoM').click();  // ou F
// rdbRepresentanteAnalfabetoN: pode não existir; alguns forms não pedem

const tipoAss = document.getElementById('ctl00_ContentPlaceHolder_ddlSocioRepresentanteTipoAssistidoRepresentado');
tipoAss.value = '304';  // REPRESENTANTE
tipoAss.dispatchEvent(new Event('change',{bubbles:true}));

const org = document.getElementById('ctl00_ContentPlaceHolder_cbSocioRepresentanteOrgaoExpedidor');
org.value = 'SSP';
org.dispatchEvent(new Event('change',{bubbles:true}));
__doPostBack('ctl00$ContentPlaceHolder$cbSocioRepresentanteOrgaoExpedidor','');
```
Espere 3s.

### Chamada 4: UF + DDD + Tel + Email + CEP, depois BUSCAR
```javascript
function sv(id, v) { const e = document.getElementById(id); if (!e) return '!'; e.value = v; e.dispatchEvent(new Event('change', {bubbles:true})); return 'ok'; }
sv('ctl00_ContentPlaceHolder_ddlSocioRepresentanteOrgaoExpedidorUF', 'SC');
sv('ctl00_ContentPlaceHolder_txtDDDRepresentanteSocio', '<DDD>');
sv('ctl00_ContentPlaceHolder_txtTelefoneRepresentanteSocio', '<TEL>');
sv('ctl00_ContentPlaceHolder_txtEmailRepresentanteSocio', '<EMAIL>');
sv('ctl00_ContentPlaceHolder_txtSocioRepresentanteCep', '<CEP>');

// Triggera BUSCAR CEP do representante
__doPostBack('ctl00$ContentPlaceHolder$Button1','');
```
Espere 5s (BUSCAR CEP demora mais que postback normal).

### Chamada 5: Logradouro + Número + GRAVAR
Após BUSCAR, UF/Município/Bairro/TipoLogradouro vêm preenchidos automaticamente, mas `Logradouro` precisa ser selecionado entre as opções carregadas (cascata):

```javascript
(() => {
  function findByContains(s) {
    const all = document.querySelectorAll('input, select');
    for (const e of all) {
      if (e.id && e.id.toLowerCase().includes(s.toLowerCase())) return e;
    }
    return null;
  }
  const log = findByContains('SocioRepresentanteLogradouro');
  // Procure a opção que melhor casa com o logradouro da minuta
  let val = null;
  const target = '<NOME_DO_LOGRADOURO_NORMALIZADO>'; // ex: 'CORONEL JOSE MARTINS CABRAL'
  for (const o of log.options) {
    if (o.text === target || o.text.includes(target)) { val = o.value; break; }
  }
  if (val) { log.value = val; log.dispatchEvent(new Event('change',{bubbles:true})); }
  
  const num = findByContains('SocioRepresentanteNumero');
  num.value = '<NÚMERO>';
  num.dispatchEvent(new Event('change',{bubbles:true}));
  
  // Complemento se houver
  const comp = findByContains('SocioRepresentanteComplemento');
  if (comp) {
    comp.value = '<COMPLEMENTO>'; // ex: 'APT 1204'
    comp.dispatchEvent(new Event('change',{bubbles:true}));
  }
  
  document.getElementById('ctl00_ContentPlaceHolder_btnSocioRepresentanteIncluir').click();
})()
```
Espere 4s.

## Após salvar o representante, salvar a PJ

Importante: o GRAVAR do representante retorna ao form da PJ. Você ainda precisa clicar GRAVAR da PJ para persistir:

```javascript
document.getElementById('ctl00_ContentPlaceHolder_btnSocioIncluir').click();
```

## JUCEB — diferença crítica

No JUCEB, o **BUSCAR CEP do representante NÃO funciona**. O endereço do representante precisa ser preenchido manualmente via cascata:

1. UF → postback → carrega municípios
2. Município → postback → carrega bairros
3. Bairro → postback → carrega logradouros
4. Logradouro → escolher

Se o Bairro mostrar "NÃO ENCONTRADO" (acontece com frequência no JUCEB), recomende preenchimento manual ao usuário.

## Erros comuns

**"A informação CPF do Representante é obrigatória"**
- O CPF não foi setado ou o `Tipo Assistido/Representado` está em branco. Para PJ comum, use 304.

**Form do representante não fecha após GRAVAR**
- Faltou Complemento ou Número (campo "Número" fica em vermelho mas Complemento também é checado mesmo opcional, em alguns casos). Setar Complemento ou deixá-lo vazio explicitamente.

**Endereço vazio mesmo após BUSCAR CEP (JUCEB)**
- BUSCAR CEP do representante não funciona no JUCEB. Use cascata manual ou peça ao usuário.

**"Representante já cadastrado"**
- Bom sinal — o representante já existe no sistema do JUCESC. Apenas confirme com GRAVAR.
