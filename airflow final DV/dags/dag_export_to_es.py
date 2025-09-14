from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch, helpers
import psycopg2

# Parámetros de conexión
PG_CONN = {
    "dbname": "cotopaxi",
    "user": "airflow",
    "password": "airflow",
    "host": "cotopaxi_postgres",
    "port": 5432,
}

ES_CONN = {
    "hosts": ["http://elasticsearch:9200"],
}

INDEX_NAME = "vulnerabilidad_export"

# Función para extraer desde Postgres
def extract_from_postgres():
    conn = psycopg2.connect(**PG_CONN)
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            row_id,
            proximidad_volcan_km,
            exposicion_alta,
            jefatura_femenina,
            adultos_mayores,
            vulnerabilidad_final,
            ts_event,
            updated_at
        FROM rt_events;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# Función para transformar en documentos para ES
def transform(rows):
    for r in rows:
        yield {
            "_index": INDEX_NAME,
            "_source": {
                "row_id": r[0],
                "proximidad_volcan_km": float(r[1]) if r[1] else None,
                "exposicion_alta": int(r[2]) if r[2] else None,
                "jefatura_femenina": int(r[3]) if r[3] else None,
                "adultos_mayores": int(r[4]) if r[4] else None,
                "vulnerabilidad_final": int(r[5]) if r[5] else None,
                "ts_event": r[6].isoformat() if r[6] else None,
                "updated_at": r[7].isoformat() if r[7] else None,
            },
        }

# Función principal: exportar a ES
def export_to_elasticsearch():
    es = Elasticsearch(**ES_CONN)
    rows = extract_from_postgres()
    actions = transform(rows)
    helpers.bulk(es, actions)

# Definir DAG
default_args = {
    "owner": "diana",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    "dag_export_to_es",
    default_args=default_args,
    description="Exportar rt_events de Postgres a Elasticsearch",
    schedule_interval="@hourly",
    start_date=datetime(2025, 9, 10),
    catchup=False,
    tags=["cotopaxi", "export", "elasticsearch"],
) as dag:

    export_task = PythonOperator(
        task_id="export_postgres_to_es",
        python_callable=export_to_elasticsearch,
    )

    export_task
