import boto3

# Create IAM client
iam = boto3.client('iam')

# List Access keys for username "Infoblox"
paginator = iam.get_paginator('list_access_keys')
for response in paginator.paginate(UserName='SEARCH_FIELD_HERE'):
    #print(response)
    paginator_response = response

# Loop through response and print only active Keys
for keys in paginator_response['AccessKeyMetadata']:
    if keys['Status'] == 'Active':
print(keys['AccessKeyId'])
