import boto3
from prettytable import PrettyTable

ec2 = boto3.resource('ec2')
table = PrettyTable(['Instance', 'State'])

### Loop through instances and get ID and state
for instance in ec2.instances.all():
    #print('Instance: ' + instance.id.upper() + '  State: ' + instance.state['Name'].upper())
    table.add_row([instance.id.upper(), instance.state['Name'].upper()])
print(table)
