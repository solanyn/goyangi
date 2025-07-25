from airflow.decorators import dag, task
from airflow.utils.dates import days_ago
import re
from urllib.parse import urlparse
from datetime import timedelta
import logging
from typing import List
from tenacity import retry, retry_if_exception_type
from bs4 import BeautifulSoup
import httpx
import os
import s3fs
from urllib.request import urlopen

NSW_PROPERTY_SALES_INFORMATION_URL = (
    "https://valuation.property.nsw.gov.au/embed/propertySalesInformation"
)


@task
@retry(retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)))
def fetch_zip_file_links() -> List[str]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        response = httpx.get(
            NSW_PROPERTY_SALES_INFORMATION_URL,
            headers=headers,
            timeout=30.0,
            follow_redirects=True,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        links = [
            link["href"]
            for link in soup.find_all(href=True)
            if re.search(r"\.zip$", link["href"], re.IGNORECASE)
        ]

        if not links:
            raise ValueError("No ZIP files found on the page")

        return links
    except httpx.HTTPStatusError as e:
        raise Exception(f"HTTP error occurred: {e.response.status_code}")
    except httpx.RequestError as e:
        raise Exception(f"Request failed: {str(e)}")


@task
@retry(retry=retry_if_exception_type((IOError)))
def download_link_to_s3(url: str) -> str:
    s3 = s3fs.S3FileSystem(
        key=os.getenv("AWS_ACCESS_KEY_ID"),
        secret=os.getenv("AWS_SECRET_ACCESS_KEY"),
        client_kwargs={
            "endpoint_url": os.getenv("S3_ENDPOINT_URL"),
            "config": s3fs.config.Config(retries=dict(max_attempts=3)),
        },
    )

    path = urlparse(url).path.lstrip("/")
    uri = f"s3://bps/{path}"

    if s3.exists(uri):
        return f"Skipped {uri}"

    with urlopen(url) as fd:
        with s3.open(uri, "wb") as f:
            f.write(fd.read())
    return f"Uploaded {uri}"


@dag(
    dag_id="nsw_property_sales_dag_v2",
    schedule_interval="@daily",
    start_date=days_ago(1),
    catchup=False,
    tags=["property", "sales"],
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "execution_timeout": timedelta(minutes=30),
    },
)
def nsw_property_sales_dag():
    try:
        urls = fetch_zip_file_links()
        if not urls:
            raise ValueError("No ZIP files found to download")

        download_link_to_s3.expand(url=urls)
    except Exception as e:
        logging.error(f"DAG execution failed: {str(e)}")
        raise


dag = nsw_property_sales_dag()
