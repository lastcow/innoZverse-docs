# Lab 11: Vision AI — How Machines See the World

## Objective

Understand how AI systems process and generate images. By the end you will be able to:

- Explain how CNNs learn to "see" features in images
- Describe CLIP — the model that connected images and language
- Understand how diffusion models generate images from text
- Identify real-world applications of vision AI

---

## How Machines See

A digital image is a 3D array of numbers: height × width × 3 (RGB channels). A 1080p image is roughly 1920 × 1080 × 3 = **6.2 million numbers**. Vision AI learns patterns in these numbers.

```python
import numpy as np
from PIL import Image

# Load image as numpy array
img = Image.open("cat.jpg").convert("RGB")
pixels = np.array(img)

print(pixels.shape)   # (480, 640, 3)  — height, width, RGB
print(pixels[0, 0])   # [134, 201, 89]  — first pixel: R=134, G=201, B=89
print(pixels.dtype)   # uint8  — values 0-255

# Neural networks normalise to 0-1 or -1 to +1
pixels_norm = pixels / 255.0
```

---

## Convolutional Neural Networks: Learning to See

CNNs learn **filters** — small matrices that detect specific visual patterns when slid across an image.

```
Original image (28×28)          Filter (3×3)
┌──────────────────┐    ×     ┌───────┐     =    Feature map
│  ....####....    │          │-1 0 1 │          (detects vertical edges)
│  ....####....    │          │-1 0 1 │
│  ....####....    │          │-1 0 1 │
└──────────────────┘          └───────┘
```

What different layers learn:

| Layer | Detects |
|-------|---------|
| Layer 1 | Edges, gradients, colour blobs |
| Layer 2 | Corners, curves, textures |
| Layer 3 | Object parts: eyes, wheels, fur |
| Layer 4 | Full objects: face, car, cat |

```python
import torch
import torch.nn as nn

class SimpleCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: detect low-level features
            nn.Conv2d(3, 32, kernel_size=3, padding=1),  # 3 channels in, 32 filter maps out
            nn.ReLU(),
            nn.MaxPool2d(2),                              # halve spatial dimensions
            
            # Block 2: detect mid-level features
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            
            # Block 3: detect high-level features
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),                 # global average pooling
        )
        self.classifier = nn.Linear(128, num_classes)

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)   # flatten
        return self.classifier(x)
```

---

## The ImageNet Moment (2012)

AlexNet's 2012 ImageNet victory (15.3% error vs 26.2% second place) launched modern vision AI. Key innovations:

- **ReLU activations** instead of sigmoid — faster training
- **GPU training** — reduced training time from weeks to days
- **Dropout** — prevented overfitting on 1.2M images
- **Data augmentation** — random flips, crops, colour jitter

Since 2012, ImageNet error rates have dropped below **2%** — better than human performance (5%). The benchmark is now considered solved.

---

## Transfer Learning: Don't Train from Scratch

The most practical computer vision technique: take a model pre-trained on ImageNet and fine-tune it on your specific task.

```python
import torchvision.models as models

# Load ResNet-50 pre-trained on ImageNet (25M parameters, ~74% accuracy)
model = models.resnet50(pretrained=True)

# Freeze pre-trained weights — keep all learned features
for param in model.parameters():
    param.requires_grad = False

# Replace final layer for your task (e.g., 5 medical scan categories)
model.fc = nn.Linear(2048, 5)

# Only the final layer gets trained — fast, data-efficient
optimizer = torch.optim.Adam(model.fc.parameters(), lr=1e-3)

# Result: works well with only ~1,000 training images
# Training from scratch would need 1,000,000+
```

**Why it works:** Features learned from millions of natural images (edges, textures, shapes) transfer remarkably well to medical imaging, satellite imagery, quality control — almost any visual domain.

---

## CLIP: Connecting Images and Language

**CLIP** (Contrastive Language-Image Pre-training, OpenAI 2021) is the model that unified vision and language. It was trained on 400 million (image, text caption) pairs from the internet using **contrastive learning**:

```
Training objective:
  Given an image and N text captions, learn to:
  - maximise similarity between the correct image-caption pair
  - minimise similarity between all wrong pairs

Image of a dog + "a golden retriever playing fetch" → HIGH similarity
Image of a dog + "the Eiffel Tower at sunset"        → LOW similarity
```

```python
import torch
import clip
from PIL import Image

# Load CLIP
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Zero-shot image classification — no task-specific training needed
image = preprocess(Image.open("dog.jpg")).unsqueeze(0).to(device)
labels = ["a dog", "a cat", "a car", "a mountain"]
text   = clip.tokenize(labels).to(device)

with torch.no_grad():
    image_features = model.encode_image(image)
    text_features  = model.encode_text(text)

    # Cosine similarity between image and each text
    similarity = (image_features @ text_features.T).softmax(dim=-1)

for label, score in zip(labels, similarity[0]):
    print(f"{label}: {score:.3f}")
# a dog: 0.891
# a cat: 0.067
# a car: 0.024
# a mountain: 0.018
```

CLIP enabled zero-shot classification — classify images into any category without training examples. It also powers the text encoders in image generation models.

---

## Diffusion Models: Generating Images from Text

**Stable Diffusion**, **DALL-E**, and **Midjourney** all use **diffusion models**. The process:

```
TRAINING: learn to reverse a noise-adding process
  Real image → add noise step 1 → add noise step 2 → ... → pure noise
  Model learns: given noisy image at step T, predict less-noisy image at step T-1

GENERATION: start from pure noise, iteratively denoise
  Pure noise → denoise step 1 → denoise step 2 → ... → generated image
  Text prompt guides each denoising step via CLIP text embeddings
```

```python
from diffusers import StableDiffusionPipeline
import torch

# Load Stable Diffusion (this downloads ~4GB on first run)
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

# Generate from text prompt
image = pipe(
    prompt="A cyberpunk cat hacker typing on a glowing keyboard, neon lights, "
           "cinematic lighting, highly detailed, 8k",
    negative_prompt="blurry, low quality, distorted",
    num_inference_steps=50,   # more steps = better quality but slower
    guidance_scale=7.5,       # how strongly to follow the prompt
    width=512,
    height=512,
).images[0]

image.save("cyberpunk_cat.png")
```

**The guidance_scale parameter:**
- Low (1–3): image ignores the prompt, very creative but unconstrained
- Medium (7–8): balanced — follows prompt, allows some variation
- High (15+): rigidly follows prompt, less natural-looking

---

## Key Vision AI Models (2024–2025)

| Model | Organisation | Capability |
|-------|-------------|-----------|
| **GPT-4V / GPT-4o** | OpenAI | Understands any image; generates text descriptions |
| **Claude 3.5** | Anthropic | Strong image analysis; chart/document reading |
| **Gemini Vision** | Google | Natively multimodal; long video understanding |
| **DALL-E 3** | OpenAI | Text-to-image; very prompt-faithful |
| **Midjourney v6** | Midjourney | Artistic quality; best aesthetics |
| **Stable Diffusion 3** | Stability AI | Open weights; runs locally |
| **Flux** | Black Forest Labs | State-of-the-art open text-to-image (2024) |
| **Sora** | OpenAI | Text-to-video; up to 1-minute HD video |
| **Runway Gen-3** | Runway | Professional video generation |
| **SAM 2** | Meta | Segment anything in images AND video |

---

## Real-World Vision AI Applications

| Application | Technology | Impact |
|-------------|-----------|--------|
| **Medical imaging** | CNN (tumour detection) | Radiologist-level accuracy for lung cancer detection |
| **Autonomous vehicles** | CNN + LiDAR fusion | Tesla Autopilot, Waymo One |
| **Quality control** | Anomaly detection CNN | Semiconductor defect detection: 99.97% accuracy |
| **Security cameras** | Object detection (YOLO) | Real-time person/vehicle/weapon detection |
| **Agriculture** | Satellite + CNN | Crop disease detection, yield prediction |
| **Retail** | Computer vision | Amazon Go: checkout-free shopping |
| **Content moderation** | CLIP + classifiers | Facebook: 95%+ harmful content removed before reporting |

---

## The Multimodal Future

The boundaries between vision, language, and audio are dissolving:

```python
# GPT-4o: one model for text, image, audio, video
import openai

client = openai.OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "What security vulnerabilities do you see in this code screenshot?"},
            {"type": "image_url", "image_url": {"url": "https://example.com/code_screenshot.png"}}
        ]
    }]
)
print(response.choices[0].message.content)
# "I can see a SQL injection vulnerability on line 23 where user input
#  is directly concatenated into the query string..."
```

---

## Further Reading

- [CS231n: Convolutional Neural Networks for Visual Recognition (Stanford)](https://cs231n.github.io/)
- [CLIP Paper: Learning Transferable Visual Models from Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- [Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239)
- [Stable Diffusion Explained — Jay Alammar](https://jalammar.github.io/illustrated-stable-diffusion/)
