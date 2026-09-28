FROM apache/airflow:2.10.5-python3.12

USER airflow

COPY airflow/requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.12.txt"

RUN pip install --no-cache-dir \
    dbt-core==1.8.9 \
    dbt-snowflake==1.8.3