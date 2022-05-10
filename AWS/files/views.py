import json
from sys import stdout
from django.http import HttpResponse
from django.views.generic import CreateView
from .models import Upload
import boto3
import time
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
import subprocess
from django.template import loader
import json
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
    a=set()
    k=1
    while True:
        out_line = process.stdout.readline()
        output=output+(out_line.decode())
        if out_line == b'': 
            break
    c=output.count('\r\r\n\r\r\n')
    process.kill()
    while k<c :
        row=""
        if k==1:
            inn=output.index(str(k)+'\r\r\n')
        if k!=1:
            inn=output.index('\r\r\n'+str(k)+'\r\r\n')
        
        if k<c:
            inn2=output.index('\r\r\n\r\r\n'+str(k+1))
        if k==c-1:
            inn2=output.rindex('\r\r\n')
        for char in output[inn:inn2:]:
            row=row+char
        print(row)
        a.add(row)
        k=k+1
    return a
       

def dynamoDB(request):
    out=getfile(request)
    
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
    # if len(name_with_extension) > 1:
    #     file_extension = name_with_extension[1]
    # else:
    #     file_extension = "no extension"
    
    table.put_item(
        Item={
                'name': file_name,
                'extension': 'srt',
                'captions':out,
            }
    )

    return UploadView.as_view()(request)

def search(request):
    template = loader.get_template('./files/search.html')
    context = {}
    params = retrieve_all_get_parameters(request)
    srtfile = getsrt(params)
    context = {
      'srt' : srtfile
    }
    return HttpResponse(template.render(context, request))

def retrieve_all_get_parameters(request):

    param = {}
    captions = request.GET.get('captions')
  
    if captions != None:
        param['srt'] = captions

    return param

def getsrt(param):
    try:
        table = dynamodb.Table('table')
    except :
       
        return 'failed'
    else:
        response = table.scan()
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            try:
                item = response['Item']
            except KeyError:
                return None
            return item