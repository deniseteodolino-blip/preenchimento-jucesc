---
name: preenchimento-jucesc-juceb
description: |
  Automatiza o preenchimento de QSA (Página 5), Capital Social/Distribuição de Quotas (Página 6) e Representantes de PJs nos sistemas REGIN da JUCESC (Santa Catarina) e JUCEB (Bahia) a partir de minutas de alteração contratual Seazone. Use SEMPRE que o usuário anexar uma minuta em PDF de "SPE LTDA" e pedir preenchimento de requerimento na JUCESC/JUCEB, mesmo sem mencionar "QSA" ou "Pagina5/6" — basta envolver URLs regin.jucesc.sc.gov.br ou regin.juceb.ba.gov.br. Acione também quando pedirem para "revisar todos os sócios", "preencher o capital de cada sócio" ou "preencher o representante" de uma sócia PJ. Cobre parsing da minuta, identificação Atual/Novo/Baixa, códigos JUCESC vs JUCEB validados, workflow de postbacks ASP.NET com waits adequados, e geração de XLSX de referência para fallback manual.
---

# Preenchimento JUCESC/JUCEB — QSA e Capital Social

## Quando usar esta skill

Use sempre que o pedido envolver:
- Minuta Seazone (PDF) de "alteração contratual" de uma "SPE LTDA" (Imbassaí, Urubici, Cachoeira, Sul da Ilha, Imbassaí, Rosa Spot, Campeche, etc.)
- URL `regin.jucesc.sc.gov.br` (Santa Catarina) ou `regin.juceb.ba.gov.br` (Bahia)
- Verbos como "preencher", "revisar", "verificar", "completar" combinados com "sócio(s)", "QSA", "capital", "Pagina5", "Pagina6" ou "representante"

Esta automação é alta repetição (37–65 sócios por requerimento, cada um exigindo ~5 chamadas sequenciais ao navegador). Use o roteiro abaixo, não improvise.

## Visão geral do fluxo

1. **Extrair** texto da minuta (`pdftotext -layout`)
2. **Parsear** os sócios em JSON estruturado (Python com regex)
3. **Identificar** o estado atual de cada linha no QSA: `Atual Atual`, `Novo Novo`, `Atual Baixa` (saída — pular)
4. **Preencher** Pagina5 sócio por sócio
5. **Preencher** Pagina6 (quotas + integralizado + a integralizar) sócio por sócio
6. **Preencher** Representantes para cada PJ
7. **Verificar totais** ao final do capital

## Pré-requisitos antes de começar

- Browser controlado (Claude in Chrome). Se houver múltiplos, **pergunte ao usuário qual** via `AskUserQuestion`.
- O usuário precisa estar logado no JUCESC/JUCEB **na mesma janela controlada** — não é possível logar no lugar dele (credenciais gov.br são propriedade dele). Se a página retornar "Não autorizado", peça para ele autenticar e abrir o requerimento até a Pagina5/6 antes de continuar.
- **Erros de validação genéricos** ("preencher os campos em vermelho") sem indicação visual costumam ser causados por **cache de postback ASP.NET**. Solução: `navigate()` para a mesma URL (hard reload) e reabrir o sócio — os campos personal info (Data Nascimento, Estado Civil, Sexo, Analfabeto) reaparecerão.

## Parsing da minuta

Use `scripts/parse_minuta.py` para extrair os sócios da minuta em JSON estruturado. Ele já lida com:
- Separação por `(N)` (ingressantes) e `N.` (sócios já existentes)
- Detecção PF vs PJ
- Extração de CPF, CNPJ, Nome, RG, Órgão Expedidor, UF, Estado Civil cru, Regime, Profissão, DDD, Telefone, Email, CEP
- Múltiplos padrões de CPF ("CPF nº", "CPF sob o n.º", "CPF/MF")
- Múltiplos padrões de CNPJ
- Caracteres invisíveis (`​` zero-width space que aparece após `(N)` em minutas Clicksign)

```bash
python scripts/parse_minuta.py <minuta.pdf> <output.json>
```

Para o capital (Pagina6), use `scripts/extract_capital.py` que parseia a tabela "Total de quotas / Capital integralizado / Capital a integralizar / %" presente em todas as minutas Seazone.

## Tabelas de códigos (NÃO confundir JUCESC com JUCEB)

Os códigos diferem entre os dois sistemas. Veja:
- `references/codigos-jucesc.md` — Códigos para Santa Catarina (Sul da Ilha, Urubici, Cachoeira, Campeche, Rosa Spot)
- `references/codigos-juceb.md` — Códigos para Bahia (Imbassaí)

Diferença crítica: "Solteiro em União Estável" é `6863` no JUCESC mas `7111` no JUCEB. Trocar isto causa o erro "preencher campos em vermelho" sem dica visual de qual campo.

## Workflow Pagina5 (QSA) — sócio PF

Veja `references/workflow-pagina5.md` para o roteiro completo, incluindo:
- Sequência exata de postbacks (TipoIdentidade → EC → OrgaoExpedidor)
- Quais campos são `__doPostBack` (causam reload parcial)
- Defaults: Data Nascimento `09/08/1980`, Nome Pai/Mãe `-`
- Tratamento de "Espólio" (sempre Não)
- Quando o sócio é "Atual": geralmente só falta `ddlTipoIdentidade` — verifique antes de refazer tudo

## Workflow Pagina5 (QSA) — sócio PJ

PJ é muito mais simples: marca "Sim" em "Está registrado em Junta?" → preenche `txtNire` → GRAVAR. Veja `references/workflow-pagina5.md` seção PJ.

## Workflow Pagina6 (Capital)

Padrão de 2 chamadas:
1. Click no sócio → wait → seta `txtQtdQuotasocio` + click `rdbCapitalIntegralizadoN` → wait
2. Seta `txtValorIntegralizado` + `txtValoraIntegralizar` → click `btnConfirmaQuota` → wait

Detalhe: quando o sócio integraliza a totalidade via bem (raro mas acontece — ex: José Ricardo Momo na URUBICI), usar `rdbCapitalIntegralizadoS` em vez de N.

Veja `references/workflow-pagina6.md`.

## Workflow Representante (PJ)

O representante de uma sócia PJ tem o próprio sub-formulário, acessado pelo botão `btnRepresentatesAbrirAba` dentro do form da PJ. Os campos seguem o mesmo padrão de postbacks mas com sufixo `Representante` (ou `Representate` — typo no JUCESC) nos IDs.

Particularidade: o **BUSCAR CEP do representante** funciona razoavelmente bem no JUCESC. No JUCEB ele tende a falhar — nesse caso o endereço precisa ser montado manualmente via cascata UF→Município→Bairro→Logradouro.

Veja `references/workflow-representante.md`.

## Estratégia para grandes requerimentos (40+ sócios)

Não tente fazer tudo em uma única sessão de conversa — o contexto fica cheio antes de terminar. Em vez disso:

1. Use `scripts/generate_reference_xlsx.py` para gerar planilha com todos os dados parseados + códigos JUCESC já aplicados, e salve em `outputs/`. Marque sócios já preenchidos em verde.
2. Preencha em batches de ~10–15 sócios por conversa, atualizando a planilha entre sessões.
3. No início de cada nova conversa, mencione qual sócio é o próximo (ex: "continue do #14 Diego Arent David") e referencie a planilha.

## Erros comuns e como diagnosticar

**"Para passar a próxima etapa é necessário preencher os campos em vermelho"** sem campo vermelho visível:
- Verifique se `ddlSocioEstadoCivil` e `ddlSocioRegime` estão preenchidos (eles costumam ser resetados por postbacks de OrgaoExpedidor — re-seta após postback do órgão)
- Se for casado: confirme regime no minuta (Comunhão Parcial 991 / Universal 992 / Separação 994)
- Se for união estável: use o código JUCESC `6863` (NÃO `7111` que é JUCEB)
- Se persistir: faça `navigate(URL)` para forçar hard reload e reabra o sócio

**Sócio aparece como "Atual" mas o GRAVAR falha:**
- Quase sempre é `ddlTipoIdentidade` vazio — sócios "Atual" frequentemente já têm RG/EC/etc preenchidos pelo DBE mas o Tipo de Doc ficou em branco. Setar 2076 (Carteira ID) ou 516 (CNH) ou 6562 (Carteira Profissional) conforme o RG/Órgão.

**Sessão expira ("Não autorizado"):**
- Não tente logar — peça ao usuário. Use a mesma janela controlada onde a navegação está ativa.

**"Representante já cadastrado":**
- Significa que o representante já está no sistema — apenas confirme via GRAVAR sem refazer.

## Boas práticas de execução

- **Use `AskUserQuestion`** para escolher o navegador quando houver múltiplos conectados.
- **Espere 3 segundos após cada postback** (`Bash sleep 3`). O JUCESC/JUCEB tem latência alta e clicar antes resulta em estado inconsistente.
- **Espere 4 segundos após GRAVAR** porque envolve commit no servidor + redirect.
- **Verifique** após GRAVAR se voltou ao grid (`!!document.querySelector('table#ctl00_ContentPlaceHolder_ListSocios')`). Se não voltou, há campo vermelho — leia a página e diagnostique.
- **Reporte progresso a cada 5–10 sócios** mas não a cada postback, para não poluir.

## Quando passar a bola para o usuário

Se um sócio individual exigir mais de 3 tentativas de GRAVAR sem sucesso, **pare** e:
1. Liste explicitamente quais campos você setou e quais o sistema reclama
2. Sugira que o usuário preencha esse sócio específico manualmente
3. Continue com o próximo

Não fique loopando no mesmo caso — perde tempo de contexto e frustra o usuário.

## Estrutura completa da skill

```
preenchimento-jucesc-juceb/
├── SKILL.md (este arquivo)
├── references/
│   ├── codigos-jucesc.md
│   ├── codigos-juceb.md
│   ├── workflow-pagina5.md
│   ├── workflow-pagina6.md
│   └── workflow-representante.md
└── scripts/
    ├── parse_minuta.py
    ├── extract_capital.py
    └── generate_reference_xlsx.py
```
