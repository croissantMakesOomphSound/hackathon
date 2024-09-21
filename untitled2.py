# -*- coding: utf-8 -*-
"""
Created on Sat Sep 21 00:56:08 2024

@author: TMpub
"""
######## deprecated already merged with temp.py########
import torch
import json
from untitled1 import jsonHANDLER

class aichecker:
    
    def __init__(self,image):
        self.imgs=image
        print("imgs"+imgs)
        image_path = imgs  # Get the first image path from the list
        imagename = image_path.split("\\")[-1] 
    
    def runmodel(self):


    # Model
        model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)


    # Inference
        results = model(self.imgs)

    # Results
        results.print()
        results.save()  # or .show()

    # Get predictions
        predictions_tensor = results.xyxy[0]  # img1 predictions (tensor)
        predictions_pandas = results.pandas().xyxy[0]  # img1 predictions (pandas)
        
        predictions_json = predictions_pandas.to_json(orient='records')

        handler = jsonHANDLER(imagename, self.imgs)

    # Loop through predictions and store them
        for pred in predictions_tensor:
            xmin, ymin, xmax, ymax, conf, cls = pred.tolist()  # Convert tensor to list
            class_name = model.names[int(cls)]  # Get class name from the model
        
        # Create annotation
            handler.createannoatation(
                class_name,
                "rectangle",  # Assuming bounding box shape
                "Detected object",
                int(xmin),
                int(ymin),
                int(xmax),
                int(ymax)
                )

        # Save the JSON and print it
        handler.createjson()
    def resultvalues():
        resultvalues=[]
        restvalues.extend([
       imagename,
       imgs,  # First element of imgs
       title,
       shape,
       desc,
       xmin,
       ymin,
       xmax,
       ymax
   ])
        return restvalues
    def resultimg():
        return results.self.imgs
