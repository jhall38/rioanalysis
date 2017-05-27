import os
import sys
import glob
import numpy as np
import cv2
import math
import dlib
from skimage import io
import boto3
import pymysql
import zipfile
import datetime
import json
import time
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText


db = pymysql.connect("vpdb-cluster.cluster-craaqshtparg.us-west-2.rds.amazonaws.com","roadio","roadio2017","RoadIO")
cur = db.cursor(pymysql.cursors.DictCursor)
s3 = boto3.resource('s3')
sqs = boto3.resource('sqs')
queue = sqs.get_queue_by_name(QueueName='video-processing')
s3_cli = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def produce_dataset_by_video(vidID):
  try:
    cur.execute("INSERT INTO DATASET (DatetimeCreated) VALUES (NOW())")
    db.commit()
  except e:
    db.rollback()
    print(e)
    exit()
  dataset_id = cur.lastrowid
  dataset_name = "dataset" + str(dataset_id) + ".zip"
  zip_archive = zipfile.ZipFile(dataset_name, "w")
  licence = 5.0
  cur.execute("SELECT CountryAbv FROM VIDEO WHERE VideoID = %s" % (vidID,))
  country = cur.fetchone()["CountryAbv"]
  data = dict()
  data["name"] = dataset_name
  data["images"] = list()
  cur.execute("SELECT * FROM IMAGE I WHERE VideoID = %s" % (vidID,))
  for row in cur.fetchall():
    image = dict()
    image["name"] = row["Name"]
    image["country"] = country
    cur.execute("SELECT * FROM IMAGE_OBJECT WHERE ImageID = %s" % (row["ImageID"],))
    if cur.rowcount != 0:
      image["objects"] = list()
      for obj_row in cur.fetchall():
        obj = dict()
        obj["id"] = obj_row["ObjectID"]
        cur.execute("SELECT Name, Value FROM OBJECT WHERE ObjectID = %s" % (obj_row["ObjectID"],))
        obj_info = cur.fetchone()
        obj["name"] = obj_info["Name"]
        obj["bounding_box_x"] = obj_row["BoundingBoxX"]
        obj["bounding_box_y"] = obj_row["BoundingBoxY"]
        obj["bounding_box_h"] = obj_row["BoundingBoxW"]
        obj["bounding_box_w"] = obj_row["BoundingBoxW"]
        image["objects"].append(obj)
        licence += float(obj_info["Value"]) * 2.65
    data["images"].append(image)
    s3_cli.download_file('dashcam-images', row["Name"], row["Name"])
    this_img = open(row["Name"], "rb")
    zip_archive.writestr(row["Name"], this_img.read())
    os.remove(row["Name"])
  data["licence_fee"] = licence
  try:
    cur.execute("UPDATE DATASET SET Name = '%s', LicenceFee = %s WHERE DatasetID = %s" % (dataset_name, licence, dataset_id))
    datasetTable = dynamodb.Table('dataset')
    datasetTable.put_item(
      Item={
        'country': country,
        'datasetName': dataset_name,
        'licence': licence,
        'dateAdded': datetime.datetime.now().isoformat()
      }
    ) 
    db.commit()
  except e:
    db.rollback()
    print(e)
    exit()
  with open('data.json', 'w') as fp:
    json.dump(data, fp)
  with open('data.json', 'rb') as fp:
    zip_archive.writestr('data.json', fp.read())
  zip_archive.close()
  with open(dataset_name, 'rb') as zi:
    s3.Bucket('roadio-datasets').put_object(Key=dataset_name, Body=zi)
  os.remove(dataset_name)

def analyze(vidKey, userID, identityID, country):
  #totalValue = 3.4444
  #efw = open("message.txt","w+")
  #efw.write("Congrats! Your video was successfully proccessed! $%s has been added to your Road.IO account.\n\nRegards,\nRoad.IO\m\"A safer world starting from your dashcam\"" % (str(Decimal(str(round(totalValue,2)))),))
  #efw.close()
  #efp = open("message.txt", 'r')
  #msg = MIMEText(efp.read())
  #efp.close()
  ##msg['Subject'] = 'Your video has been proccessed!'
  #msg['From'] = 'road.io@gmail.com'
  #userTable = dynamodb.Table('user')
  #response = userTable.get_item(
  #  Key={
  #    'user_id': userID
  #  }
  #)
  #print(response)
  #msg['To'] = response['Item']['email']
  #s = smtplib.SMTP('localhost')
  #s.sendmail(me, [you], msg.as_string())
  #s.quit()
  
  stopsign_detector = dlib.simple_object_detector("detector.svm")
  s3_cli.download_file('driver-videos', identityID + '/' + vidKey, vidKey)
  #vid = 'teststop.mp4'
  vidID = ""
  try:
    cur.execute("INSERT INTO VIDEO (Name, Duration, CountryAbv) VALUES ('%s',%s,'%s')" % (vidKey,0,country))
    db.commit()
    vidID = cur.lastrowid
    print("vidid" + str(vidID))
  except e:
    print(e)
    db.rollback()
    db.close()
    exit()
  cap = cv2.VideoCapture(vidKey)
  img_num = 1
  frame_num = 0
  frameRate = cap.get(5) #frame rate
  totalValue = 1.00
  win = dlib.image_window()
  while(cap.isOpened()):
    frame_num += 1
    frameId = cap.get(1) #current frame number
    ret, img = cap.read()
    try:
      b,g,r = cv2.split(img)
    except:
      break
    img = cv2.merge([r,g,b])
    if ret != True:
      break
    if (frameId % math.floor(frameRate) != 0):
      continue
    print("Processing file: {}".format(img))
    stop_dets = stopsign_detector(img)
    print("Number of stopsigns detected: {}".format(len(stop_dets)))
    win.clear_overlay()
    win.set_image(img)  
    r,g,b = cv2.split(img)
    img = cv2.merge([b,g,r])
    img_name = str(vidID) + '_' + str(frameId) + '.jpg'
    cv2.imwrite(img_name, img)
    data = open(img_name, 'rb')
    try:
      cur.execute("INSERT INTO IMAGE (Name, VideoID) VALUES ('%s',%s)" % (img_name,vidID))
      db.commit()
      s3.Bucket('dashcam-images').put_object(Key=img_name, Body=data)
      imgID = cur.lastrowid
      cur.execute("SELECT ObjectID, Value FROM OBJECT WHERE Name = 'stopsign'")
      cur_obj = cur.fetchone()
      StopsignObjectID = cur_obj["ObjectID"]
      obj_val = cur_obj["Value"]
      print("id" + str(StopsignObjectID))
      for k, d in enumerate(stop_dets):
        print("Detection {}: Overall: {} Left: {} Top: {} Right: {} Bottom: {}".format(
        k, d, d.left(), d.top(), d.right(), d.bottom()))
        win.add_overlay(stop_dets)
        try:
          cur.execute("INSERT INTO IMAGE_OBJECT (ImageID, ObjectID, BoundingBoxX, BoundingBoxY, BoundingBoxW, BoundingBoxH) VALUES (%s, %s, %s, %s, %s, %s)" % (imgID, StopsignObjectID, d.left(), d.top(), d.right(), d.bottom())) 
          totalValue += float(obj_val)
          db.commit()
        except e:
          db.rollback()
          print(e)
    except e:
      db.rollback()
      print(e)
    os.remove(img_name)
  cap.release()
  os.remove(vidKey)
  paymentTable = dynamodb.Table('driverPayments')
  paymentTable.put_item(
    Item={
      'userID': userID,
      'timestamp': datetime.datetime.now().isoformat(),
      'amount': Decimal(str(round(totalValue,2))),
      'vidName' : vidKey
    }
  )
  duration = int(frame_num / frameRate)
  try:
    cur.execute("UPDATE VIDEO SET Duration = %s WHERE VideoID = %s" % (duration, int(vidID)))
    videoTable = dynamodb.Table('videos')
    videoTable.update_item(
      Key={
        'userID': userID,
        'vidID': vidKey
      },
      UpdateExpression="set #dur = :dur",
      ExpressionAttributeValues={
        ':dur': duration
      },
      ExpressionAttributeNames = {
        '#dur': 'duration'
      }
    )
    db.commit()
  except e:
    db.rollback()
    print(e)
  produce_dataset_by_video(vidID)

#analyze()
#produce_dataset_by_video(6)
while True:
  print("Polling messages...")
  for message in queue.receive_messages(MessageAttributeNames=['VidKey', 'IdentityID', 'CountryAbv']):
    vidKey = message.message_attributes.get('VidKey').get('StringValue')
    userID = vidKey.split('|')[0]
    identityID = message.message_attributes.get('IdentityID').get('StringValue')
    country = message.message_attributes.get('CountryAbv').get('StringValue')
    print("proccessing %s by user %s" % (vidKey, userID)) 
    analyze(vidKey, userID, identityID, country)
    message.delete()
  time.sleep(2)

  

