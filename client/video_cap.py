import sys
import cPickle
import datetime
import cv2
import boto3
import time
import cPickle
from multiprocessing import Pool
import pytz
import json

rekog_client = boto3.client("rekognition")

camera_index = 0 # 0 is usually the built-in webcam
capture_rate = 500 # Frame capture rate.. every X frames. Positive integer.

def send_frame(frame, frame_count):
    try:
        #collection_id = "face-collection"
        collection_id = get_global_params()["CollectionId"]

        retval, buff = cv2.imencode(".jpg", frame)

        img_bytes = bytearray(buff)

        utc_dt = pytz.utc.localize(datetime.datetime.now())
        now_ts_utc = (utc_dt - datetime.datetime(1970, 1, 1, tzinfo=pytz.utc)).total_seconds()

        frame_package = {
            'ApproximateCaptureTime' : now_ts_utc,
            'FrameCount' : frame_count,
            'ImageBytes' : img_bytes
        }

        index_faces_response = rekog_client.index_faces(
            CollectionId=collection_id,
            Image={
                'Bytes': img_bytes
            },
            #ExternalImageId='string',
            DetectionAttributes=[
                'DEFAULT'
            ],
            MaxFaces=5,
            QualityFilter='AUTO'
        )
        #print response

        faces_to_delete = []
        #Iterate on rekognition face records. Enrich and prep them for storage in DynamoDB
        for face_record in index_faces_response['FaceRecords']:

            search_response = rekog_client.search_faces(
                CollectionId=collection_id,
                FaceId=face_record['Face']['FaceId'],
                #did not check, but I think it is not supported in python's sdk, judging by prior experience with index_faces
                MaxFaces=2,
                FaceMatchThreshold=70
            )

            face_record['isNew'] = True

            if len(search_response['FaceMatches']) > 0:
                face_record['isNew'] = False

            if len(search_response['FaceMatches']) > 1:
                print 'search of similar faces responded more than one face instances'

            for found_face in search_response['FaceMatches']:
                if found_face['Face']['Confidence'] > face_record['Face']['Confidence']:
                    #delete new face, and change it to old Convert
                    faces_to_delete.append(face_record['Face']['FaceId'])
                    face_record['Face']['FaceId'] = found_face['Face']['FaceId']
                else:
                    #delete old face
                    faces_to_delete.append(found_face['Face']['FaceId'])

            if face_record['isNew']:
                print 'New Face is Found'

        #delete unnecessary faces_to_delete
        if len(faces_to_delete) > 0:
            delete_response=rekog_client.delete_faces(CollectionId=collection_id,
                           FaceIds=faces_to_delete)
        print 'face duplicates were deleted'
    except Exception as e:
        print e

def main():

    argv_len = len(sys.argv)

    if argv_len > 1 and sys.argv[1].isdigit():
        capture_rate = int(sys.argv[1])

    cap = cv2.VideoCapture(0) #Use 0 for built-in camera. Use 1, 2, etc. for attached cameras.
    pool = Pool(processes=3)

    frame_count = 0
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        #cv2.resize(frame, (640, 360));

        if ret is False:
            break

        if frame_count % capture_rate == 0:
            result = pool.apply_async(run_local_implementation, (frame, frame_count))

        frame_count += 1

        # Display the resulting frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # When everything done, release the capture
    cap.release()
    cv2.destroyAllWindows()
    return

if __name__ == '__main__':
    main()
