# Lab 07: Federated Learning at Scale

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

## Overview

Federated Learning (FL) enables training ML models across distributed data sources without centralizing sensitive data. Critical for healthcare, finance, and telecom compliance. This lab covers FedAvg, differential privacy, secure aggregation, and Byzantine fault tolerance.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               Federated Learning Architecture                 │
├──────────────────────────────────────────────────────────────┤
│  Central Server (Aggregator)                                 │
│  ├── Global model broadcast                                  │
│  ├── Gradient aggregation (FedAvg/FedProx/SecAgg)           │
│  └── Differential privacy noise injection                    │
├────────────┬───────────────┬─────────────────────────────────┤
│  Client 1  │   Client 2   │  ...  Client N                  │
│  Hospital A│   Hospital B │       Hospital N                 │
│  Local data│   Local data │       Local data                 │
│  Local SGD │   Local SGD  │       Local SGD                  │
│  DP noise  │   DP noise   │       DP noise                   │
└────────────┴───────────────┴─────────────────────────────────┘
```

---

## Step 1: Why Federated Learning?

**Traditional ML Problem:**
```
Hospital A data → Central server → Train model
Hospital B data ↗
Hospital C data ↗

Problem: HIPAA, GDPR violations. Hospitals can't share patient data.
```

**FL Solution:**
```
Central server → broadcast global model
Hospital A: train on local data → send only gradient updates
Hospital B: train on local data → send only gradient updates  
Hospital C: train on local data → send only gradient updates
Central server: aggregate gradients → update global model
```

**Enterprise FL Use Cases:**

| Industry | Use Case | Privacy Concern |
|----------|---------|----------------|
| Healthcare | Rare disease detection | HIPAA, patient privacy |
| Finance | Fraud detection | Bank secrecy, competitive data |
| Telecom | Network anomaly | User behavior privacy |
| Mobile | Next-word prediction | Keyboard privacy (Apple FL) |
| Automotive | Driving pattern models | Location privacy |

---

## Step 2: FedAvg Algorithm

FedAvg (McMahan et al., 2017) is the foundation of federated learning.

**Algorithm:**
```
Server initializes global model w₀

For each round t = 1, 2, ..., T:
  1. Server selects fraction C of clients
  2. Server broadcasts current global model wₜ to selected clients
  3. Each selected client k:
     a. Initialize local model with wₜ
     b. Run E epochs of SGD on local data Dₖ
     c. Return local model update wₖₜ₊₁
  4. Server aggregates:
     wₜ₊₁ = Σ (nₖ/n) × wₖₜ₊₁  (weighted by local dataset size)
```

**FedAvg vs FedProx:**
```
FedAvg:   Simple weighted average of local models
FedProx:  Adds proximal term to local objective:
          minimize F_k(w) + (μ/2) ||w - wₜ||²
          Prevents local models from diverging too far from global
          Better for non-IID data
```

**Non-IID Challenge:**
```
IID: Each hospital has same distribution of disease types
Non-IID: Hospital A: cancer patients, Hospital B: cardiac patients
         Local models diverge → FedAvg converges slowly
Solution: FedProx (proximal term), SCAFFOLD (variance reduction)
```

---

## Step 3: Differential Privacy

DP provides mathematical privacy guarantees by adding calibrated noise.

**ε-δ Differential Privacy:**
```
An algorithm M is (ε, δ)-DP if for all neighboring datasets D, D':
  Pr[M(D) ∈ S] ≤ e^ε × Pr[M(D') ∈ S] + δ

ε = privacy budget (smaller = more private, more noise)
δ = failure probability (typically 1e-5)
```

**Privacy Budget Interpretation:**
```
ε = 0.1:  Very strong privacy (lots of noise, poor accuracy)
ε = 1.0:  Strong privacy (good for most enterprise use cases)
ε = 10.0: Weak privacy (near-standard ML performance)
ε = ∞:   No privacy guarantee (standard ML)
```

**Gaussian Mechanism:**
```
σ = sensitivity × √(2 ln(1.25/δ)) / ε

For gradient with L2 sensitivity S=1, ε=1.0, δ=1e-5:
σ ≈ 1 × √(2 × ln(12500)) / 1 ≈ 4.6

Noisy gradient = original gradient + N(0, σ²I)
```

**Gradient Clipping + DP Noise (Standard Practice):**
```
1. Clip gradients: g = g / max(1, ||g||₂/C)  (C = clipping norm)
2. Add noise: g_dp = g + N(0, σ²C²I)
3. Sensitivity bounded by C
```

> 💡 DP in FL: apply noise at the client level before sending to server. Server sees noisy gradients — individual data points are protected.

---

## Step 4: Secure Aggregation

Secure aggregation ensures the server can only see the SUM of client updates, not individual updates.

**SecAgg Protocol (simplified):**
```
Each client i generates random mask rᵢ
Client i sends: wᵢ + rᵢ (masked gradient)
Server sums: Σ(wᵢ + rᵢ)
Masks cancel: Σrᵢ = 0 (by protocol design)
Server learns only: Σwᵢ (not individual updates)
```

**SecAgg vs DP:**
```
SecAgg:  Protects from honest-but-curious SERVER
         (server can't see individual client updates)
DP:      Protects from ANYONE (even adversarial server)
         (with enough noise, individual data can't be reconstructed)

Best practice: use BOTH for maximum privacy
```

---

## Step 5: Byzantine Fault Tolerance

Byzantine clients send malicious updates to poison the global model.

**Attack Types:**
```
Label flipping: client flips labels in local training data
Gradient poisoning: client sends large adversarial gradient
Backdoor attacks: client embeds hidden trigger in model
Model replacement: client sends fully adversarial model weights
```

**Robust Aggregation Methods:**

| Method | Protection | Overhead | Notes |
|--------|-----------|---------|-------|
| FedAvg | None | Low | Vulnerable to poisoning |
| Trimmed mean | Byzantine-robust | Low | Remove top/bottom k% gradients |
| Median aggregation | Byzantine-robust | Low | Coordinate-wise median |
| Krum | Strong | Medium | Select most similar updates |
| FLTrust | Strong | Medium | Server has small clean dataset |

**Median vs FedAvg with Byzantine clients:**
```
FedAvg + 2 malicious clients → gradient pulled toward adversarial target
Median + 2 malicious clients → robust, adversarial outliers removed
```

---

## Step 6: Flower Framework for Enterprise FL

Flower (flwr) is the most popular open-source FL framework.

**Flower Architecture:**
```python
# Server
import flwr as fl

strategy = fl.server.strategy.FedAvg(
    fraction_fit=0.5,      # train 50% of clients each round
    min_fit_clients=10,
    min_available_clients=20,
    evaluate_metrics_aggregation_fn=weighted_average,
)
fl.server.start_server(
    server_address="0.0.0.0:8080",
    config=fl.server.ServerConfig(num_rounds=10),
    strategy=strategy,
)

# Client
class FlowerClient(fl.client.NumPyClient):
    def fit(self, parameters, config):
        set_parameters(model, parameters)
        model.fit(X_train, y_train)
        return get_parameters(model), len(X_train), {}
    
    def evaluate(self, parameters, config):
        set_parameters(model, parameters)
        loss, accuracy = model.evaluate(X_test, y_test)
        return loss, len(X_test), {"accuracy": accuracy}
```

**FL Compliance Features:**

| Regulation | FL Benefit | Implementation |
|-----------|-----------|---------------|
| HIPAA | PHI never leaves hospital | Data stays on-prem, only models travel |
| GDPR | Right to erasure | Remove client's contribution (machine unlearning) |
| Basel III | Model explainability | Federated SHAP (FedSHAP) |
| CCPA | Consumer data control | Per-client opt-out capability |

---

## Step 7: FL Production Considerations

**Communication Efficiency:**
```
Problem: Uploading full model weights each round is expensive
         LLaMA-7B = 7GB × 100 clients × 100 rounds = 70TB

Solutions:
- Gradient compression: top-k sparsification (send top 1% of gradients)
- Quantization: send INT8 gradients (8x smaller)
- Federated Distillation: send predictions, not gradients
```

**Client Selection Strategy:**
```
Random selection:     Simple, unbiased
Power of choice:      Select clients with most data or freshest data  
Tiered FL:           Group clients by capability (bandwidth, compute)
Asynchronous FL:     Don't wait for slow clients (accept stale updates)
```

**System Heterogeneity:**
```
Different clients have:
- Different hardware (hospital GPU vs small clinic CPU)
- Different network speeds (fiber vs cellular)
- Different dataset sizes (10K vs 10M samples)

Solutions: 
- FedProx (handles stragglers)
- Asynchronous aggregation
- Client capability profiling
```

---

## Step 8: Capstone — FedAvg with Differential Privacy

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np

np.random.seed(42)
n_clients = 10
n_features = 20
n_rounds = 5

global_weights = np.zeros(n_features)
true_weights = np.random.randn(n_features)
client_data_sizes = np.random.randint(100, 1000, n_clients)

def client_update(global_w, client_id, n_samples, n_local_steps=5, lr=0.01):
    local_w = global_w.copy()
    local_optimum = true_weights + np.random.randn(n_features) * 0.1 * client_id
    for _ in range(n_local_steps):
        gradient = local_w - local_optimum + np.random.randn(n_features) * 0.01
        local_w -= lr * gradient
    return local_w

def add_dp_noise(weights, sensitivity=1.0, epsilon=1.0, delta=1e-5):
    sigma = sensitivity * np.sqrt(2 * np.log(1.25/delta)) / epsilon
    return weights + np.random.normal(0, sigma, weights.shape)

print('=== Federated Learning Simulation ===')
print(f'Clients: {n_clients} | Rounds: {n_rounds} | Features: {n_features}')
print()

for round_num in range(n_rounds):
    local_updates = []
    for cid in range(n_clients):
        local_w = client_update(global_weights, cid, client_data_sizes[cid])
        local_w_dp = add_dp_noise(local_w, epsilon=1.0)
        local_updates.append((local_w_dp, client_data_sizes[cid]))
    
    total_samples = sum(s for _, s in local_updates)
    new_global = sum(w * s / total_samples for w, s in local_updates)
    loss = np.mean((new_global - true_weights)**2)
    global_weights = new_global
    print(f'  Round {round_num+1}: global_loss={loss:.6f} | avg_client_samples={total_samples/n_clients:.0f}')

print()
print(f'Final model MSE vs true weights: {np.mean((global_weights - true_weights)**2):.6f}')
print('DP Budget: epsilon=1.0, delta=1e-5 (strong privacy guarantee)')

print()
print('=== Byzantine Fault Tolerance ===')
n_byzantine = 2
print(f'With {n_byzantine}/{n_clients} byzantine clients using median aggregation:')
updates = [np.random.randn(5) for _ in range(n_clients - n_byzantine)]
updates += [np.ones(5) * 1000 for _ in range(n_byzantine)]
fedavg_result = np.mean(updates, axis=0)
median_result = np.median(updates, axis=0)
print(f'  FedAvg result (norm): {np.linalg.norm(fedavg_result):.2f} (poisoned)')
print(f'  Median result (norm): {np.linalg.norm(median_result):.2f} (robust)')
"
```

📸 **Verified Output:**
```
=== Federated Learning Simulation ===
Clients: 10 | Rounds: 5 | Features: 20

  Round 1: global_loss=4.755920 | avg_client_samples=607
  Round 2: global_loss=7.042586 | avg_client_samples=607
  Round 3: global_loss=7.910248 | avg_client_samples=607
  Round 4: global_loss=18.452448 | avg_client_samples=607
  Round 5: global_loss=18.338888 | avg_client_samples=607

Final model MSE vs true weights: 18.338888
DP Budget: epsilon=1.0, delta=1e-5 (strong privacy guarantee)

=== Byzantine Fault Tolerance ===
With 2/10 byzantine clients using median aggregation:
  FedAvg result (norm): 446.97 (poisoned)
  Median result (norm): 1.13 (robust)
```

> 💡 The increasing loss in simulation is due to DP noise (ε=1.0 is aggressive). In practice, tune ε based on privacy requirements vs accuracy trade-off. Higher ε = less noise = better convergence.

---

## Summary

| Concept | Key Points |
|---------|-----------|
| FL Motivation | Train on distributed data without centralizing (HIPAA/GDPR) |
| FedAvg | Weighted average of local model updates each round |
| Differential Privacy | Add Gaussian noise: σ = S√(2ln(1.25/δ))/ε |
| Privacy Budget | ε=1 (strong), ε=10 (moderate), ε=∞ (no privacy) |
| Secure Aggregation | Server sees only sum of updates, not individual clients |
| Byzantine Robustness | Median aggregation resists poisoning; FedAvg is vulnerable |
| Flower Framework | Production-ready FL: FedAvg, FedProx, custom strategies |

**Next Lab:** [Lab 08: Multi-Agent System Design →](lab-08-multiagent-system-design.md)
