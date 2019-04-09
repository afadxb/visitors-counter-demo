import os
import shutil
import time
from pynt import task
import boto3
import botocore
from botocore.exceptions import ClientError
import json
from subprocess import call

def read_json(jsonf_path):

    with open(jsonf_path, 'r') as jsonf:
        json_text = jsonf.read()
        return json.loads(json_text)

def get_global_params(**kwargs):

    global_params_path = kwargs.get("global_params_path", "config/global-params.json")
    return read_json(global_params_path)

@task()
def videocaptureip(videouri, capturerate="30", clientdir="client/"):

    call(["python", clientdir+"video_cap_ipcam.py", videouri, capturerate])
    return

@task()
def videocapture(capturerate="30",clientdir="client/"):

    call(["python", clientdir+"video_cap.py", capturerate])
    return

@task()
def createcollection(**kwargs):

    client=boto3.client('rekognition')
    collection_id = get_global_params()["CollectionId"]

    print('Creating collection:' + collection_id)
    response=client.create_collection(CollectionId=collection_id)
    print('Collection ARN: ' + response['CollectionArn'])
    print('Status code: ' + str(response['StatusCode']))
    print('Done...')

@task()
def listcollections(**kwargs):

    maxResults=2
    client=boto3.client('rekognition')
    collection_id = get_global_params()["CollectionId"]

    #Display all the collections
    print('Displaying collections...')
    response=client.list_collections(MaxResults=maxResults)
    while True:
        collections=response['CollectionIds']

        for collection in collections:
            print (collection)

        if 'NextToken' in response:
            nextToken=response['NextToken']
            response=client.list_collections(NextToken=nextToken,MaxResults=maxResults)

        else:
            break

    print('done...')

@task()
def collectionexists(**kwargs):

        maxResults=2
        client=boto3.client('rekognition')
        collection_id = get_global_params()["CollectionId"]

        response=client.list_collections(MaxResults=maxResults)
        while True:
            collections=response['CollectionIds']

            if collection_id in collections:
                return True

            if 'NextToken' in response:
                nextToken=response['NextToken']
                response=client.list_collections(NextToken=nextToken,MaxResults=maxResults)

            else:
                break

        return False

@task()
def describecollection(**kwargs):

    client=boto3.client('rekognition')
    collection_id = get_global_params()["CollectionId"]

    print('Attempting to describe collection ' + collection_id)

    try:
        response=client.describe_collection(CollectionId=collection_id)
        print("Collection Arn: "  + response['CollectionARN'])
        print("Face Count: "  + str(response['FaceCount']))
        print("Face Model Version: "  + response['FaceModelVersion'])
        print("Timestamp: "  + str(response['CreationTimestamp']))

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print ('The collection ' + collection_id + ' was not found ')
        else:
            print ('Error other than Not Found occurred: ' + e.response['Error']['Message'])
    print('Done...')

@task()
def deletecollection(**kwargs):

    collection_id = get_global_params()["CollectionId"]

    print('Attempting to delete collection ' + collection_id)
    client=boto3.client('rekognition')
    statusCode=''
    try:
        response=client.delete_collection(CollectionId=collection_id)
        statusCode=response['StatusCode']

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print ('The collection ' + collection_id + ' was not found ')
        else:
            print ('Error other than Not Found occurred: ' + e.response['Error']['Message'])
        statusCode=e.response['ResponseMetadata']['HTTPStatusCode']
    print('Operation returned Status Code: ' + str(statusCode))
    print('Done...')

@task()
def startawsdemo():

    deletecollection()
    createcollection()
    videocapture()
