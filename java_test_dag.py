import datetime as dt

import airflow
from airflow.models import DAG
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.latest_only_operator import LatestOnlyOperator
from airflow.operators.python_operator import PythonOperator

from airflow.operators.docker_operator import DockerOperator
from airflow.operators.bash_operator import BashOperator


from airflow.utils.dates import days_ago
from pprint import pprint

DAG_ID = "Java-hello-world-test"  # must change before uploading to airflow !!!
START_DATE = days_ago(1)
# SCHEDULE_INTERVAL = dt.timedelta(hours=12)
# SCHEDULE_INTERVAL = "@daily"
SCHEDULE_INTERVAL = "0 22 * * 2-6"

MAX_ACTIVE_RUN = 1
MAX_CONCURRENT_TASKS = 3
RETRY_COUNT = 3
RETRY_DELAY = dt.timedelta(minutes=5)

EMAIL = "mobinalhassan1@gmail.com"
OWNER = "datascope2"

default_args = {
    'owner': OWNER,
    'depends_on_past': False,
    'start_date': START_DATE,
    'email': [EMAIL],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': RETRY_COUNT,
    'retry_delay': RETRY_DELAY,
    # 'execution_timeout': timedelta(seconds=300),
    # 'on_failure_callback': some_function,
    # 'on_success_callback': some_other_function,
    # 'on_retry_callback': another_function,
    'trigger_rule': 'all_done'
}

dag = DAG(
    dag_id=DAG_ID,
    schedule_interval=SCHEDULE_INTERVAL,
    start_date=START_DATE,
    max_active_runs=MAX_ACTIVE_RUN,
    catchup=False,
    default_args=default_args,
    concurrency=MAX_CONCURRENT_TASKS

)

latest_only = LatestOnlyOperator(task_id='my_latest_only', dag=dag)

java_test_scheduler = DockerOperator(
    task_id='Java-hello-world-test-scheduler',
    image='registry.gitlab.com/mobinalhassan/jamay_aeronova:latest',
    auto_remove=True,
    force_pull=True,
    dag=dag
)

latest_only >> java_test_scheduler