# Copyright 2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# Licensed under the Amazon Software License (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at
#     http://aws.amazon.com/asl/
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions and limitations under the License.

from __future__ import print_function
import base64
import datetime
import time
import decimal
import uuid
import json
import cPickle
import boto3
import pytz
from pytz import timezone
from copy import deepcopy

def replace_floats(obj):
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            obj[i] = replace_floats(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.iterkeys():
            obj[k] = replace_floats(obj[k])
        return obj
    elif isinstance(obj, float):
        return int(obj)
    else:
        return obj

def load_config():
    '''Load configuration from file.'''
    with open('imageprocessor-params.json', 'r') as conf_file:
        conf_json = conf_file.read()
        return json.loads(conf_json)

def convert_ts(ts, config):
    '''Converts a timestamp to the configured timezone. Returns a localized datetime object.'''
    #lambda_tz = timezone('US/Pacific')
    tz = timezone(config['timezone'])
    utc = pytz.utc

    utc_dt = utc.localize(datetime.datetime.utcfromtimestamp(ts))

    localized_dt = utc_dt.astimezone(tz)

    return localized_dt


def process_image(event, context):

    collection_id = 'face-collection'

    #Initialize clients
    rekog_client = boto3.client('rekognition')
    sns_client = boto3.client('sns')
    s3_client = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')

    #Load config
    config = load_config()

    s3_bucket = config["s3_bucket"]
    s3_key_frames_root = config["s3_key_frames_root"]

    ddb_table = dynamodb.Table(config["ddb_table"])

    rekog_min_conf = float(config["rekog_min_conf"])

    #Iterate on frames fetched from Kinesis
    for record in event['Records']:

        frame_package_b64 = record['kinesis']['data']
        frame_package = cPickle.loads(base64.b64decode(frame_package_b64))

        img_bytes = frame_package["ImageBytes"]
        approx_capture_ts = frame_package["ApproximateCaptureTime"]
        frame_count = frame_package["FrameCount"]

        now_ts = time.time()

        frame_id = str(uuid.uuid4())
        processed_timestamp = decimal.Decimal(now_ts)
        approx_capture_timestamp = decimal.Decimal(approx_capture_ts)

        now = convert_ts(now_ts, config)
        year = now.strftime("%Y")
        mon = now.strftime("%m")
        day = now.strftime("%d")
        hour = now.strftime("%H")

        rekog_response = rekog_client.index_faces(
            CollectionId=collection_id,
            Image={
                'Bytes': img_bytes
            },
            #ExternalImageId='string',
            DetectionAttributes=[
                'DEFAULT'
            ],
            #These two below require higher boto3 version, but python SDK does not support it yet
            #maximum number of the first biggest faces to return
            #MaxFaces=123,
            #QualityFilter is turned on by default
            #QualityFilter='AUTO'
        )

        faces_to_delete = []
        #Iterate on rekognition face records. Enrich and prep them for storage in DynamoDB
        for face_record in rekog_response['FaceRecords']:

            search_response = rekog_client.search_faces(
                CollectionId=collection_id,
                FaceId=face_record['Face']['FaceId'],
                #did not check, but I think it is not supported in python's sdk, judging by prior experience with index_faces
                MaxFaces=1,
                FaceMatchThreshold=90
            )

            face_record['isNew'] = True

            for found_face in search_response['FaceMatches']:

                if found_face['Face']['Confidence'] > face_record['Face']['Confidence']:
                    #delete new face, and change it to old Convert
                    faces_to_delete.append(face_record['Face']['FaceId'])
                    face_record['Face']['FaceId'] = found_face['Face']['FaceId']

                else:
                    #delete old face
                    faces_to_delete.append(found_face['Face']['FaceId'])
                face_record['isNew'] = False

            conf = face_record['Face']['Confidence']

            #delete unnecessary faces_to_delete
            delete_response=rekog_client.delete_faces(CollectionId=collection_id,
                               FaceIds=faces_to_delete)

        #Store frame image in S3
        s3_key = (s3_key_frames_root + '{}/{}/{}/{}/{}.jpg').format(year, mon, day, hour, frame_id)

        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=img_bytes
        )

        #Persist frame data in dynamodb

        item = {
            'frame_id': frame_id,
            'processed_timestamp' : processed_timestamp,
            'approx_capture_timestamp' : approx_capture_timestamp,
            'rekog_face_records' : rekog_response['FaceRecords'],
            'rekog_orientation_correction' :
                rekog_response['OrientationCorrection']
                if 'OrientationCorrection' in rekog_response else 'ROTATE_0',
            'processed_year_month' : year + mon, #To be used as a Hash Key for DynamoDB GSI
            's3_bucket' : s3_bucket,
            's3_key' : s3_key
        }

        replace_floats(item)

        ddb_table.put_item(Item=item)

    print('Successfully processed {} records.'.format(len(event['Records'])))
    return

def handler(event, context):
    return process_image(event, context)
