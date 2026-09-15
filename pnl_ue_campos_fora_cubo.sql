-- =============================================================================
-- CAMPOS QUE NAO EXISTEM NO CUBO (WHOWNER.LK_FIN_FA_CUBE_ACQ) -- direto da UE
-- -----------------------------------------------------------------------------
-- Companion de pnl_ue_mapping.sql e pnl_fin_fa_cube_acq.sql.
--
-- O cubo LK_FIN_FA_CUBE_ACQ (78 categorias PNL) NAO carrega o detalhe de
-- D.19.4 CPA linha a linha nem D.20.3 / D.28. So tem, dessas 10, as duas
-- abaixo com equivalente confiavel:
--     UE_MP_MNG_SLS_FORCE_AMT_LC         -> slug 'Fuerza_de_Ventas'        (D.22.2)
--     UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC  -> slug 'Fuerza_de_Ventas_Propia'(D.19.4.3)
-- As outras 8 nao tem slug correspondente no cubo (ou o slug existente cobre
-- um campo DIFERENTE - ver nota 2) e por isso precisam vir direto daqui.
--
-- Por vir direto da BT_MP_UNIT_ECONOMICS, NAO tem as dimensoes extras do cubo
-- (payment method, device tap type, segmento, produto operacional) - so o
-- grao PERIODO / SITE / BU / SUBBU / PRODUCT, igual ao pnl_ue_mapping.sql.
--
-- Numeracao no mapping (para referencia cruzada com pnl_ue_mapping.sql):
--   UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC   -> D.20.3
--   UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC  -> D.19.4.1
--   UE_MP_MNG_SLS_FORCE_AMT_LC                   -> D.22.2   (cube: Fuerza_de_Ventas)
--   UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC            -> D.19.4.3 (cube: Fuerza_de_Ventas_Propia)
--   UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC  -> D.19.4.4
--   UE_MP_MNG_TELEVENTAS_AMT_LC                  -> D.19.4.5
--   UE_MP_MNG_WEB_TERC_AMT_LC                    -> D.19.4.6
--   UE_MP_MNG_PRES_LCL_AMT_LC                    -> D.19.4.7
--   UE_MP_MNG_MGM_AMT_LC                         -> D.19.4.8
--   UE_MP_SHIPPING_OPS_FIXED_AMT_LC              -> D.28
--
-- CUSTO: medido via dry-run, janela 2024-01-01 -> hoje (~2,7 anos), estas 10
-- colunas: 16.652 GiB (~US$ 81). Se so precisar de um periodo mais curto,
-- estreite UE_DATE_DESDE - o custo cai proporcionalmente.
-- =============================================================================

DECLARE UE_DATE_DESDE DATE DEFAULT DATE '2024-01-01';   -- 2024 em diante
DECLARE UE_DATE_HASTA DATE DEFAULT CURRENT_DATE();

SELECT
    PERIODO,
    SIT_SITE_ID,
    UE_MP_BU_MANAGERIAL,
    UE_MP_SUBBU_MANAGERIAL,
    UE_MP_PRODUCT_MANAGERIAL,
    SUM(UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC)  AS UE_MP_MNG_OTHER_FIXED_FINTECH_COSTS_AMT_LC,
    SUM(UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC) AS UE_MP_MNG_COMISIONES_RESELLERS_POINT_AMT_LC,
    SUM(UE_MP_MNG_SLS_FORCE_AMT_LC)                  AS UE_MP_MNG_SLS_FORCE_AMT_LC,
    SUM(UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC)           AS UE_MP_MNG_SLS_FORCE_PROPIA_AMT_LC,
    SUM(UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC) AS UE_MP_MNG_OTHER_SALES_EXPENSES_POINT_AMT_LC,
    SUM(UE_MP_MNG_TELEVENTAS_AMT_LC)                 AS UE_MP_MNG_TELEVENTAS_AMT_LC,
    SUM(UE_MP_MNG_WEB_TERC_AMT_LC)                   AS UE_MP_MNG_WEB_TERC_AMT_LC,
    SUM(UE_MP_MNG_PRES_LCL_AMT_LC)                   AS UE_MP_MNG_PRES_LCL_AMT_LC,
    SUM(UE_MP_MNG_MGM_AMT_LC)                        AS UE_MP_MNG_MGM_AMT_LC,
    SUM(UE_MP_SHIPPING_OPS_FIXED_AMT_LC)             AS UE_MP_SHIPPING_OPS_FIXED_AMT_LC
FROM `meli-bi-data.WHOWNER.BT_MP_UNIT_ECONOMICS`
WHERE UE_DATE BETWEEN UE_DATE_DESDE AND UE_DATE_HASTA
GROUP BY ALL
;

-- =============================================================================
-- NOTAS
-- -----------------------------------------------------------------------------
-- 1) Nomes de coluna e ordem identicos ao que voce colou originalmente - so
--    corrigido para sintaxe BigQuery valida:
--      - tabela qualificada com o projeto (`meli-bi-data.WHOWNER...`)
--      - DECLARE no lugar de string solta em UE_DATE >= '2024-01-01'
--        (equivalente, mas explicito sobre o tipo DATE e com limite superior)
-- 2) Cuidado ao cruzar com o cubo: o slug 'Other_Sales_Expenses' do cubo
--    mapeia para D.22.1 (UE_MP_MNG_OTH_SLS_EXP_AMT_LC, "Other Sales Expenses
--    DC" - generico), que E DIFERENTE de D.19.4.4 (UE_MP_MNG_OTHER_SALES_
--    EXPENSES_POINT_AMT_LC, "Other Sales Expenses Point" - especifico de
--    Point) que esta nesta query. Nao sao a mesma coisa apesar do nome
--    parecido - nao substituir uma pela outra.
-- 3) Se quiser estas 10 linhas ja no mesmo formato longo/categorizado dos
--    outros dois arquivos (uma linha por PERIODO/SITE/BU/SUBBU/PRODUCT/CAMPO,
--    com NUMERACION/N1..N4), e so pedir - a estrutura de UNPIVOT + mapa e a
--    mesma de pnl_ue_mapping.sql, so que restrita a estas 10 colunas.
-- =============================================================================
