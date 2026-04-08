# -*- coding: utf-8 -*-
"""
run_query_pnl.py
Executa a query P&L no BigQuery e salva os resultados em data_pnl.json.
Execute sempre que quiser atualizar os dados do dashboard.

Requisito: google-cloud-bigquery
  pip install google-cloud-bigquery google-cloud-bigquery-storage pyarrow
"""

from google.cloud import bigquery
import json
from datetime import datetime

PROJECT = "meli-bi-data"

QUERY = """
SELECT
    view_check_versiones_S4.DICCIONARIO_SUBBU        AS BU,
    view_check_versiones_S4.TARGET2_PRODUCT          AS Product,
    view_check_versiones_S4.DICCIONARIO_MACRO_BU     AS Macro_BU,
    MES_ID AS MES,
    view_check_versiones_S4.ANIO                     AS ANO,
    CASE
        WHEN CAST(SUBSTR(CAST(MES_ID AS STRING), 5, 2) AS INT64) BETWEEN 1  AND 3  THEN 'Q1'
        WHEN CAST(SUBSTR(CAST(MES_ID AS STRING), 5, 2) AS INT64) BETWEEN 4  AND 6  THEN 'Q2'
        WHEN CAST(SUBSTR(CAST(MES_ID AS STRING), 5, 2) AS INT64) BETWEEN 7  AND 9  THEN 'Q3'
        WHEN CAST(SUBSTR(CAST(MES_ID AS STRING), 5, 2) AS INT64) BETWEEN 10 AND 12 THEN 'Q4'
    END AS QUARTER,
    view_check_versiones_S4.PYL0   AS PYL_0,
    view_check_versiones_S4.PYL1   AS PYL_1,
    view_check_versiones_S4.PYL2   AS PYL_2,
    view_check_versiones_S4.PYL3   AS PYL_3,
    view_check_versiones_S4.PYL4   AS PYL_4,
    view_check_versiones_S4.M_L1_DESC  AS MNG_1,
    view_check_versiones_S4.M_L2_DESC  AS MNG_2,
    view_check_versiones_S4.M_L3_DESC  AS MNG_3,
    view_check_versiones_S4.M_L4_DESC  AS MNG_4,
    view_check_versiones_S4.ESCENARIO  AS Cenario,
    view_check_versiones_S4.DICCIONARIO_LOCAL_EBIT,
    view_check_versiones_S4.IMPORTE    AS Value
FROM
    `meli-bi-data.WHOWNER.BT_PLG_CHECK_VERSIONES_S4` AS view_check_versiones_S4
WHERE
    view_check_versiones_S4.ESCENARIO IN (
        'Actual Sin Distribuir',
        'Realizado',
        'Plan',
        'Forecast',
        'Real Distribuido Liminar 2023 sin Indirect to S4'
    )
    AND view_check_versiones_S4.MONEDA = 'Local'
    AND view_check_versiones_S4.DICCIONARIO_COUNTRY = 'Brasil'
    AND MES_ID >= 202201
GROUP BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18
ORDER BY 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18
"""

def safe(v):
    """Converte tipos numpy/pandas para Python nativo."""
    if v is None:
        return None
    if hasattr(v, "item"):          # numpy scalar
        return v.item()
    if hasattr(v, "isoformat"):     # date/datetime
        return v.isoformat()
    try:
        import math
        if math.isnan(float(v)):
            return None
    except (TypeError, ValueError):
        pass
    return v


def main():
    print(f"[{datetime.now():%H:%M:%S}] Conectando ao BigQuery (projeto: {PROJECT})...")
    client = bigquery.Client(project=PROJECT)

    print(f"[{datetime.now():%H:%M:%S}] Executando query...")
    df = client.query(QUERY).to_dataframe()
    print(f"[{datetime.now():%H:%M:%S}] {len(df):,} linhas retornadas.")

    records = []
    for row in df.to_dict(orient="records"):
        records.append({k: safe(v) for k, v in row.items()})

    output = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "row_count": len(records),
        "data": records,
    }

    out_path = "data_pnl.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, default=str)

    print(f"[{datetime.now():%H:%M:%S}] Salvo em {out_path}  ({len(records):,} linhas)")


if __name__ == "__main__":
    main()
