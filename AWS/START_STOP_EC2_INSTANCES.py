import sys
import boto3
from botocore.exceptions import ClientError
from prettytable import PrettyTable

instances_list_raw = raw_input('InstanceID: (for multiple seperate with a comma.) ').lower()
action = raw_input('Action: (ON/OFF)')
instances_list = instances_list_raw.split(',')
ec2 = boto3.client('ec2')
table = PrettyTable(['Instance', 'State'])

# Loop through instances in "instance_list" and preform action on them
for instances in instances_list:
    if action == 'ON':
        # Do a dryrun first to verify permissions
        try:
            ec2.start_instances(InstanceIds=[instances], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, run start_instances without dryrun
        try:
            response = ec2.start_instances(InstanceIds=[instances], DryRun=False)
            table.add_row([response['StartingInstances'][0]['InstanceId'].upper(), response['StartingInstances'][0]['CurrentState']['Name'].upper()])
            #print(response['StartingInstances'][0]['CurrentState']['Name'].upper() + ' Instance: ' + response['StartingInstances'][0]['InstanceId'].upper() )

        except ClientError as e:
            print(e)
    else:
        # Do a dryrun first to verify permissions
        try:
            ec2.stop_instances(InstanceIds=[instances], DryRun=True)
        except ClientError as e:
            if 'DryRunOperation' not in str(e):
                raise

        # Dry run succeeded, call stop_instances without dryrun
        try:
            response = ec2.stop_instances(InstanceIds=[instances], DryRun=False)
            table.add_row([response['StoppingInstances'][0]['InstanceId'].upper(), response['StoppingInstances'][0]['CurrentState']['Name'].upper()])
            #print(response['StoppingInstances'][0]['CurrentState']['Name'].upper() + ' Instance: ' + response['StoppingInstances'][0]['InstanceId'].upper() )
        except ClientError as e:
            print(e)
print(table)
