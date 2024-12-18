import json
import time
import paramiko
import webbrowser
import boto3
from botocore.exceptions import ClientError

with open(".secret", "r", encoding="utf-8") as f:
    secrets = json.load(f)
    access_key_id = secrets["access_key_id"]
    secret_access_key = secrets["secret_access_key"]
    region_name = secrets["region_name"]
    url = secrets["url"]
    parameter = secrets["parameter"]
    instance_id = secrets["instance_id"]

ami_id = '' # Write ami_id
instance_type = '' # Write instance type
key_name = '' # Write key name

ec2 = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region_name)

response_ = ec2.describe_instances(InstanceIds=[instance_id])
public_ip = response_['Reservations'][0]['Instances'][0]['PublicIpAddress']
url = url.replace("localhost",public_ip)
webbrowser.open(url)
