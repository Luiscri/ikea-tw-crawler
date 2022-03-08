import os
import json
from typing import List

from google.cloud import storage
from google.cloud import bigquery

DATASET = os.environ.get('DATASET')
TABLENAME = os.environ.get('TABLENAME')
BUCKETNAME = os.environ.get('BUCKETNAME')
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')

def upload_data_to_bq(db: bigquery.Client, data: List[dict]):
    """Method which uploads the data passed as a parameter to BigQuery.

    Parameters
    ----------
    db: google.cloud.bigquery.Client
        BigQuery client used to create the connection and upload the data.
    data: list[dict]
        List of JSON-like objects to be uploaded.
    """

    bucket = storage.Client().get_bucket(BUCKETNAME)
    blob = bucket.get_blob('schemes/tweets_schema.json')
    table_schema = parse_bq_json_schema(json.loads(blob.download_as_bytes()))
    job_config = bigquery.LoadJobConfig(
        schema=table_schema,
        create_disposition='CREATE_IF_NEEDED',
        write_disposition='WRITE_APPEND',
        destination_table_description='Tweets collected from Twitter API',
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        time_partitioning=bigquery.table.TimePartitioning(
            field='created_at',
            type_='DAY'),
        clustering_fields=['crawler', 'lang']
    )

    table_name = '{}.{}.{}'.format(
        GOOGLE_CLOUD_PROJECT, DATASET, TABLENAME
    )
    load_job = db.load_table_from_json(data, table_name, job_config=job_config)
    load_job.result()

def _get_field_schema(field: dict):
    """Submethod to parse a single field of a schema.
    
    Default values for the most important keys are set.

    If the field to be parsed is a RECORD, it is parsed recursively.

    Parameters
    ----------
    field: dict
        Field to be parsed.
    """

    name = field.get('name', 'undefined')
    description = field.get('description', '')
    field_type = field.get('type', 'STRING')
    mode = field.get('mode', 'NULLABLE')
    fields = field.get('fields', [])

    subschema = []
    if fields:
        for f in fields:
            fields_res = _get_field_schema(f)
            subschema.append(fields_res)

    field_schema = bigquery.SchemaField(
        name=name,
        description=description,
        field_type=field_type,
        mode=mode,
        fields=subschema
    )
    return field_schema

def parse_bq_json_schema(schema: List[dict]):
    """Method which parses a schema passed as a parameter.

    Parameters
    ----------
    schema: list[dict]
        Schema to be parsed.
    """

    output = []
    for field in schema:
        output.append(_get_field_schema(field))

    return output

def get_by_ids(db: bigquery.Client, ids: List[int]):
    """Method which retrieves from a BigQuery table the tweets contained in
    the list given as a parameter.

    Parameters
    ----------
    db: google.cloud.bigquery.Client
        BigQuery client used to create the connection and retrieve the data.
    ids: list[int]
        List of ids to retrieve.
    """

    if not ids:
        return []
    formatted_ids = '({})'.format(', '.join(map(str, ids)))
    query = """
SELECT
    ANY_VALUE(created_at) AS created_at,
    ANY_VALUE(text) AS text,
    ANY_VALUE(interactions) AS interactions
FROM `{}.{}.{}`
WHERE
    id IN  {}
    AND created_at >= DATE_SUB(CURRENT_DATE(), INTERVAL 8 DAY)
    AND created_at <= DATE_ADD(CURRENT_DATE(), INTERVAL 1 DAY)
GROUP BY id
""".format(GOOGLE_CLOUD_PROJECT, DATASET, TABLENAME, formatted_ids)
    query_job = db.query(query, location='EU')
    records = list(map(dict, query_job))
    for record in records:
        record['created_at'] = record['created_at'].strftime(
            '%Y-%m-%d %H:%M:%S')
    return records