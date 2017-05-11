import numpy as np
import cv2

stopsign_cascade = cv2.CascadeClassifier('data/cascade.xml')

cap = cv2.VideoCapture('sample_street_stopsign1.mov')
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640,480))
while(cap.isOpened()):
    ret, img = cap.read()
    try:
      gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
      # add this
      # image, reject levels level weights.
      stopsigns = stopsign_cascade.detectMultiScale(gray, 50, 50)
    
      # add this
      for (x,y,w,h) in stopsigns:
          cv2.rectangle(img,(x,y),(x+w,y+h),(255,255,0),2)        

      #cv2.imshow('img',img)
      out.write(img)
      k = cv2.waitKey(30) & 0xff
      if k == 27:
        break
    except Exception as e:
      print(str(e))

cap.release()
out.release()
cv2.destroyAllWindows()
