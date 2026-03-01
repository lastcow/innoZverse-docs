# Computer Vision

## Convolutional Neural Networks (CNNs)

CNNs are specialized for image data. They learn spatial features through convolutional filters.

```python
import torch
import torch.nn as nn

class CNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            # Conv block 1
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),     # 224 → 112

            # Conv block 2
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),     # 112 → 56
        )
        self.classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        return self.classifier(x)
```

## Transfer Learning (Recommended)

Use pretrained models instead of training from scratch:

```python
import torchvision.models as models

# Load pretrained ResNet50
model = models.resnet50(weights='IMAGENET1K_V2')

# Freeze all layers
for param in model.parameters():
    param.requires_grad = False

# Replace final layer for your task
model.fc = nn.Linear(model.fc.in_features, num_classes)

# Only train the new layer
optimizer = torch.optim.Adam(model.fc.parameters(), lr=0.001)
```

## Image Processing with OpenCV

```python
import cv2
import numpy as np

# Read image
img = cv2.imread('image.jpg')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# Resize
img_resized = cv2.resize(img, (224, 224))

# Edge detection
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 100, 200)

# Face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
```
