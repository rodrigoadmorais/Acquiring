-- =============================================================================
-- P&L DETALHADO (dimensoes extras) a partir de WHOWNER.LK_FIN_FA_CUBE_ACQ
-- -----------------------------------------------------------------------------
-- Companion de pnl_ue_mapping.sql (que le WHOWNER.BT_MP_UNIT_ECONOMICS).
-- Esta tabela ja vem em formato longo (1 linha por categoria PNL) e traz 4
-- dimensoes que a BT_MP_UNIT_ECONOMICS nao tem:
--     OPERATION_PRODUCT_DESC, PAYMENT_METHOD_DESC, DEVICE_TAP_TYPE, SEGMENT_DESC
-- (Alem de BUYER/SELLER_SEGMENT_DESC, CHANNEL_DESC, ACQUIRER, FINANCING_TYPE_DESC,
--  incluidos tambem por completude.)
--
-- SUBBU (do cubo) sai como SUBBU_MANAGERIAL, para casar com o nome usado em
-- pnl_ue_mapping.sql (UE_MP_SUBBU_MANAGERIAL).
--
-- PORTFOLIO_AGRUPADO replica a regra que voce passou:
--     '%ACQ%'                    -> AQUISICAO
--     '%ENG%' / 'NA NA' / vazio  -> LEGADO
--     demais valores             -> mantidos como estao
--
-- CLASSIFICACAO (coluna CLASSE), o mesmo espirito de pnl_ue_mapping.sql:
--   * PYL        -> linha do P&L, classificada nos niveis N1..N4 do mapping
--   * CONTROL_UE -> margem pronta (contabil/economica) para conciliar,
--                   NAO somar junto com as linhas PYL
--   * REVISAR    -> categoria cujo destino no mapping ficou ambiguo (12 casos,
--                   ver OBS de cada uma). Nao foi silenciosamente classificada.
--   * NAO_PYL    -> metrica de volume/taxa (TPV, TPN, Take Rate) - nao e valor
--                   monetario de receita/custo, nao soma com o resto
--
-- Nada se perde: qualquer slug de PNL novo que aparecer no cubo e nao estiver
-- no CTE `mapa` cai em 'Z.99.99 / REVISAR' automaticamente (LEFT JOIN).
-- =============================================================================

DECLARE MONTH_DESDE INT64 DEFAULT 202401;   -- 2024 em diante (formato AAAAMM)

WITH base AS (
  SELECT
    MONTH,
    MONTH_DATE,
    SUBBU AS SUBBU_MANAGERIAL,
    PORTFOLIO_DESC,
    CASE
      WHEN PORTFOLIO_DESC LIKE '%ACQ%' THEN 'AQUISICAO'
      WHEN PORTFOLIO_DESC LIKE '%ENG%' THEN 'LEGADO'
      WHEN PORTFOLIO_DESC = 'NA NA' THEN 'LEGADO'
      WHEN PORTFOLIO_DESC IS NULL OR TRIM(PORTFOLIO_DESC) = '' THEN 'LEGADO'
      ELSE PORTFOLIO_DESC
    END AS PORTFOLIO_AGRUPADO,
    PNL AS PNL_SLUG,
    OPERATION_PRODUCT_DESC,
    PAYMENT_METHOD_DESC,
    DEVICE_TAP_TYPE,
    SEGMENT_DESC,
    BUYER_SEGMENT_DESC,
    SELLER_SEGMENT_DESC,
    CHANNEL_DESC,
    ACQUIRER,
    FINANCING_TYPE_DESC,
    SUM(VALUE_AMT) AS VALUE_AMT
  FROM `meli-bi-data.WHOWNER.LK_FIN_FA_CUBE_ACQ`
  WHERE MONTH >= MONTH_DESDE
  GROUP BY ALL
),

-- de/para PNL_SLUG -> linha do PYL (fonte da verdade desta analise)
mapa AS (
  SELECT * FROM UNNEST(ARRAY<STRUCT<
      PNL_SLUG    STRING,
      CLASSE      STRING,
      NUMERACION  STRING,
      NOMBRE_PYL  STRING,
      N1_MARGEN   STRING,
      N2_SUBTOTAL STRING,
      N3_DETALLE  STRING,
      N4_UE       STRING,
      OBS         STRING
  >>[
    ('Alquiler_MPOS', 'PYL', 'D.19.1.5', 'Alquiler MPOS', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.1 Sales MPOS', 'D.19.1.5 Alquiler MPOS', NULL),
    ('BPP', 'PYL', 'C.12', 'BPP', 'C. Variable Contribution', 'C.12 BPP', NULL, NULL, NULL),
    ('Bad_Debt_Incobrables', 'PYL', 'C.10', 'Bad Debt', 'C. Variable Contribution', 'C.10 Bad Debt', NULL, NULL, NULL),
    ('CHARGEBACKS_Contable', 'PYL', 'C.9.1', 'Chargebacks gross', 'C. Variable Contribution', 'C.9 Chargebacks', 'C.9.1 Chargebacks gross', NULL, NULL),
    ('CX_Fixed', 'PYL', 'D.24', 'CX Fixed', 'D. Direct Contribution', 'D.24 CX Fixed', NULL, NULL, NULL),
    ('CX_Variable', 'PYL', 'C.14', 'CX Variable', 'C. Variable Contribution', 'C.14 CX Variable', NULL, NULL, NULL),
    ('Collection_Fees', 'PYL', 'C.8', 'Collection Fees', 'C. Variable Contribution', 'C.8 Collection Fees', NULL, NULL, NULL),
    ('Consultor_Certificado', 'PYL', 'C.17.6', 'Other Variable Fintech Costs', 'C. Variable Contribution', 'C.17 Direct Variable Costs', 'C.17.6 Other Variable Fintech Costs', NULL, 'Componente: certified advisor'),
    ('Content_Cost', 'PYL', 'D.23', 'Loyalty Content', 'D. Direct Contribution', 'D.23 Loyalty Content', NULL, NULL, 'Componente de custo de conteudo'),
    ('Cost_Of_Product_Sold', 'PYL', 'D.19.2.1', 'Cost of Product Sold', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.2 Point COGS', 'D.19.2.1 Cost of Product Sold', NULL),
    ('COUPONS', 'PYL', 'Z.99.01', 'A categorizar - Coupons', 'Z. A Categorizar', 'Z.99 Campos sem mapeamento', NULL, NULL, 'Confirma residual ja sinalizado; sugestao original: C.17.8 Descuentos'),
    ('Descuentos_MPOS', 'PYL', 'D.19.1.3', 'Descuentos MPOS', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.1 Sales MPOS', 'D.19.1.3 Descuentos MPOS', NULL),
    ('Fin_Cost_FTP', 'PYL', 'B.5.2.1', 'Theoretical financing cost', 'B. Net Monetization', 'B.5 Financing Net', 'B.5.2 Financing Costs', 'B.5.2.1 Theoretical financing cost', NULL),
    ('FP_Variable', 'PYL', 'C.16', 'Fraud Prevention Variable', 'C. Variable Contribution', 'C.16 Fraud Prevention Variable', NULL, NULL, NULL),
    ('Fraud_Prevention', 'PYL', 'D.26', 'Fraud Prevention Fixed', 'D. Direct Contribution', 'D.26 Fraud Prevention Fixed', NULL, NULL, NULL),
    ('Fuerza_de_Ventas', 'PYL', 'D.22.2', 'Fuerza de Ventas', 'D. Direct Contribution', 'D.22 Sales Expenses', 'D.22.2 Fuerza de Ventas', NULL, NULL),
    ('Fuerza_de_Ventas_Propia', 'PYL', 'D.19.4.3', 'Fuerza de Venta Propia Acquiring', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.4 CPA', 'D.19.4.3 Fuerza de Venta Propia Acquiring', NULL),
    ('GA_BU_CORP', 'PYL', 'Z.99.08', 'A categorizar - G&A Corp BU', 'Z. A Categorizar', 'Z.99 Campos sem mapeamento', NULL, NULL, 'Confirma residual ja sinalizado (UE_MP_MNG_GNA_CORP_BU_AMT_LC)'),
    ('GA_CORPORATE', 'PYL', 'F.35', 'G&A BM', 'F. Business Margin', 'F.35 G&A BM', NULL, NULL, NULL),
    ('GA_LOCAL', 'PYL', 'E.30.2', 'G&A Directo Local', 'E. Business Contribution', 'E.30 G&A BC', 'E.30.2 G&A Directo Local', NULL, NULL),
    ('GA_SUBBU_CORP', 'PYL', 'E.30.1', 'G&A Directo Corp', 'E. Business Contribution', 'E.30 G&A BC', 'E.30.1 G&A Directo Corp', NULL, NULL),
    ('HII_FTP', 'PYL', 'B.5.2.2', 'Holding Interest Income', 'B. Net Monetization', 'B.5 Financing Net', 'B.5.2 Financing Costs', 'B.5.2.2 Holding Interest Income', NULL),
    ('Hosting_Fixed', 'PYL', 'D.25', 'Hosting Fixed', 'D. Direct Contribution', 'D.25 Hosting Fixed', NULL, NULL, NULL),
    ('Hosting_Variable', 'PYL', 'C.15', 'Hosting Variable', 'C. Variable Contribution', 'C.15 Hosting Variable', NULL, NULL, NULL),
    ('Insumos_Point', 'PYL', 'D.19.2.4', 'Insumos Point', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.2 Point COGS', 'D.19.2.4 Insumos Point', NULL),
    ('Marketing_Branding', 'PYL', 'D.29.3', 'Marketing Branding', 'D. Direct Contribution', 'D.29 Demand Gen, Branding & Others', 'D.29.3 Marketing Branding', NULL, NULL),
    ('OTHER_FIXED_COSTS', 'PYL', 'D.20.2', 'Other Fixed Costs', 'D. Direct Contribution', 'D.20 Other Fixed Costs', 'D.20.2 Other Fixed Costs', NULL, NULL),
    ('Other_Direct_Variable_Costs', 'PYL', 'C.17.6', 'Other Variable Fintech Costs', 'C. Variable Contribution', 'C.17 Direct Variable Costs', 'C.17.6 Other Variable Fintech Costs', NULL, 'Componente: UE_MP_MNG_OTH_DIR_VAR_COST_AMT_LC (total = 0 no periodo medido)'),
    ('Other_MPOS_Cogs', 'PYL', 'D.19.2.6', 'Other MPOS Cogs', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.2 Point COGS', 'D.19.2.6 Other MPOS Cogs', NULL),
    ('Other_Marketing_Fixed', 'PYL', 'D.29.4', 'Other Marketing Expenses', 'D. Direct Contribution', 'D.29 Demand Gen, Branding & Others', 'D.29.4 Other Marketing Expenses', NULL, NULL),
    ('Other_Sales_Expenses', 'PYL', 'D.22.1', 'Other Sales Expenses DC', 'D. Direct Contribution', 'D.22 Sales Expenses', 'D.22.1 Other Sales Expenses DC', NULL, NULL),
    ('PD_BM', 'PYL', 'F.33', 'PD BM', 'F. Business Margin', 'F.33 PD BM', NULL, NULL, NULL),
    ('PRODUCT_DEVELOPMENT_DIRECT', 'PYL', 'E.29.2', 'PD Directo Local', 'E. Business Contribution', 'E.29 PD BC', 'E.29.2 PD Directo Local', NULL, NULL),
    ('PRODUCT_DEVELOPMENT_INDIRECT', 'PYL', 'E.29.1', 'PD Directo Corp', 'E. Business Contribution', 'E.29 PD BC', 'E.29.1 PD Directo Corp', NULL, NULL),
    ('Plataforma', 'PYL', 'A.1.3.3', 'Uso de Plataforma Insurtech', 'A. Product Monetization', 'A.1 Net Variable Fees', 'A.1.3 Insurtech Variable Fees', 'A.1.3.3 Uso de Plataforma Insurtech', NULL),
    ('Reacondicionamento', 'PYL', 'D.19.2.5', 'Reacondicionamiento', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.2 Point COGS', 'D.19.2.5 Reacondicionamiento', NULL),
    ('SM_BU_CORP', 'PYL', 'Z.99.09', 'A categorizar - S&M Corp BU', 'Z. A Categorizar', 'Z.99 Campos sem mapeamento', NULL, NULL, 'Confirma residual ja sinalizado (UE_MP_MNG_SM_CORP_BU_AMT_LC)'),
    ('SM_CORPORATE', 'PYL', 'F.34', 'S&M BM', 'F. Business Margin', 'F.34 S&M BM', NULL, NULL, NULL),
    ('SM_Local', 'PYL', 'D.27', 'S&M Local DC', 'D. Direct Contribution', 'D.27 S&M Local DC', NULL, NULL, NULL),
    ('SM_SUBBU_CORP', 'PYL', 'E.31', 'S&M BC', 'E. Business Contribution', 'E.31 S&M BC', NULL, NULL, NULL),
    ('Sales_MPOS_Gross', 'PYL', 'D.19.1.1', 'Sales MPOS Gross', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.1 Sales MPOS', 'D.19.1.1 Sales MPOS Gross', NULL),
    ('Sales_Tax_MPOS', 'PYL', 'D.19.1.4', 'Sales tax MPOS', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.1 Sales MPOS', 'D.19.1.4 Sales tax MPOS', NULL),
    ('Sales_Taxes_Contable', 'PYL', 'B.6', 'Sales Taxes', 'B. Net Monetization', 'B.6 Sales Taxes', NULL, NULL, 'Variante contabil (sem ajuste)'),
    ('Sales_Taxes_Econ', 'PYL', 'B.6', 'Sales Taxes', 'B. Net Monetization', 'B.6 Sales Taxes', NULL, NULL, 'Variante economica (com UE_MP_MNG_SALES_TAXES_ADJ_AMT_LC)'),
    ('Shipping_Costs_Point', 'PYL', 'D.19.2.2', 'Shipping Costs Point', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.2 Point COGS', 'D.19.2.2 Shipping Costs Point', NULL),
    ('Special_Dates', 'PYL', 'D.29.2', 'Demand Generation', 'D. Direct Contribution', 'D.29 Demand Gen, Branding & Others', 'D.29.2 Demand Generation', NULL, NULL),
    ('Strategic_Initiatives', 'PYL', 'Z.99.06', 'A categorizar - Iniciativas (INI)', 'Z. A Categorizar', 'Z.99 Campos sem mapeamento', NULL, NULL, 'Confirma que e linha propria (UE_MP_MNG_INI_AMT_LC), distinta de Special_Dates/D.29.2'),
    ('Subscriptions_Revs', 'PYL', 'D.23', 'Loyalty Content', 'D. Direct Contribution', 'D.23 Loyalty Content', NULL, NULL, 'Componente: subx revenue (total = 0 no periodo medido)'),
    ('Telemetria', 'PYL', 'C.17.7', 'Telemetria', 'C. Variable Contribution', 'C.17 Direct Variable Costs', 'C.17.7 Telemetria', NULL, NULL),
    ('Warehousing_Point', 'PYL', 'D.19.2.3', 'Warehousing Point', 'D. Direct Contribution', 'D.19 Customer Acquisition Cost', 'D.19.2 Point COGS', 'D.19.2.3 Warehousing Point', NULL),
    ('BUSINESS_CONTRIBUTION_CONTABLE', 'CONTROL_UE', NULL, 'Business Contribution (control, contabil)', 'E. Business Contribution', 'E. Business Contribution (control)', NULL, NULL, 'Margem pronta - conciliar, nao somar com PYL'),
    ('BUSINESS_CONTRIBUTION_ECONOMICO', 'CONTROL_UE', NULL, 'Business Contribution (control, economico)', 'E. Business Contribution', 'E. Business Contribution (control)', NULL, NULL, 'Equivale a UE_MP_BUSINESS_CONTRIBUTION_AMT_LC'),
    ('BUSINESS_MARGIN_CONTABLE', 'CONTROL_UE', NULL, 'Business Margin (control, contabil)', 'F. Business Margin', 'F. Business Margin (control)', NULL, NULL, 'Margem pronta - conciliar, nao somar com PYL'),
    ('BUSINESS_MARGIN_ECONOMICO', 'CONTROL_UE', NULL, 'Business Margin (control, economico)', 'F. Business Margin', 'F. Business Margin (control)', NULL, NULL, 'Equivale a UE_MP_BUSINESS_MARGIN_AMT_LC'),
    ('DIRECT_CONTRIBUTION_CONTABLE', 'CONTROL_UE', NULL, 'Direct Contribution (control, contabil)', 'D. Direct Contribution', 'D. Direct Contribution (control)', NULL, NULL, 'Margem pronta - conciliar, nao somar com PYL'),
    ('DIRECT_CONTRIBUTION_ECONOMICO', 'CONTROL_UE', NULL, 'Direct Contribution (control, economico)', 'D. Direct Contribution', 'D. Direct Contribution (control)', NULL, NULL, 'Equivale a UE_MP_DC_AMT_LC'),
    ('NET_MONETIZATION_CONTABLE', 'CONTROL_UE', NULL, 'Net Monetization (control, contabil)', 'B. Net Monetization', 'B. Net Monetization (control)', NULL, NULL, 'Margem pronta - conciliar, nao somar com PYL'),
    ('NET_MONETIZATION_ECONOMICO', 'CONTROL_UE', NULL, 'Net Monetization (control, economico)', 'B. Net Monetization', 'B. Net Monetization (control)', NULL, NULL, 'Equivale a UE_MP_NET_MONETIZATION_AMT_LC'),
    ('PRODUCT_MONETIZATION_CONTABLE', 'CONTROL_UE', NULL, 'Product Monetization (control, contabil)', 'A. Product Monetization', 'A. Product Monetization (control)', NULL, NULL, 'Margem pronta - conciliar, nao somar com PYL'),
    ('PRODUCT_MONETIZATION_ECONOMICO', 'CONTROL_UE', NULL, 'Product Monetization (control, economico)', 'A. Product Monetization', 'A. Product Monetization (control)', NULL, NULL, 'Equivale a UE_MP_PRODUCT_MONETIZATION_AMT_LC'),
    ('VARIABLE_CONTRIBUTION_CONTABLE', 'CONTROL_UE', NULL, 'Variable Contribution (control, contabil)', 'C. Variable Contribution', 'C. Variable Contribution (control)', NULL, NULL, 'Margem pronta - conciliar, nao somar com PYL'),
    ('VARIABLE_CONTRIBUTION_ECONOMICO', 'CONTROL_UE', NULL, 'Variable Contribution (control, economico)', 'C. Variable Contribution', 'C. Variable Contribution (control)', NULL, NULL, 'Equivale a UE_MP_VARIABLE_CONTRIBUTION_AMT_LC'),
    ('BC_Adj', 'REVISAR', NULL, 'Business Contribution Adj', NULL, NULL, NULL, NULL, 'Ajuste de margem sem linha numerada equivalente no mapping atual - confirmar onde encaixa (H.* EBIT adjustments? ou item novo)'),
    ('BM_Adj', 'REVISAR', NULL, 'Business Margin Adj', NULL, NULL, NULL, NULL, 'Idem BC_Adj, ao nivel de Business Margin'),
    ('CBK_Theoretical', 'REVISAR', NULL, 'Chargeback Theoretical', NULL, NULL, NULL, NULL, 'Pode ser C.9.3 Ajuste contable cbk (UE_MP_CBK_PREVISION_AMT_LC) ou o proprio calculo teorico que alimenta CHARGEBACKS_Contable - confirmar antes de classificar'),
    ('Cashbacks_Sellers', 'REVISAR', NULL, 'Cashbacks Sellers', NULL, NULL, NULL, NULL, 'Pode ser UE_MP_BONIFICACIONES_SELLERS_AMT_LC ou UE_MP_CUPONES_SELLER_AMT_LC (ambos dentro de C.17.8 Descuentos) - confirmar qual componente'),
    ('Com_Resselers', 'REVISAR', NULL, 'Comisiones Resellers', NULL, NULL, NULL, NULL, 'Ambiguo entre C.17.5 Comisiones resellers (UE_MP_MNG_COMM_RSLR_AMT_LC) e D.19.4.1 Comisiones a Resellers Point (UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC) - confirmar qual'),
    ('DC_Adj', 'REVISAR', NULL, 'Direct Contribution Adj', NULL, NULL, NULL, NULL, 'Ajuste de margem sem linha numerada equivalente - confirmar'),
    ('Financing_Revenues', 'REVISAR', NULL, 'Financing Revenues', NULL, NULL, NULL, NULL, 'Pode ser so B.5.1.1 Financing Gross ou o subtotal B.5.1 inteiro (Gross+Floating+Interest) - confirmar escopo'),
    ('NM_Adj', 'REVISAR', NULL, 'Net Monetization Adj', NULL, NULL, NULL, NULL, 'Ajuste de margem sem linha numerada equivalente - confirmar'),
    ('Paid_On_Media', 'REVISAR', NULL, 'Paid On Media (POM)', NULL, NULL, NULL, NULL, 'Ambiguo entre D.29.1.2 POM Acquisition e o residual Z.99.05 POM Point (UE_MP_MNG_POM_POINT_AMT_LC) - confirmar escopo'),
    ('PM_Adj', 'REVISAR', NULL, 'Product Monetization Adj', NULL, NULL, NULL, NULL, 'Ajuste de margem sem linha numerada equivalente - confirmar'),
    ('Processing_Fees', 'REVISAR', 'A.1.1', 'Processing Fees (suspeito)', 'A. Product Monetization', 'A.1 Net Variable Fees', 'A.1.1 Processing Fees', NULL, 'ATENCAO: no periodo medido (>=2024-01), o total desta linha bateu EXATAMENTE igual ao de PRODUCT_MONETIZATION_ECONOMICO (14.112.620.082,78). Pode ser coincidencia de arredondamento ou um bug/placeholder na fonte - validar antes de tratar como A.1.1 real.'),
    ('VC_Adj', 'REVISAR', NULL, 'Variable Contribution Adj', NULL, NULL, NULL, NULL, 'Ajuste de margem sem linha numerada equivalente - confirmar'),
    ('TAKE_RATE_CONTABLE', 'NAO_PYL', NULL, 'Take Rate (contabil)', NULL, NULL, NULL, NULL, 'Metrica de taxa (%), nao e valor monetario de P&L - nao somar com as demais linhas'),
    ('TAKE_RATE_ECONOMICO', 'NAO_PYL', NULL, 'Take Rate (economico)', NULL, NULL, NULL, NULL, 'Metrica de taxa (%), nao e valor monetario de P&L - nao somar com as demais linhas'),
    ('TPN', 'NAO_PYL', NULL, 'TPN (volume de transacoes)', NULL, NULL, NULL, NULL, 'Metrica de volume/contagem, nao e valor monetario de P&L'),
    ('TPV', 'NAO_PYL', NULL, 'TPV (volume de pagamentos)', NULL, NULL, NULL, NULL, 'Metrica de volume monetario transacional, nao e uma linha de custo/receita do P&L')
  ])
)

SELECT
  b.MONTH,
  b.MONTH_DATE,
  b.SUBBU_MANAGERIAL,
  b.PORTFOLIO_DESC,
  b.PORTFOLIO_AGRUPADO,
  b.PNL_SLUG,
  COALESCE(m.CLASSE     , 'REVISAR')                         AS CLASSE,
  COALESCE(m.NUMERACION , 'Z.99.99')                         AS NUMERACION,
  COALESCE(m.NOMBRE_PYL , b.PNL_SLUG)                        AS NOMBRE_PYL,
  m.N1_MARGEN,
  m.N2_SUBTOTAL,
  m.N3_DETALLE,
  m.N4_UE,
  COALESCE(m.OBS, 'Categoria nova - nao mapeada, revisar manualmente') AS OBS,
  b.OPERATION_PRODUCT_DESC,
  b.PAYMENT_METHOD_DESC,
  b.DEVICE_TAP_TYPE,
  b.SEGMENT_DESC,
  b.BUYER_SEGMENT_DESC,
  b.SELLER_SEGMENT_DESC,
  b.CHANNEL_DESC,
  b.ACQUIRER,
  b.FINANCING_TYPE_DESC,
  b.VALUE_AMT
FROM base AS b
LEFT JOIN mapa AS m
  ON m.PNL_SLUG = b.PNL_SLUG
WHERE b.VALUE_AMT IS NOT NULL
  AND b.VALUE_AMT <> 0
ORDER BY
  b.MONTH, b.SUBBU_MANAGERIAL, NUMERACION, b.PNL_SLUG
;

-- =============================================================================
-- NOTAS
-- -----------------------------------------------------------------------------
-- 1) 12 categorias caem em CLASSE = 'REVISAR' (ambiguidade real, nao chute):
--       BC_Adj, BM_Adj, DC_Adj, NM_Adj, PM_Adj, VC_Adj   (ajustes de margem
--          sem linha numerada equivalente no mapping atual)
--       CBK_Theoretical      (pode ser C.9.3 ou o calculo teorico do CBK gross)
--       Cashbacks_Sellers    (qual componente de C.17.8 Descuentos)
--       Com_Resselers        (C.17.5 generico vs D.19.4.1 especifico de Point)
--       Financing_Revenues   (so B.5.1.1 Gross, ou o subtotal B.5.1 inteiro)
--       Paid_On_Media        (D.29.1.2 POM Acquisition vs Z.99.05 POM Point)
--       Processing_Fees      (valor bateu identico a PRODUCT_MONETIZATION_
--                              ECONOMICO no periodo medido - suspeito, validar
--                              antes de usar como A.1.1)
-- 2) 4 categorias sao metricas de volume/taxa, nao valores de P&L:
--       TPV, TPN, TAKE_RATE_CONTABLE, TAKE_RATE_ECONOMICO
--    Ficam com CLASSE = 'NAO_PYL' - uteis para ratio/analise, nao para somar
--    junto com o restante do P&L.
-- 3) 3 slugs confirmam residuais ja levantados em pnl_ue_mapping.sql:
--       GA_BU_CORP -> Z.99.08, SM_BU_CORP -> Z.99.09, Strategic_Initiatives -> Z.99.06
-- 4) Sales_Taxes_Contable e Sales_Taxes_Econ mapeiam para a MESMA linha B.6
--    (variante contabil vs economica/com ajuste) - nao somar as duas juntas.
-- 5) *_CONTABLE / *_ECONOMICO das margens (A/B/C/D/E/F) sao CONTROL_UE: servem
--    para conciliar contra a soma das linhas PYL da respectiva margem, nao para
--    somar junto com elas.
-- =============================================================================
