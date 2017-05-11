import numpy as np
import cv2

stopsign_cascade = cv2.CascadeClassifier('data/cascade.xml')

cap = cv2.VideoCapture('test4way.mp4')
#fourcc = cv2.VideoWriter_fourcc(*'XVID')
#out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640,480))
img_num = 1
while(cap.isOpened()):
    ret, img = cap.read()
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # add this
    # image, reject levels level weights.
    stopsigns = stopsign_cascade.detectMultiScale(gray, 30, 30)
    
    # add this
    for (x,y,w,h) in stopsigns:
        cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)        

    #cv2.imshow('img',img)
#    out.write(img)
    cv2.imwrite('frames/frame' + str(img_num) + '.jpg', img)
    k = cv2.waitKey(30) & 0xff
    if k == 27:
        break
    img_num += 1

cap.release()
#out.release()
cv2.destroyAllWindows()
