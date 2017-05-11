import urllib.request
import cv2
import numpy as np
import os

def store_raw_images():
#  neg_images_link = 'http://image-net.org/api/text/imagenet.synset.geturls?wnid=n04334599'
#  neg_image_urls = urllib.request.urlopen(neg_images_link).read().decode()
  neg_images_file = open('neg_links_2.txt','r')

  print('loaded')
  if not os.path.exists('neg'):
    os.makedirs('neg')

  pic_num = 787
#neg_image_urls.split('\n'):
  for i in neg_images_file.readlines():
    try:
      print(i)
      urllib.request.urlretrieve(i, "neg/"+str(pic_num) + '.jpg')
      img = cv2.imread("neg/"+str(pic_num)+'.jpg',cv2.IMREAD_GRAYSCALE)
      resized_img = cv2.resize(img, (100,100))
      cv2.imwrite("neg/"+str(pic_num)+'.jpg', resized_img)
      pic_num += 1


    except Exception as e:
      print(str(e))

def find_uglies():
  for file_type in ['neg']:
    for img in os.listdir(file_type):
      for ugly in os.listdir('uglies'):
        try:
          current_image_path = str(file_type) + '/' + str(img)
          ugly = cv2.imread('uglies/' + str(ugly))
          question = cv2.imread(current_image_path)
          if ugly.shape == question.shape and not(np.bitwise_xor(ugly,question).any()):
            print('ugly')
            os.remove(current_image_path)

        except Exception as e:
          print(str(e))
      

def create_pos_n_neg():
  for file_type in ['neg']:
    for img in os.listdir(file_type):
      if file_type == 'neg':
        line = file_type + '/' + img + '\n'
        with open('bg.txt','a') as f:
          f.write(line)

create_pos_n_neg()
#store_raw_images()
#find_uglies()
