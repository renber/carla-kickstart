import os
from typing import List

import cv2
import numpy as np

class DetectedObject:

    def __init__(self, rect, class_name):
        self.rect = rect
        self.class_name = class_name

    def __repr__(self):
        return f"'{self.class_name}' at ({self.rect[0]}, {self.rect[1]}) with size ({self.rect[2]}, {self.rect[3]})"

class ObjectDetectionSensor():
    """
    Sensor which runs object detection using YOLO
    """

    def __init__(self):
        model_weights = 'yolo/yolov3.cfg'
        model_cfg = 'yolo/yolov3.weights'
        self.net = cv2.dnn.readNet(model_weights, model_cfg)
        #self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        #self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

        self.classes = []
        with open("yolo/coco.names", "r") as f:
            self.classes = [line.strip() for line in f.readlines()]

        self.output_layers = self.net.getUnconnectedOutLayersNames()
        self.colors = np.random.uniform(0, 255, size = (len(self.classes), 3))

    def detect(self, image, image_size) -> List[DetectedObject]:
        width = image_size[0]
        height = image_size[1]

        # Detect image
        blob = cv2.dnn.blobFromImage(image, 1/255, (width, height), (0, 0, 0), True, crop = False)

        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        orig_detections = {}
        detections = []

        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > 0.5:
                    #Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y -h / 2)

                    #if 0 <= x < width and 0 <= y < height:
                    if not class_id in orig_detections:
                        orig_detections[class_id] = []

                    orig_detections[class_id].append( (x, y, w, h) )


        for class_id in orig_detections:
            class_name = self.classes[class_id]
            orig_rects = orig_detections[class_id]
            grouped_rects, weights = cv2.groupRectangles(orig_rects, groupThreshold=1)
            for r in grouped_rects:
                detections.append(DetectedObject( (r[0], r[1], r[2], r[3]) , class_name))

        return detections

