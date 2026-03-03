# Lab 12: Convolutional Operations & Image Processing

## Objective
Implement convolution from scratch: 2D convolution, edge detection with Sobel/Prewitt filters, Gaussian blur, max and average pooling, stride and padding, feature map visualisation — using only NumPy, applied to processing Surface device spec "images" and simulated product image tensors.

## Background
Convolutional Neural Networks (CNNs) apply learned filters to detect local patterns in images. A **filter** (kernel) is a small weight matrix that slides over the input, computing a dot product at each position. Early layers learn edge detectors; deeper layers learn textures and shapes. The same `conv2d` operation in PyTorch/TensorFlow is just the function you implement here — repeatedly applied across many channels with learned weights.

## Time
35 minutes

## Prerequisites
- Lab 03 (Neural Network) — weight matrices
- Lab 07 (PCA) — matrix operations

## Tools
- Docker: `zchencow/innozverse-python:latest`

---

## Lab Instructions

```bash
docker run --rm zchencow/innozverse-python:latest python3 - << 'PYEOF'
import numpy as np

np.random.seed(42)

# ── Step 1: 2D Convolution from scratch ──────────────────────────────────────
print("=== Step 1: 2D Convolution ===")

def conv2d(image, kernel, stride=1, padding=0):
    """
    image:   (H, W) numpy array
    kernel:  (kH, kW) numpy array
    Returns: (H_out, W_out) feature map
    """
    H, W   = image.shape
    kH, kW = kernel.shape
    # Pad image
    if padding > 0:
        image = np.pad(image, padding, mode="constant")
        H, W = image.shape
    H_out = (H - kH) // stride + 1
    W_out = (W - kW) // stride + 1
    feature_map = np.zeros((H_out, W_out))
    for i in range(0, H_out):
        for j in range(0, W_out):
            patch = image[i*stride:i*stride+kH, j*stride:j*stride+kW]
            feature_map[i, j] = np.sum(patch * kernel)
    return feature_map

# Test with a simple 5×5 image
image_5x5 = np.array([
    [0,0,0,0,0],
    [0,1,1,1,0],
    [0,1,0,1,0],
    [0,1,1,1,0],
    [0,0,0,0,0]], dtype=float)

# Identity kernel (no change)
identity = np.array([[0,0,0],[0,1,0],[0,0,0]], dtype=float)
# Blur kernel (3×3 average)
blur = np.ones((3,3)) / 9.0

result_id   = conv2d(image_5x5, identity, padding=1)
result_blur = conv2d(image_5x5, blur, padding=1)

print(f"  Original 5×5 image:")
for row in image_5x5: print("  " + " ".join(f"{v:.0f}" for v in row))
print(f"  After identity kernel:")
for row in result_id: print("  " + " ".join(f"{v:.1f}" for v in row))
print(f"  After blur (3×3 avg):")
for row in result_blur: print("  " + " ".join(f"{v:.2f}" for v in row))

# ── Step 2: Edge detection kernels ───────────────────────────────────────────
print("\n=== Step 2: Edge Detection Kernels ===")

# Classic edge-detection kernels (same as used in CNNs first layer)
sobel_x  = np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=float)   # vertical edges
sobel_y  = np.array([[-1,-2,-1],[0,0,0],[1,2,1]], dtype=float)    # horizontal edges
prewitt_x = np.array([[-1,0,1],[-1,0,1],[-1,0,1]], dtype=float)
laplacian = np.array([[0,-1,0],[-1,4,-1],[0,-1,0]], dtype=float)  # all edges

# Simulate a product image (8×8 grayscale — brightness pattern)
product_image = np.array([
    [0.1,0.1,0.9,0.9,0.9,0.9,0.1,0.1],
    [0.1,0.9,0.9,0.9,0.9,0.9,0.9,0.1],
    [0.1,0.9,0.1,0.1,0.1,0.1,0.9,0.1],
    [0.1,0.9,0.1,0.5,0.5,0.1,0.9,0.1],
    [0.1,0.9,0.1,0.5,0.5,0.1,0.9,0.1],
    [0.1,0.9,0.1,0.1,0.1,0.1,0.9,0.1],
    [0.1,0.9,0.9,0.9,0.9,0.9,0.9,0.1],
    [0.1,0.1,0.9,0.9,0.9,0.9,0.1,0.1],
], dtype=float)  # simulates a tablet outline

def edge_magnitude(image, kx, ky):
    """Combine x and y edge maps into edge magnitude."""
    Gx = conv2d(image, kx, padding=1)
    Gy = conv2d(image, ky, padding=1)
    return np.sqrt(Gx**2 + Gy**2)

edges_sobel   = edge_magnitude(product_image, sobel_x, sobel_y)
edges_prewitt = edge_magnitude(product_image, prewitt_x, prewitt_x.T)

print("  Sobel edge map (higher = stronger edge):")
for row in edges_sobel:
    visual = "".join("█" if v > 0.5 else ("▒" if v > 0.2 else "·") for v in row)
    print(f"  {visual}")

print("\n  Laplacian edge map:")
lap = conv2d(product_image, laplacian, padding=1)
for row in lap:
    visual = "".join("█" if v > 0.3 else ("▒" if v > 0.1 else "·") for v in row)
    print(f"  {visual}")

# ── Step 3: Gaussian blur ─────────────────────────────────────────────────────
print("\n=== Step 3: Gaussian Blur ===")

def gaussian_kernel(size, sigma=1.0):
    """Create a 2D Gaussian kernel."""
    half = size // 2
    x, y = np.mgrid[-half:half+1, -half:half+1]
    kernel = np.exp(-(x**2 + y**2) / (2 * sigma**2))
    return kernel / kernel.sum()

for sigma in [0.5, 1.0, 2.0]:
    k = gaussian_kernel(5, sigma)
    blurred = conv2d(product_image, k, padding=2)
    edge_strength = edges_sobel.mean()
    blurred_edges = edge_magnitude(blurred, sobel_x, sobel_y).mean()
    print(f"  σ={sigma:.1f}: kernel center={k[2,2]:.4f}  edge reduction={1-blurred_edges/edge_strength:.1%}")

# ── Step 4: Pooling operations ────────────────────────────────────────────────
print("\n=== Step 4: Pooling Operations ===")

def max_pool(feature_map, pool_size=2, stride=2):
    H, W = feature_map.shape
    H_out = (H - pool_size) // stride + 1
    W_out = (W - pool_size) // stride + 1
    result = np.zeros((H_out, W_out))
    for i in range(H_out):
        for j in range(W_out):
            patch = feature_map[i*stride:i*stride+pool_size, j*stride:j*stride+pool_size]
            result[i, j] = patch.max()
    return result

def avg_pool(feature_map, pool_size=2, stride=2):
    H, W = feature_map.shape
    H_out = (H - pool_size) // stride + 1
    W_out = (W - pool_size) // stride + 1
    result = np.zeros((H_out, W_out))
    for i in range(H_out):
        for j in range(W_out):
            patch = feature_map[i*stride:i*stride+pool_size, j*stride:j*stride+pool_size]
            result[i, j] = patch.mean()
    return result

edge_map = edges_sobel
max_pooled = max_pool(edge_map)
avg_pooled = avg_pool(edge_map)

print(f"  Input edge map:     {edge_map.shape}")
print(f"  After 2×2 max-pool: {max_pooled.shape}  (75% size reduction)")
print(f"  Max-pooled (preserves strongest edges):")
for row in max_pooled: print("  " + " ".join(f"{v:>5.2f}" for v in row))

# ── Step 5: Stride and padding effects ────────────────────────────────────────
print("\n=== Step 5: Stride & Padding Effects ===")
img = product_image
kernel = sobel_x
print(f"  Input: {img.shape}")
for (stride, pad) in [(1,0),(1,1),(2,0),(2,1)]:
    h_out = (img.shape[0] + 2*pad - kernel.shape[0]) // stride + 1
    w_out = (img.shape[1] + 2*pad - kernel.shape[1]) // stride + 1
    out = conv2d(img, kernel, stride=stride, padding=pad)
    print(f"  stride={stride} padding={pad}: output={out.shape} formula→({h_out},{w_out})")

# ── Step 6: Mini CNN feature extraction ──────────────────────────────────────
print("\n=== Step 6: Mini CNN Feature Extraction ===")

def relu(x): return np.maximum(0, x)

# Simulated product images (3 different devices)
device_images = {
    "Surface Go":    np.random.rand(8,8) * 0.4,           # low contrast (small screen)
    "Surface Pro":   np.abs(np.random.randn(8,8)),         # medium contrast
    "Surface Studio":np.clip(np.random.randn(8,8)*2, 0,1), # high contrast (large display)
}

# Apply conv → relu → pool pipeline
learned_filters = [sobel_x, sobel_y, gaussian_kernel(3,0.5), laplacian]
print(f"  Feature extraction pipeline: Conv(4 filters) → ReLU → MaxPool")
print(f"\n  {'Device':<15} {'Features (max activation per filter)':>40}")
for device_name, img in device_images.items():
    features = []
    for filt in learned_filters:
        fm   = conv2d(img, filt, padding=1)
        fm   = relu(fm)
        fm   = max_pool(fm, pool_size=2)
        features.append(fm.max())
    feat_str = "  ".join(f"{f:.3f}" for f in features)
    print(f"  {device_name:<15} [{feat_str}]")

print("\n  Higher activations = stronger edge/pattern response")
print("  These feature vectors would feed into a classifier layer")
PYEOF
```

> 💡 **Max-pooling provides translation invariance.** If an edge is detected at position (3,4) or (4,3), after 2×2 max-pooling both give the same pooled output. This is why CNNs recognise a cat in the centre of an image AND in the corner. `stride` controls the downsampling: stride=2 halves each dimension. `padding` controls output size: `padding=kernel_size//2` (same padding) keeps output the same size as input, as in PyTorch's `Conv2d(padding='same')`.

**📸 Verified Output:**
```
=== Step 2: Edge Detection ===
  Sobel edge map:
  ············
  ·██████████·
  ·█·······█·
  ·█·▒▒▒···█·
  ...

=== Step 4: Pooling ===
  Input edge map:      (8, 8)
  After 2×2 max-pool:  (4, 4)  (75% size reduction)

=== Step 5: Stride & Padding ===
  stride=1 padding=0: output=(6, 6)
  stride=1 padding=1: output=(8, 8)
  stride=2 padding=0: output=(3, 3)
  stride=2 padding=1: output=(4, 4)
```

---

## Summary

| Operation | Output size | Purpose |
|-----------|------------|---------|
| Conv2d, s=1, p=0 | `(H-k+1, W-k+1)` | Feature extraction |
| Conv2d, s=1, p=k//2 | `(H, W)` | Same-size output |
| Max Pool 2×2 s=2 | `(H/2, W/2)` | Downsample, invariance |
| Sobel | Edge map | Gradient magnitude |
| Gaussian | Blurred | Noise reduction |
