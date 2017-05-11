import os
import sys
import glob
import numpy as np
import cv2
import math
import dlib
from skimage import io

stopsigns_folder = '/home/ubuntu/training/frames'


detector = dlib.simple_object_detector("detector.svm")

cap = cv2.VideoCapture('teststop.mp4')
#for f in glob.glob(os.path.join(stopsigns_folder, "*.jpg")):
img_num = 1
frameRate = cap.get(5) #frame rate
while(cap.isOpened()):
  frameId = cap.get(1) #current frame number
  ret, img = cap.read()
  b,g,r = cv2.split(img)       # get b,g,r
  img = cv2.merge([r,g,b])
  if ret != True:
    break
  if (frameId % math.floor(frameRate) != 0):
    print("not yet")
    continue
  win = dlib.image_window()
  print("Processing file: {}".format(img))
  #img = io.imread(f)
  dets = detector(img)
  print("Number of stopsigns detected: {}".format(len(dets)))
  for k, d in enumerate(dets):
    print("Detection {}: Overall: {} Left: {} Top: {} Right: {} Bottom: {}".format(
    k, d, d.left(), d.top(), d.right(), d.bottom()))

    win.clear_overlay()
    win.set_image(img)
    win.add_overlay(dets)
    dlib.hit_enter_to_continue()
  r,g,b = cv2.split(img)       # get b,g,r
  img = cv2.merge([b,g,r])
  cv2.imwrite('frames/frame' + str(frameId) + '.jpg', img)
  

cap.release()
