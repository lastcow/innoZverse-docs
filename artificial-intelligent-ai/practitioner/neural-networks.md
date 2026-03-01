# Neural Networks

## How Neural Networks Work

```
Input Layer   Hidden Layer 1   Hidden Layer 2   Output Layer
[x1]  ───┐                                      
[x2]     ├─→ [neurons] ──→ [neurons] ──→ [prediction]
[x3]  ───┘

Each connection has a weight. Training adjusts weights to minimize error.
```

## PyTorch — Build a Neural Network

```python
import torch
import torch.nn as nn
import torch.optim as optim

# Define model
class MLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x):
        return self.network(x)

# Instantiate
model = MLP(input_dim=20, hidden_dim=128, output_dim=2)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# Training loop
for epoch in range(100):
    model.train()
    optimizer.zero_grad()
    outputs = model(X_train_tensor)
    loss = criterion(outputs, y_train_tensor)
    loss.backward()
    optimizer.step()

    if epoch % 10 == 0:
        print(f"Epoch {epoch}, Loss: {loss.item():.4f}")

# Inference
model.eval()
with torch.no_grad():
    predictions = model(X_test_tensor)
    predicted_classes = predictions.argmax(dim=1)
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Activation** | ReLU, Sigmoid, Tanh — adds non-linearity |
| **Loss Function** | MSE (regression), CrossEntropy (classification) |
| **Optimizer** | SGD, Adam — update weights |
| **Learning Rate** | Step size for weight updates |
| **Batch Size** | Samples processed before weight update |
| **Epoch** | One full pass through training data |
| **Dropout** | Randomly zero neurons — prevents overfitting |
| **Batch Norm** | Normalize layer inputs — speeds training |
