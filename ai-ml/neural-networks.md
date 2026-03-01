# Neural Networks

## How Neural Networks Work

A neural network consists of layers of interconnected nodes (neurons):

```
Input Layer → Hidden Layers → Output Layer
[features]  → [processing]  → [prediction]
```

## PyTorch Example

```python
import torch
import torch.nn as nn

class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.layers(x)

model = SimpleNet()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()
```

## Key Concepts

| Term | Meaning |
|------|---------|
| Epoch | One full pass through training data |
| Batch | Subset of data processed together |
| Learning Rate | How fast the model updates weights |
| Overfitting | Model memorizes training data |
| Dropout | Regularization to prevent overfitting |
