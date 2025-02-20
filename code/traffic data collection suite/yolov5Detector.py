
from typing import List, Optional, Union
import cv2

import numpy as np
import norfair
from norfair import Detection, Paths, Tracker, Video
import yolov5
import torch
from ultralytics import YOLO
from motpy import Detection, MultiObjectTracker
import colorsys

#import intel_extension_for_pytorch as ipex


from eventCollector import EventCollector


class Yolov5Detector:
    def __init__(self):
        self.device = torch.device("cuda:0")
        self.WALDO = 0
        
        if(self.WALDO):
            self.model = YOLO("/home/nvidia/projects/carTrackerForWindow/videoFromMipi/WALDO30_yolov8m_640x640.pt")
        else:
            self.model = torch.hub.load("ultralytics/yolov5", "yolov5l", "~/").to(self.device) # yolov5.load('ultralytics/yolov5s')

        self.dt = 0.033
        self.tracker = MultiObjectTracker(dt=self.dt)

        self.model.conf = 0.25  # NMS confidence threshold
        self.model.iou = 0.45  # NMS IoU threshold
        self.model.agnostic = False  # NMS class-agnostic
        self.model.multi_label = False  # NMS multiple labels per box
        self.model.max_det = 1000  # maximum number of detections per image
        self.positionDict = {}
        
        self.eventCollector = EventCollector()


    def infere(self, frame):
        
        frame = cv2.resize(frame, (720, 480))
    
        results = self.model(frame)



        listForTracker = []

        if(self.WALDO):
            res = results[0]
            #print(res.boxes.xyxy)
            for box in res.boxes.xyxy:
                print(box)
                x1, y1, x2, y2 = [int(x) for x in box]
                
                color = (0, 255, 0)  # Green color for rectangle
                thickness = 2
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        else:
            detections = results.xyxy[0]  # Detections for the first image (if batch size > 1)
            # Each row is (x1, y1, x2, y2, confidence, class)
            class_names = self.model.names 
            # Iterate through detections
            for *box, conf, cls in detections:
                

                #print(f"Box: {box}, Confidence: {conf}, Class: {cls}, name: {class_names[int(cls)]}")

                name = class_names[int(cls)]

                x1, y1, x2, y2 = map(int, box)  # Convert coordinates to integers
                #class_name = class_names[int(cls)]  # Get class name

                # Draw the rectangle on the image
                if(conf > 0.5):
                    if(name == "car"):
                        color = (0, 255, 0)  # Green color for rectangle
                        listForTracker.append(Detection(box=[x1, y1, x2, y2]))
                        #self.eventCollector.registerEvent("carDetection", {
                        #    "time": self.eventCollector.getTimestamp(),
                        #})
                    else:
                        color = (0, 0, 255)
                    thickness = 2
                    #cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                    
                    # Using cv2.putText() method
                    #frame = cv2.putText(frame, name, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 
                    #1, color, 2, cv2.LINE_AA)


            self.tracker.step(detections=listForTracker)
            tracks = self.tracker.active_tracks()

            trackIdDict = {}
            for track in tracks:
                color = (128, 0, 128)
                x1, y1, x2, y2 = map(int, track.box)
                #print(dir(track))
                trackIdDict[track.id] = 1

                if(track.id in self.positionDict):
                    path = self.positionDict[track.id]
                    p = [(x1+x2)/2, (y1 + y2)/2]
                    p = [int(x) for x in p]
                    path.append(p)
                    for k in range(len(path)-1):
                        dist = np.sqrt((path[k][0] - path[k+1][0])**2 + (path[k][1] - path[k+1][1])**2)
                        dist /= self.dt
                        #print(dist)
                        
                        lim = 600
                        dist = max(0, min(lim, dist))
                        # dist is <0, lim>
                        normDist = dist/lim
                        color = colorsys.hsv_to_rgb(normDist*0.33, 1, 0.8)
                        color = [int(x*255) for x in color]
                        cv2.line(frame, path[k], path[k+1], color, 2)
                else:
                    p = [(x1+x2)/2, (y1 + y2)/2]
                    p = [int(x) for x in p]
                    self.positionDict[track.id] = [p]
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                #frame = cv2.putText(frame, str(track.id), (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 
                #   0.5, color, 1, cv2.LINE_AA)
                #cv2.text()

            keysToRemove = []
            for key in self.positionDict:
                if(not key in trackIdDict):
                    # expired key, remove and analyze
                    path = self.positionDict[key]
                    t = self.eventCollector.getTimestamp()
                    dist = 0
                    for k in range(len(path)-1):
                        dist += np.sqrt((path[k][0] - path[k+1][0])**2 + (path[k][1] - path[k+1][1])**2)
                    avgSpeed = dist / len(path) / self.dt

                    data = {
                        #"path": path,
                        "time": t,
                        "dist": dist,
                        "avgSpeed": avgSpeed
                    }
                    self.eventCollector.registerEvent("finishedTrack", data)

                    keysToRemove.append(key)


            for ke in keysToRemove:
                print("deleting ", ke)
                del self.positionDict[ke]



        return frame