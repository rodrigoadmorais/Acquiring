---
name: acquiring-dashboard
description: >
  Builds a complete live dashboard pipeline for any Mercado Livre Acquiring KPI or metric.
  Use this skill whenever the user wants to: create a dashboard from a Google Sheets spreadsheet,
  host it on GitHub Pages, automate data updates via Verdi Flows, or track any business metric
  (headcount, TPV, leads, churn, conversion, NPS, revenue, etc.) with a visual hosted dashboard.
  Triggers on: "criar dash", "gerar dashboard", "hospedar dashboard", "atualizar dados automatico",
  "verdi flows", "dash KPI", "dash headcount", "dash TPV", "dash leads", "dash metricas",
  or any mention of building a dashboard from a planilha to be hosted on GitHub with automated refresh.
  Also trigger when the user mentions a Google Sheets URL alongside a GitHub repo and wants visualization.
---

# Acquiring Dashboard Skill

Automates the full pipeline for **any metric type**:
**Google Sheets -> HTML Dashboard (GitHub Pages) -> Verdi Flow (auto-refresh)**

Produces four artifacts:
1. GitHub repository (created if it doesn't exist)
2. Self-contained HTML dashboard adapted to the data type
3. Initial JSON data files
4. Verdi Flow JSON (importable into https://web.furycloud.io/ai/verdi-flows)

---

## Step 1 - Understand the data and gather requirements

Ask ALL of these in a single message:

```
1. URL da planilha Google Sheets com os dados
2. Nome das abas (ex: "2025" e "2026", ou "Jan", "Historico"...)
3. Quais colunas existem? Cole os nomes das colunas aqui
   (isso define as dimensoes dos filtros e a estrutura do dash)
4. O que cada linha representa? O que esta sendo medido?
   (ex: "cada linha e um cargo com valores mensais de headcount",
        "cada linha e uma regiao com TPV mensal",
        "cada linha e um produto com leads por mes")
5. Ha uma coluna que distingue PLANO vs REALIZADO/FCST?
   (ex: coluna "CENARIO" com valores "PLANO" e "REALIZADO")
   Se nao, os dados sao apenas realizados?
6. GitHub: quer usar um repo existente ou criar um novo?
   - Se existente: owner/repo e branch padrao
   - Se novo: nome do repo, visibilidade (publico/privado), descricao
7. Titulo do dashboard e nome do arquivo HTML (ex: dash_tpv.html)
8. Frequencia de atualizacao (diario / a cada 2 dias / semanal)
9. IDs das credenciais Verdi:
   - Google Sheets credential ID
   - GitHub credential ID
```

---

## Step 2 - Analyze the data structure

Before building anything, map the columns to their roles:

- **Dimension columns**: text fields used for filtering/grouping (ex: Canal, Regiao, Produto, Equipe, Segmento)
- **Scenario column**: if exists, which column and which values mean Plan vs Actual
- **Metric columns**: numeric columns being tracked
  - If monthly: identify the time pattern (ex: `jan./25`, `Feb-25`, `2025-01`, `Jan 25`)
  - If already aggregated: identify what they represent
- **Year/period**: does data span multiple years? Are years in separate tabs or in one tab?

This analysis determines:
- Which filters to show (one dropdown per dimension column)
- The KPI labels (use the actual metric name, not "headcount")
- The chart axis labels
- The `transformRows()` function's field mapping
- The JSON file naming (ex: `tpv_2025.json`, `leads_q1.json`, `data_2025.json`)

---

## Step 3 - Create the GitHub repository (if needed)

If the user wants a new repo:

```bash
gh repo create <owner>/<repo-name> --public --description "<description>" --source=. --remote=origin
# OR using the API if gh CLI is not available:
# POST https://api.github.com/user/repos
```

Initialize with a README and set up GitHub Pages:
- Settings -> Pages -> Source: Deploy from branch -> branch: master (or main) -> / (root)

If using an existing repo, just verify it exists and note the default branch.

---

## Step 4 - Build the dashboard HTML

Single self-contained HTML file, all CSS/JS inline.

### Mercado Livre visual identity (NOT Mercado Pago)
```css
--ml-yellow: #FFE600;   /* header bar, active elements, primary chart color */
--ml-dark:   #333333;
--ml-bg:     #F5F5F5;
--ml-card:   #FFFFFF;
--ml-border: #E0E0E0;

/* dark theme (data-theme="dark") */
--ml-bg:   #1A1A1A;
--ml-card: #242424;
--ml-dark: #F0F0F0;
```

### Adapting to the data type

The dashboard structure is always the same, but labels and filters adapt:

**Filters**: one dropdown per dimension column detected in Step 2.
If data spans multiple years/periods: add a year/period selector.
If data has a time range (monthly): add De/Ate period selector when viewing full history.

**KPI cards** (always 4):
- If Plan vs Actual exists: Media Plano | Media Real | Atingimento % | Gap Medio
- If only Actual: Total/Media Atual | vs Periodo Anterior | Variacao % | [4th relevant KPI from data]
- Use the actual metric name in labels (ex: "Media TPV Plano", "Media Leads", "Atingimento HC")

**Charts**:
- Evolution: `type:'line'`, dashed=Plano/Meta, solid=Real. If no plan: single solid line.
- Gap/Variacao: `type:'bar'`, full width. Green=positive, red=negative.

**Rankings**: top entries by last period - adapt dimension to what makes sense
(ex: Top Canais for headcount, Top Regioes for TPV, Top Produtos for leads).

**Table**: dynamic columns based on actual data dimensions + metric columns.

**Resumo Executivo por IA** (collapsible panel, always use this exact label): auto-generated text adapted to metric type.

### Generic data loading pattern

```javascript
// Adjust variable names and array names to the data topic
// Ex: for TPV: let PTPV25=[], RTPV25=[], PTPV26=[], RTPV26=[]
// Ex: for headcount: let P25=[], R25=[], P26=[], R26=[]
let PLAN_DATA = [], REAL_DATA = []; // or per-year arrays if multi-year

// transformRows: adapt field names to match actual sheet columns
function transformRows(rows, year) {
  // IMPORTANT: month key format must match the actual sheet column names exactly
  // Detect from Step 2 analysis: 'jan./25', 'Jan-25', '2025-01', etc.
  const monthKeys = {
    '2025': [ /* actual month column names from sheet */ ],
    '2026': [ /* actual month column names from sheet */ ]
  };
  const keys = monthKeys[year] || [];
  const plan = [], real = [];
  rows.forEach(row => {
    // Adapt scenario detection to actual column/values in the sheet
    const scenario = (row['CENARIO'] || row['SCENARIO'] || row['Tipo'] || '').trim().toUpperCase();
    const obj = {
      // Map dimension columns: use actual column names from Step 2
      dim1: (row['<DIM1_COL>'] || '').trim(),  // ex: Canal, Regiao, Produto
      dim2: (row['<DIM2_COL>'] || '').trim(),  // ex: Sub-bu, Segmento
      // ... add all dimension columns
      label: (row['<LABEL_COL>'] || '').trim(), // ex: Cargo, SKU, Equipe
      m: keys.map(k => {
        const n = parseFloat(String(row[k] || '0').replace(',', '.'));
        return isNaN(n) ? 0 : n;
      })
    };
    if (!obj.dim1 && !obj.label) return;
    if (scenario === 'PLANO' || scenario === 'PLAN' || scenario === 'META') plan.push(obj);
    else real.push(obj);
  });
  return { plan, real };
}

// loadData: adapt filenames to match what the Verdi Flow writes
async function loadData() {
  try {
    const t = Date.now();
    const [r1, r2] = await Promise.all([
      fetch('<data_file_year1>.json?t=' + t).catch(() => null),
      fetch('<data_file_year2>.json?t=' + t).catch(() => null)
    ]);
    if (r1 && r1.ok) {
      const rows = await r1.json();
      const res = transformRows(rows, '2025');
      if (res.plan.length) PLAN_25 = res.plan;
      if (res.real.length) REAL_25 = res.real;
    }
    // repeat for second year...
  } catch(e) {}
  render();
}
loadData();
```

### CDN (exact versions - always use these)
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<script src="https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js"></script>
```

### Consistent UX controls (always include)
- Dark/light mode toggle
- Y-axis toggle (on/off)
- Data labels toggle (on/off)
- Export to Excel button (SheetJS)

---

## Step 5 - Create initial JSON data files

Name files to reflect the data topic and period:
- Headcount 2025/2026: `headcount_2025.json`, `headcount_2026.json`
- TPV by quarter: `tpv_q1.json`, `tpv_q2.json`
- Leads monthly: `leads_2025.json`
- Generic: `data_2025.json`, `data_2026.json`

The Verdi Flow will use these same filenames when writing to GitHub.

Format: array of raw sheet rows preserving original column names exactly:
```json
[
  {"CENARIO":"PLANO","Canal":"BIG SELLERS","jan./25":1000,"fev./25":1200,...},
  {"CENARIO":"REALIZADO","Canal":"BIG SELLERS","jan./25":980,"fev./25":1150,...}
]
```

CRITICAL: GitHub "Edit" operation requires the file to already exist on the target branch.
Create these files BEFORE the flow ever runs or it will fail with 404.

Push to both the default branch AND master (GitHub Pages branch).

---

## Step 6 - Create the Verdi Flow JSON (n8n format)

### Topology: one branch per sheet tab
```
Schedule Trigger
  |-> Read Sheet "<tab1>" -> Write <file1>.json to GitHub
  |-> Read Sheet "<tab2>" -> Write <file2>.json to GitHub
  (add more branches if there are more tabs)
```

For a single-tab sheet, use 3 nodes (Trigger + Read + Write).
For two tabs, use 5 nodes. For three tabs, use 7 nodes.

### Schedule config
| Frequency     | interval array                                           |
|---------------|----------------------------------------------------------|
| Diario        | [{"triggerAtHour":1}]                                    |
| A cada 2 dias | [{"field":"days","daysInterval":2,"triggerAtHour":1}]    |
| Semanal       | [{"field":"weeks","weeksInterval":1,"triggerAtHour":1}]  |

### NEVER use these nodes
- n8n-nodes-base.code - not installed in this Verdi instance
- n8n-nodes-base.set (v3.4) - strips ALL input data fields
- n8n-nodes-base.merge - not needed with per-branch file writes

### Node specs
- scheduleTrigger typeVersion: 1.2
- googleSheets typeVersion: 4.7, executeOnce: true
- github typeVersion: 1.1, executeOnce: true, operation:"edit", resource:"file"
- GitHub fileContent: `={{ JSON.stringify($input.all().map(item => item.json)) }}`
- Do NOT set additionalParameters.branch

Set `"active":true` and `"settings":{"executionOrder":"v1"}` at flow root.

---

## Step 7 - Push to GitHub

```bash
git add <all files>
git commit -m "Add <topic> dashboard + Verdi Flow automation"
git push origin master

# If default branch differs from master, also push data JSONs there:
git checkout -b tmp origin/<default-branch>
git checkout master -- <data-json-files>
git commit -m "Adicionar JSONs iniciais para Verdi Flow"
git push origin HEAD:<default-branch>
git checkout master && git branch -D tmp
```

---

## Step 8 - Return results

```
Dashboard publicado!
Link: https://<owner>.github.io/<repo>/<filename>.html

Arquivos criados:
- <filename>.html - dashboard
- <data_files>.json - dados iniciais
- <flow_name>.json - automacao Verdi Flows

Para ativar automacao:
1. Acesse https://web.furycloud.io/ai/verdi-flows
2. Import from file -> <flow_name>.json
3. Execute manualmente e confirme que todos os nodes ficaram com checkmark verde
4. Ative o toggle "Active"

Frequencia configurada: <frequencia>
```

---

## Examples of data type adaptations

### Headcount (PLANO vs REALIZADO)
- Dimensions: Canal, Sub-BU, Cargo, Role, RV
- Scenario col: CENARIO (PLANO / REALIZADO)
- Metrics: monthly headcount values (jan./25...dez./25)
- KPIs: Media Plano, Media Real, Atingimento %, Gap Medio

### TPV (volumes de pagamento)
- Dimensions: Canal, Produto, Regiao, Segmento
- May have no scenario (only realized) or Budget vs Real
- Metrics: monthly TPV R$ values
- KPIs: TPV Total, vs Budget, Variacao MoM, Crescimento YoY

### Leads / Funil de vendas
- Dimensions: Canal de origem, Equipe, Produto
- Metrics: leads, conversao %, tempo de ciclo
- KPIs: Total Leads, Taxa Conversao, Meta vs Real, Variacao

### NPS / Satisfacao
- Dimensions: Canal, Regiao, Segmento
- Metrics: NPS score, volume de respostas
- KPIs: NPS Atual, vs Meta, Variacao MoM, Benchmark
