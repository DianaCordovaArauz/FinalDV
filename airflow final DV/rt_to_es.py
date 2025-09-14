#!/usr/bin/env python3
"""
Generador near real-time -> Elasticsearch
Requisitos: pip install elasticsearch
Uso: python rt_to_es.py --index rt_sensores --rate 5 --host http://localhost:9200
Ctrl+C para detener.
"""
import argparse, random, time, uuid, json
from datetime import datetime, timezone
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError as ESConnError
from elasticsearch.helpers import bulk

MAPPING = {
    "mappings": {
        "dynamic": "true",
        "properties": {
            "@timestamp": {"type": "date"},
            "sensor_id":   {"type": "keyword"},
            "canton_id":   {"type": "integer"},
            "temp_c":      {"type": "float"},
            "hum_rel":     {"type": "float"},
            "status":      {"type": "keyword"}
        }
    }
}

def ensure_index(es: Elasticsearch, index: str):
    try:
        es.indices.get(index=index)
    except NotFoundError:
        es.indices.create(index=index, body=MAPPING)

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def gen_doc():
    return {
        "@timestamp": now_iso(),
        "sensor_id": f"S-{random.randint(1, 20):03d}",
        "canton_id": random.choice([1701,1702,1703,1704,1705]),  # ejemplo
        "temp_c": round(random.uniform(15.0, 34.0), 2),
        "hum_rel": round(random.uniform(30.0, 90.0), 1),
        "status": random.choice(["ok", "ok", "ok", "warn"])  # más prob. de "ok"
    }

def run(index: str, host: str, rate: int, batch: int):
    es = Elasticsearch(hosts=[host], request_timeout=10)
    ensure_index(es, index)
    print(f"[OK] Conectado a {host} | index: {index} | rate: {rate}/s | batch: {batch}")

    try:
        while True:
            actions = []
            for _ in range(batch):
                doc = gen_doc()
                actions.append({"_index": index, "_op_type": "index", "_source": doc})
            if actions:
                ok, errors = bulk(es, actions, chunk_size=len(actions), request_timeout=30)
                if errors:
                    print("[WARN] Algunos errores en bulk:", errors)
            # Mantén aprox. 'rate' documentos por segundo (batch puede ser >1)
            time.sleep(max(0.0, batch / max(1, rate)))
    except KeyboardInterrupt:
        print("\n[STOP] Cancelado por usuario.")
    except ESConnError as e:
        print(f"[ERROR] Conexión ES: {e}")
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--index", default="rt_sensores", help="Nombre del índice en ES")
    p.add_argument("--host", default="http://localhost:9200", help="URL de Elasticsearch")
    p.add_argument("--rate", type=int, default=10, help="docs por segundo aprox.")
    p.add_argument("--batch", type=int, default=10, help="tamaño de lote por envío")
    args = p.parse_args()
    run(args.index, args.host, args.rate, args.batch)
