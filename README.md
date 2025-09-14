# PROYECTO FINAL  
**Autora:** Diana Córdova  

---

## 🎯 Objetivo  
Mostrar cómo distintas tecnologías (**KNIME, Airflow, PostgreSQL, MySQL, Elasticsearch, Kibana**) se pueden orquestar para integrar datos sociales y de riesgo en tiempo real, producir indicadores de vulnerabilidad y exposición, y finalmente generar evidencia útil para la gestión del riesgo de desastres y la toma de decisiones en políticas públicas.

- **Tipo de entorno:** Local  
- **Fuentes de datos iniciales:**  
  - **Reales:** Datos Censo 2022 Ecuador  
  - **Sintéticos:** Datos creados a través de un script en Python (índice de jefatura de hogar femenina = 1, y cercanía al volcán Cotopaxi).  

---

## 🛠️ Tipo de Pipeline  

**Figura 1: Flujo ELT**  

Herramientas usadas: **KNIME, MySQL (VS Code connector), Apache Airflow (DAGs), Elasticsearch y Kibana**.  

---

## 🔹 KNIME  

**Figura 2. Flujo KNIME**  
**Figura 3. Visualizaciones con KNIME**  

- Transformación de un CSV de vivienda para evaluar la vulnerabilidad frente al Cotopaxi.  
- Depuración de columnas irrelevantes, filtrado por provincia Pichincha, creación de RowID limpio.  
- Imputación de valores faltantes y construcción de indicadores clave como **déficit habitacional** y un **puntaje socioeconómico de vulnerabilidad**.  
- Integración de datos auxiliares desde **MySQL**, normalización de identificadores, creación de variable de exposición.  
- Cálculo de un **puntaje final de vulnerabilidad (0–10)** con reglas y fórmulas.  
- Validación visual de duplicados/inconsistencias, exportación final a **base de datos** y **CSV**.  

---

## 📋 Retos y Soluciones

| **Reto** | **Solución** |
|----------|--------------|
| Conexión a MySQL desde terminal (Access denied, cambios no visibles) | Revisé credenciales, creé usuario con permisos, activé Autocommit / DB Transaction End en KNIME. |
| Creación de tablas sintéticas en MySQL (135,068 filas, errores DECIMAL, out of range) | Usé `DROP TABLE IF EXISTS`, ajusté MD5 + CONV, aumenté precisión de columnas (DECIMAL(7,2)). |
| Formato de identificadores (Row0 vs ROW-000001) | Reemplacé fórmulas en SQL y usé String Manipulation + RowID en KNIME para uniformar joins. |
| Definir escalas de puntaje de vulnerabilidad | Construí columnas derivadas (Math Formula, Rule Engine) y escalé índice final 0–10. |
| Validación visual y duplicados | Histogramas, scatter plots (JavaScript Views), GroupBy y consultas SQL para confirmar las 135,068 filas. |

---

## 🐍 Generación de Datos Sintéticos en Python  

**Script:** `seismic_events_nrt.py`  

- Simula eventos sísmicos con atributos físicos (**magnitud, profundidad, proximidad al volcán**).  
- Emisión en:  
  - **Archivos NDJSON** (batch para Airflow).  
  - **Directo a Elasticsearch** (streaming).  
- Campos: `station_id, ts_event, magnitude_ml, depth_km, proximidad_volcan_km`.  

| **Reto** | **Solución** |
|----------|--------------|
| `SyntaxError` en contador total | Corregí a `total += 1`. |
| Índice no creado en ES (404) | Ajusté condición `if MODE in ("es","both")`. |
| Duplicación de datos en modo both | Decidí entre `file` o `es` según escenario. |
| Conexión rechazada a ES | Validé que contenedor `elasticsearch` estuviera activo en `localhost:9200`. |

---

## 📦 Ingesta y Almacenamiento en Elasticsearch  

- Indexación de datos batch (censo_batch) y simulados (seismic_rt-*).  
- Definición de **mappings**:  
  - `magnitude_ml, depth_km, proximidad_volcan_km` → float  
  - `vulnerabilidad_score` → integer  
  - `location` → geo_point  
  - `ts_event, updated_at` → date  

**Con DAG en Airflow:**  
- Exportación automática desde batch + near-real-time hacia ES.  
- Resolución de problemas de tipado mediante casting.  
- Normalización de nulos y fechas ISO 8601.  
- Uso de `helpers.bulk` con lotes pequeños y reintentos.  
- Definición de `geo_point` para visualizaciones en Kibana.  

| **Reto** | **Solución** |
|----------|--------------|
| Duplicados tras join | Cambié Joiner en KNIME a `modifier=left`. |
| Campos numéricos como texto | Casting explícito en DAG. |
| Dynamic mapping mal interpretado | Definí mappings antes del bulk. |
| Kibana no reconocía fechas | Exporté con `.isoformat()`. |
| Payload demasiado grande | Usé `helpers.bulk` con lotes más pequeños. |
| Connection refused | Añadí dependencia de salud en Compose + validación con `/_count`. |
| Visualizaciones geoespaciales bloqueadas | Definí `location` como geo_point. |

---

## 📊 Visualización en Kibana  

- **Index patterns:** `censo_batch*` y `seismic*`.  
- Visualizaciones:  
  - Histogramas de magnitud por estación.  
  - Mapas de calor de vulnerabilidad por provincia y zona de lahar.  
  - Scatter plot proximidad–vulnerabilidad.  
  - Mapas de eventos sísmicos geolocalizados.  

**Figura 5. Visualizaciones batch y near-real-time.**

---

## ✅ Conclusiones  

Este pipeline integró **fuentes de datos heterogéneas** (censo en CSV + datos sintéticos en MySQL), usando KNIME como base.  
Con **Apache Airflow** orquesté procesos **batch y near-real-time**, estructurando un flujo reproducible.  

Los **datos sintéticos** representaron fenómenos físicos y sociales, y fueron indexados en **Elasticsearch**, resolviendo problemas de tipado y consistencia.  

Finalmente, construí **dashboards interactivos en Kibana** para visualizar relaciones entre actividad sísmica y vulnerabilidad socioeconómica.  

👉 Este proyecto constituye un **pipeline end-to-end** que demuestra capacidades en:  
- **ETL y orquestación de flujos**.  
- **Simulación de datos realistas**.  
- **Indexación eficiente en motores de búsqueda**.  
- **Visualización en tiempo real**.  
