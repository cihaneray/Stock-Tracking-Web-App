import json
import time
import paramiko
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


def close_python(h, u, f_):
    client_ = paramiko.SSHClient()

    client_.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client_.load_system_host_keys()

    client_.connect(hostname=h, username=u, key_filename=f_)

    client_.exec_command("pkill -f crm.py")

    client_.close()


with open(".secret", "r", encoding="utf-8") as f:
    secrets = json.load(f)
access_key_id = secrets["access_key_id"]
secret_access_key = secrets["secret_access_key"]
region_name = secrets["region_name"]

# Specify the AMI ID (Amazon Machine Image) and other instance details
ami_id = '' # Write ami id
instance_type = '' # Write instance type
key_name = '' # Write key name

# Create an EC2 client object
ec2 = boto3.client('ec2', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region_name)
instance_id = '' # Write instance id 
# Describe the instance with the given ID
try:
    print("Instance Already Running", end=" IP: ")
    response_ = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = response_['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print(public_ip)
except KeyError as k:
    print("Instance Stopped")
    print("Instance Starting")
    print("Please wait")
    response = ec2.start_instances(InstanceIds=[instance_id])  
    response_ = ec2.describe_instances(InstanceIds=[instance_id])
    while response_['Reservations'][0]['Instances'][0]['State']['Name'] != 'running':
        print(response_['Reservations'][0]['Instances'][0]['State']['Name'])
        time.sleep(10)
        response_ = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = response_['Reservations'][0]['Instances'][0]['PublicIpAddress']
    print("Instance Running Ip Address: ", public_ip)


ec2_host = public_ip
ec2_username = '' # Write user name
key_file = '' # Write key file

try:
    client = paramiko.SSHClient()

    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.load_system_host_keys()

    client.connect(hostname=ec2_host, username=ec2_username, key_filename=key_file)

    command = 'cd YagmurTeknoloji\ncd crm\npython3 crm.py'
    # Print the output of the command
    stdin, stdout, stderr = client.exec_command(command)
    while True:
        inp = input('Sunucuyu kapatmak için lütfen "kapat" yazın.')
        if inp == 'kapat':
            client.close()
            close_python(ec2_host, ec2_username, key_file)
            break

except Exception as e:
    print(f"An error occurred: {str(e)}")
