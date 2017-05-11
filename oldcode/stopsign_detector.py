import os
import sys
import glob

import dlib
from skimage import io

stopsigns_folder = '/home/ubuntu/training/stopsigns'

options = dlib.simple_object_detector_training_options()
options.add_left_right_image_flips = True

options.C = 5

options.num_threads = 4
options.be_verbose = True

training_xml_path = os.path.join(stopsigns_folder, "training.xml")
testing_xml_path = os.path.join(stopsigns_folder, "testing.xml")
dlib.train_simple_object_detector(training_xml_path, "detector.svm", options)
print("")  # Print blank line to create gap from previous output

print("Training accuracy: {}".format(
    dlib.test_simple_object_detector(training_xml_path, "detector.svm")))

print("Testing accuracy: {}".format(
    dlib.test_simple_object_detector(testing_xml_path, "detector.svm")))
detector = dlib.simple_object_detector("detector.svm")


print("Showing detections on the images in the faces folder...")
win = dlib.image_window()
for f in glob.glob(os.path.join(stopsigns_folder, "*.jpg")):
    print("Processing file: {}".format(f))
    img = io.imread(f)
    dets = detector(img)
    print("Number of faces detected: {}".format(len(dets)))
    for k, d in enumerate(dets):
        print("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
            k, d.left(), d.top(), d.right(), d.bottom()))

    win.clear_overlay()
    win.set_image(img)
    win.add_overlay(dets)
    dlib.hit_enter_to_continue()



# You just need to put your images into a list.
images = [io.imread(stopsigns_folder + '/2008_002506.jpg'),
          io.imread(stopsigns_folder + '/2009_004587.jpg')]
# Then for each image you make a list of rectangles which give the pixel
# locations of the edges of the boxes.
boxes_img1 = ([dlib.rectangle(left=329, top=78, right=437, bottom=186),
               dlib.rectangle(left=224, top=95, right=314, bottom=185),
               dlib.rectangle(left=125, top=65, right=214, bottom=155)])
boxes_img2 = ([dlib.rectangle(left=154, top=46, right=228, bottom=121),
               dlib.rectangle(left=266, top=280, right=328, bottom=342)])
# And then you aggregate those lists of boxes into one big list and then call
# train_simple_object_detector().
boxes = [boxes_img1, boxes_img2]

detector2 = dlib.train_simple_object_detector(images, boxes, options)
# We could save this detector to disk by uncommenting the following.
#detector2.save('detector2.svm')

# Now let's look at its HOG filter!
win_det.set_image(detector2)
dlib.hit_enter_to_continue()

# Note that you don't have to use the XML based input to
# test_simple_object_detector().  If you have already loaded your training
# images and bounding boxes for the objects then you can call it as shown
# below.
print("\nTraining accuracy: {}".format(
    dlib.test_simple_object_detector(images, boxes, detector2)))
