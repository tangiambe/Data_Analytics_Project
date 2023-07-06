import json
import pandas as pd
import boto3
import sys
import csv
import logging
import pymysql
from io import StringIO
from etl import data_cleaning
from db_funcs import prep_insert_qry
import rds_conn_info

s3 = boto3.client('s3')

# rds settings
rds_host  = rds_conn_info.rds_host
user_name = rds_conn_info.user_name
password = rds_conn_info.password
db_name = rds_conn_info.db_name

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.
try:
    conn = pymysql.connect(host=rds_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit()

logger.info("SUCCESS: Connection to RDS MySQL instance succeeded")

def depth(L): return (isinstance(L, list) or isinstance(L, tuple)) and max(map(depth, L))+1

def lambda_handler(event, context):
    print(event)#to check the data in event
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    file_name = event["Records"][0]["s3"]["object"]["key"]
    
    file = s3.get_object(Bucket=bucket_name, Key=file_name)
    content = file["Body"].read().decode('utf-8')
    
    if file_name.endswith(".csv"):
        csv_string_io = StringIO(content)
        
        csv_content_df = data_cleaning(pd.read_csv(csv_string_io))
        csv_string_io = StringIO(csv_content_df.to_csv(index=False))
        
        reader = csv.reader(csv_string_io)
        attributes_list = next(reader, None)
        data = [tuple(line) for line in reader]
    elif file_name.endswith(".json"):
        json_content = json.loads(content)
        df_content = pd.DataFrame(json_content, columns = list(json_content.keys()))
        json_content_df = data_cleaning(df_content)

        attributes_list = list(json_content_df.columns)
        data = json_content_df.iloc[0].values.flatten().tolist()
        
    with conn.cursor() as cur:
        query = prep_insert_qry(attributes_list)
        try:
            if depth(data) > 1:
                cur.fast_executemany = True
                cur.executemany(query, data)
            else:
                cur.execute(query, data)
        except pymysql.err.IntegrityError as e:
            pass
        except Exception as e:
            raise e
    conn.commit()
    
    print("Success")    

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }