from sys import stdout
from django.views.generic import CreateView
from .models import Upload
import boto3
import time
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
import subprocess

fs = FileSystemStorage(location='C:\\Users\\JM\\Videos\\Captures')

dynamodb = boto3.resource('dynamodb', region_name='ap-south-1',aws_access_key_id='AKIAYFEE5XXYQTCNNGHH',aws_secret_access_key='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')
client = boto3.client('dynamodb', region_name='ap-south-1',aws_access_key_id='AKIAYFEE5XXYQTCNNGHH',aws_secret_access_key='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')


class UploadView(CreateView):
    model = Upload
    fields = ["file"]
    template_name = 'files/upload.html'
    success_url = "/"



def getfile(request):
    file=request.FILES['file']
    filename=fs.save(file.name,file)
    process = subprocess.Popen(
    ['ccextractorwinfull', '-stdout', '-quiet', 'C:\\Users\\JM\\Videos\\Captures\\'+filename],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = ""
    while True:
        out_line = process.stdout.readline()
        output=output+(out_line.decode())
        if out_line == b'': 
            break
    return output
       



def dynamoDB(request):
    out=getfile(request)
    print(out)
    table_name = 'table'

    existing_tables = client.list_tables()['TableNames']

    if table_name not in existing_tables:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                },
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                },

            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        time.sleep(5)

    table = dynamodb.Table(table_name)

    name_with_extension = request.FILES['file'].name.split('.')
    file_name = name_with_extension[0]
    if len(name_with_extension) > 1:
        file_extension = name_with_extension[1]
    else:
        file_extension = "no extension"
    
    table.put_item(
        Item={
                'name': file_name,
                'extension': 'srt',
                'captions':out,
            }
    )

    return UploadView.as_view()(request)
