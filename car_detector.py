import os
import sys
import glob

import dlib
from skimage import io

stopsigns_folder = '/home/ubuntu/training/stopsigns'
cars_folder = '/home/ubuntu/training/cars'

options = dlib.simple_object_detector_training_options()
options.add_left_right_image_flips = True

options.C = 5

options.num_threads = 4
options.be_verbose = True

training_xml_path = os.path.join(cars_folder, "mydataset.xml")
testing_xml_path = os.path.join(stopsigns_folder, "testing.xml")
dlib.train_simple_object_detector(training_xml_path, "detector.svm", options)
print("")

print("Training accuracy: {}".format(
    dlib.test_simple_object_detector(training_xml_path, "car_detector.svm")))

print("Testing accuracy: {}".format(
    dlib.test_simple_object_detector(testing_xml_path, "car_detector.svm")))
detector = dlib.simple_object_detector("car_detector.svm")


print("Showing detections on the images in the stopsigns folder...")
win = dlib.image_window()
for f in glob.glob(os.path.join(stopsigns_folder, "*.jpg")):
    print("Processing file: {}".format(f))
    img = io.imread(f)
    dets = detector(img)
    print("Number of stopsigns detected: {}".format(len(dets)))
    for k, d in enumerate(dets):
        print("Detection {}: Left: {} Top: {} Right: {} Bottom: {}".format(
            k, d.left(), d.top(), d.right(), d.bottom()))

    win.clear_overlay()
    win.set_image(img)
    win.add_overlay(dets)
    dlib.hit_enter_to_continue()


print("\nTraining accuracy: {}".format(
    dlib.test_simple_object_detector(images, boxes, detector2)))
