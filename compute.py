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

db = pymysql.connect("vpdb-cluster.cluster-craaqshtparg.us-west-2.rds.amazonaws.com","roadio","roadio2017","RoadIO")
cur = db.cursor(pymysql.cursors.DictCursor)
s3 = boto3.resource('s3')
#stopsigns_folder = '/home/ubuntu/training/frames'

def produce_dataset_by_video(vidID):
  s3_cli = boto3.client('s3')
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
  cur.execute("SELECT PostalZipCode FROM VIDEO WHERE VideoID = %s" % (vidID,))
  postal_zip = cur.fetchone()["PostalZipCode"]
  data = dict()
  data["name"] = dataset_name
  data["images"] = list()
  cur.execute("SELECT * FROM IMAGE I WHERE VideoID = %s" % (vidID,))
  for row in cur.fetchall():
    image = dict()
    image["name"] = row["Name"]
    image["postal_code"] = postal_zip
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
  
  



def analyze():
  stopsign_detector = dlib.simple_object_detector("detector.svm")
  vid = 'teststop.mp4'
  vidID = ""
  try:
    cur.execute("INSERT INTO VIDEO (Name, Duration, PostalZipCode) VALUES ('%s',%s,'%s')" % (vid,3600,"98105"))
    db.commit()
    vidID = cur.lastrowid
    print("vidid" + str(vidID))
  except e:
    print(e)
    db.rollback()
    db.close()
    exit()
  cap = cv2.VideoCapture(vid)
  #for f in glob.glob(os.path.join(stopsigns_folder, "*.jpg")):
  img_num = 1
  frameRate = cap.get(5) #frame rate
  while(cap.isOpened()):
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
      print("not yet")
      continue
    #win = dlib.image_window()
    print("Processing file: {}".format(img))
    #img = io.imread(f)
    stop_dets = stopsign_detector(img)
    print("Number of stopsigns detected: {}".format(len(stop_dets)))
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
      cur.execute("SELECT ObjectID FROM OBJECT WHERE Name = 'stopsign'")
      StopsignObjectID = cur.fetchone()["ObjectID"]
      print("id" + str(StopsignObjectID))
      for k, d in enumerate(stop_dets):
        print("Detection {}: Overall: {} Left: {} Top: {} Right: {} Bottom: {}".format(
        k, d, d.left(), d.top(), d.right(), d.bottom()))
        try:
          cur.execute("INSERT INTO IMAGE_OBJECT (ImageID, ObjectID, BoundingBoxX, BoundingBoxY, BoundingBoxW, BoundingBoxH) VALUES (%s, %s, %s, %s, %s, %s)" % (imgID, StopsignObjectID, d.left(), d.top(), d.right(), d.bottom()))
      
        #win.clear_overlay()
        #win.set_image(img)
        #win.add_overlay(stop_dets)
        #dlib.hit_enter_to_continue() 
          db.commit()
        except e:
          db.rollback()
          print(e)
    except e:
      db.rollback()
      print(e)
    os.remove(img_name)
  cap.release()
  produce_dataset_by_video(vidID)

analyze()
#produce_dataset_by_video(6)
