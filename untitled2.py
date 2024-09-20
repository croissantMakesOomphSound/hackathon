import torch

# Model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Images
imgs = [r"C:\Users\TMpub\OneDrive\Desktop\toy.jpeg"]  # local image path

# Inference
results = model(imgs)

# Results
results.print()
results.save()  # or .show()

# Get predictions
predictions_tensor = results.xyxy[0]  # img1 predictions (tensor)
predictions_pandas = results.pandas().xyxy[0]  # img1 predictions (pandas)
