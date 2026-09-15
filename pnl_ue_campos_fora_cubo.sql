-- =============================================================================
-- CAMPOS QUE NAO EXISTEM NO CUBO (WHOWNER.LK_FIN_FA_CUBE_ACQ) -- direto da UE
-- -----------------------------------------------------------------------------
-- Companion de pnl_ue_mapping.sql e pnl_fin_fa_cube_acq.sql.
--
-- O cubo LK_FIN_FA_CUBE_ACQ (78 categorias PNL) NAO carrega o detalhe de
-- D.19.4 CPA linha a linha nem D.20.3 / D.28. So tem, destas 10, as duas
-- abaixo com equivalente confiavel:
--     UE_MP_MNG_SLS_FORCE_AMT_LC         -> slug 'Fuerza_de_Ventas'        (D.22.2)
--     UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC  -> slug 'Fuerza_de_Ventas_Propia'(D.19.4.3)
-- As outras 8 nao tem slug correspondente no cubo (ou o slug existente cobre
-- um campo DIFERENTE - ver nota 2) e por isso precisam vir direto daqui.
--
-- Saida agora em formato LONGO (igual pnl_ue_mapping.sql): uma linha por
-- PERIODO/SITE/BU/SUBBU/PRODUCT/CAMPO, cada uma das 10 metricas ja vira sua
-- propria linha de PYL (NUMERACION/N1..N4), em vez de 10 colunas lado a lado.
--
-- Por vir direto da BT_MP_UNIT_ECONOMICS, NAO tem as dimensoes extras do cubo
-- (payment method, device tap type, segmento, produto operacional) - so o
-- grao PERIODO / SITE / BU / SUBBU / PRODUCT.
--
-- Mapeamento 1:1 (todos os 10 campos tem linha propria no mapping - nenhuma
-- ambiguidade aqui, diferente do cubo):
--   UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC   -> D.20.3   Other Fixed Fintech Costs
--   UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC  -> D.19.4.1 Comisiones a Resellers Point
--   UE_MP_MNG_SLS_FORCE_AMT_LC                   -> D.22.2   Fuerza de Ventas       (cube: Fuerza_de_Ventas)
--   UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC            -> D.19.4.3 Fuerza de Venta Propia (cube: Fuerza_de_Ventas_Propia)
--   UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC  -> D.19.4.4 Other Sales Expenses Point
--   UE_MP_MNG_TELEVENTAS_AMT_LC                  -> D.19.4.5 Televentas
--   UE_MP_MNG_WEB_TERC_AMT_LC                    -> D.19.4.6 Venta en pagina web de terceros
--   UE_MP_MNG_PRES_LCL_AMT_LC                    -> D.19.4.7 Venta presencial en locales
--   UE_MP_MNG_MGM_AMT_LC                         -> D.19.4.8 MGM
--   UE_MP_SHIPPING_OPS_FIXED_AMT_LC              -> D.28     Shipping Ops Fixed
--
-- Nada se perde: se um 11o campo for adicionado ao UNPIVOT sem entrar no CTE
-- `mapa`, cai em NUMERACION = 'Z.99.99' (LEFT JOIN), nao desaparece.
--
-- Todas as metricas saem CAST(... AS BIGNUMERIC): o UNPIVOT exige tipo
-- identico em toda a lista IN (mesma razao de pnl_ue_mapping.sql).
--
-- CUSTO: medido via dry-run, janela 2024-01-01 -> hoje (~2,7 anos), estas 10
-- colunas: 16.652 GiB (~US$ 81). Estreite UE_DATE_DESDE para reduzir.
-- =============================================================================

DECLARE UE_DATE_DESDE DATE DEFAULT DATE '2024-01-01';   -- 2024 em diante
DECLARE UE_DATE_HASTA DATE DEFAULT CURRENT_DATE();

WITH base AS (
  SELECT
    PERIODO,
    SIT_SITE_ID,
    UE_MP_BU_MANAGERIAL,
    UE_MP_SUBBU_MANAGERIAL,
    UE_MP_PRODUCT_MANAGERIAL,
    CAST(SUM(UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC)  AS BIGNUMERIC) AS UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC,
    CAST(SUM(UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC) AS BIGNUMERIC) AS UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC,
    CAST(SUM(UE_MP_MNG_SLS_FORCE_AMT_LC)                  AS BIGNUMERIC) AS UE_MP_MNG_SLS_FORCE_AMT_LC,
    CAST(SUM(UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC)           AS BIGNUMERIC) AS UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC,
    CAST(SUM(UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC) AS BIGNUMERIC) AS UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC,
    CAST(SUM(UE_MP_MNG_TELEVENTAS_AMT_LC)                 AS BIGNUMERIC) AS UE_MP_MNG_TELEVENTAS_AMT_LC,
    CAST(SUM(UE_MP_MNG_WEB_TERC_AMT_LC)                   AS BIGNUMERIC) AS UE_MP_MNG_WEB_TERC_AMT_LC,
    CAST(SUM(UE_MP_MNG_PRES_LCL_AMT_LC)                   AS BIGNUMERIC) AS UE_MP_MNG_PRES_LCL_AMT_LC,
    CAST(SUM(UE_MP_MNG_MGM_AMT_LC)                        AS BIGNUMERIC) AS UE_MP_MNG_MGM_AMT_LC,
    CAST(SUM(UE_MP_SHIPPING_OPS_FIXED_AMT_LC)             AS BIGNUMERIC) AS UE_MP_SHIPPING_OPS_FIXED_AMT_LC
  FROM `meli-bi-data.WHOWNER.BT_MP_UNIT_ECONOMICS`
  WHERE UE_DATE BETWEEN UE_DATE_DESDE AND UE_DATE_HASTA
  GROUP BY ALL
),

-- 2) wide -> long (uma linha por campo UE)
ue_long AS (
  SELECT
    PERIODO,
    SIT_SITE_ID,
    UE_MP_BU_MANAGERIAL,
    UE_MP_SUBBU_MANAGERIAL,
    UE_MP_PRODUCT_MANAGERIAL,
    CAMPO_UE,
    VALOR
  FROM base
  UNPIVOT (VALOR FOR CAMPO_UE IN (
    UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC,
    UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC,
    UE_MP_MNG_SLS_FORCE_AMT_LC,
    UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC,
    UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC,
    UE_MP_MNG_TELEVENTAS_AMT_LC,
    UE_MP_MNG_WEB_TERC_AMT_LC,
    UE_MP_MNG_PRES_LCL_AMT_LC,
    UE_MP_MNG_MGM_AMT_LC,
    UE_MP_SHIPPING_OPS_FIXED_AMT_LC
  ))
),

-- 3) de/para CAMPO_UE -> linha do PYL
mapa AS (
  SELECT * FROM UNNEST(ARRAY<STRUCT<
      CAMPO_UE    STRING,
      NUMERACION  STRING,
      NOMBRE_PYL  STRING,
      NIVEL_PNL   STRING,
      N1_MARGEN   STRING,
      N2_SUBTOTAL STRING,
      N3_DETALLE  STRING,
      N4_UE       STRING
  >>[
    ('UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC',  'D.20.3',   'Other Fixed Fintech Costs',        'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.20 Other Fixed Costs',          'D.20.3 Other Fixed Fintech Costs', NULL),
    ('UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC', 'D.19.4.1', 'Comisiones a Resellers Point',     'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.1 Comisiones a Resellers Point'),
    ('UE_MP_MNG_SLS_FORCE_AMT_LC',                  'D.22.2',   'Fuerza de Ventas',                 'PYL_DETAIL_MANAGERIAL_NEW', 'D. Direct Contribution', 'D.22 Sales Expenses',             'D.22.2 Fuerza de Ventas', NULL),
    ('UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC',           'D.19.4.3', 'Fuerza de Venta Propia Acquiring', 'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.3 Fuerza de Venta Propia Acquiring'),
    ('UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC', 'D.19.4.4', 'Other Sales Expenses Point',       'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.4 Other Sales Expenses Point'),
    ('UE_MP_MNG_TELEVENTAS_AMT_LC',                 'D.19.4.5', 'Televentas',                       'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.5 Televentas'),
    ('UE_MP_MNG_WEB_TERC_AMT_LC',                   'D.19.4.6', 'Venta en pagina web de terceros',  'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.6 Venta en pagina web de terceros'),
    ('UE_MP_MNG_PRES_LCL_AMT_LC',                   'D.19.4.7', 'Venta presencial en locales',      'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.7 Venta presencial en locales'),
    ('UE_MP_MNG_MGM_AMT_LC',                        'D.19.4.8', 'MGM',                              'PYL_MANAGERIAL_UE_NEW',    'D. Direct Contribution', 'D.19 Customer Acquisition Cost',  'D.19.4 CPA', 'D.19.4.8 MGM'),
    ('UE_MP_SHIPPING_OPS_FIXED_AMT_LC',             'D.28',     'Shipping Ops Fixed',               'SUBTOTALES_MANAGERIAL_NEW', 'D. Direct Contribution', 'D.28 Shipping Ops Fixed',        NULL, NULL)
  ])
)

-- 4) resultado final: 1 linha por PERIODO/SITE/BU/SUBBU/PRODUCT/campo, ja
--    categorizada como uma linha de PYL
SELECT
  l.PERIODO,
  l.SIT_SITE_ID,
  l.UE_MP_BU_MANAGERIAL,
  l.UE_MP_SUBBU_MANAGERIAL,
  l.UE_MP_PRODUCT_MANAGERIAL,
  COALESCE(m.NUMERACION , 'Z.99.99')                    AS NUMERACION,
  COALESCE(m.NOMBRE_PYL , CONCAT('A categorizar - ', l.CAMPO_UE)) AS NOMBRE_PYL,
  COALESCE(m.NIVEL_PNL  , 'NO_MAPEADO')                  AS NIVEL_PNL,
  m.N1_MARGEN,
  m.N2_SUBTOTAL,
  m.N3_DETALLE,
  m.N4_UE,
  l.CAMPO_UE,
  l.VALOR
FROM ue_long AS l
LEFT JOIN mapa AS m
  ON m.CAMPO_UE = l.CAMPO_UE
WHERE l.VALOR IS NOT NULL
  AND l.VALOR <> 0
ORDER BY
  l.PERIODO, l.SIT_SITE_ID, l.UE_MP_BU_MANAGERIAL, l.UE_MP_SUBBU_MANAGERIAL,
  l.UE_MP_PRODUCT_MANAGERIAL, NUMERACION
;

-- =============================================================================
-- NOTAS
-- -----------------------------------------------------------------------------
-- 1) Diferente de pnl_ue_mapping.sql, aqui NENHUM dos 10 campos precisou de
--    CASE WHEN / split por TPV_SEGMENT_ID - e o SUM cru de cada coluna,
--    exatamente como na sua query original. Mapeamento 1:1, sem ambiguidade.
-- 2) Cuidado ao cruzar com o cubo (pnl_fin_fa_cube_acq.sql): o slug
--    'Other_Sales_Expenses' do cubo mapeia para D.22.1 (UE_MP_MNG_OTH_SLS_
--    EXP_AMT_LC, "Other Sales Expenses DC" - generico), que E DIFERENTE de
--    D.19.4.4 (UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC, "Other Sales
--    Expenses Point" - especifico) que esta aqui. Nao sao a mesma linha
--    apesar do nome parecido.
-- 3) Para juntar com pnl_ue_mapping.sql num unico long-format (mesmas colunas
--    de saida), basta UNION ALL os dois SELECTs finais - a estrutura de
--    colunas (PERIODO..PRODUCT, NUMERACION, NOMBRE_PYL, NIVEL_PNL, N1..N4,
--    CAMPO_UE, VALOR) e compativel entre os dois arquivos.
-- =============================================================================
