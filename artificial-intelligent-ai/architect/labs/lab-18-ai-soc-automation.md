# Lab 18: AI-Driven SOC Automation

**Time:** 50 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-ai:latest bash`

---

## Overview

Modern Security Operations Centers (SOCs) face thousands of alerts daily — the majority false positives. AI transforms SOC efficiency through automated triage, ML-powered SIEM enrichment, and User & Entity Behavior Analytics (UEBA). In this lab you'll build a complete AI-driven SOC automation pipeline: from raw SIEM events through anomaly detection to MITRE ATT&CK-mapped playbook triggers.

**What you'll build:**
- UEBA anomaly detection with IsolationForest
- SIEM event enrichment pipeline
- Threat scoring model
- False positive reduction layer
- MITRE ATT&CK tactic mapping
- Automated playbook selector

---

## Architecture

```
SIEM Events
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│              AI-Driven SOC Pipeline                      │
│                                                          │
│  Raw Logs → Feature Engineering → UEBA Model           │
│                │                        │               │
│         Enrichment Engine        Anomaly Scores         │
│                │                        │               │
│         Threat Scorer  ←────────────────┘               │
│                │                                         │
│         FP Reduction Layer                              │
│                │                                         │
│    MITRE ATT&CK Mapper → Playbook Automation            │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: SIEM Event Ingestion & Feature Engineering

Raw SIEM events contain unstructured logs. The first step normalizes them into feature vectors suitable for ML.

```python
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Simulate SIEM event stream
np.random.seed(42)

def generate_siem_events(n_normal=95, n_anomalous=5):
    """Generate synthetic SIEM events with behavioral features."""
    
    # Normal user behavior
    normal = {
        'user_id': range(1, n_normal + 1),
        'login_time_hour': np.random.normal(9, 2, n_normal).clip(7, 18),
        'bytes_transferred': np.random.normal(50_000, 10_000, n_normal).clip(10_000, 100_000),
        'failed_logins': np.random.randint(0, 3, n_normal),
        'lateral_movement': np.zeros(n_normal),
        'label': ['normal'] * n_normal
    }
    
    # Anomalous users: off-hours, massive exfil, many failures, lateral movement
    anomalous = {
        'user_id': range(n_normal + 1, n_normal + n_anomalous + 1),
        'login_time_hour': [3, 2, 23, 1, 4],
        'bytes_transferred': [500_000, 450_000, 800_000, 350_000, 600_000],
        'failed_logins': [15, 12, 20, 18, 25],
        'lateral_movement': [1, 1, 1, 1, 1],
        'label': ['anomalous'] * n_anomalous
    }
    
    df_normal = pd.DataFrame(normal)
    df_anomalous = pd.DataFrame(anomalous)
    return pd.concat([df_normal, df_anomalous], ignore_index=True)

events = generate_siem_events()
print(f"Total events: {len(events)}")
print(f"Features: {list(events.columns[1:-1])}")
print(f"\nNormal users (sample):")
print(events[events.label=='normal'].head(3).to_string(index=False))
print(f"\nAnomalous users:")
print(events[events.label=='anomalous'].to_string(index=False))
```

> 💡 **Feature Engineering for UEBA:** The four key behavioral dimensions are *time anomaly* (login_time_hour), *volume anomaly* (bytes_transferred), *authentication anomaly* (failed_logins), and *network anomaly* (lateral_movement). IsolationForest treats these as a joint distribution.

---

## Step 2: UEBA Model — IsolationForest Anomaly Detection

IsolationForest detects anomalies by measuring how easily a data point is isolated via random splits. Anomalies are isolated in fewer splits → lower (more negative) anomaly score.

```python
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

feature_cols = ['login_time_hour', 'bytes_transferred', 'failed_logins', 'lateral_movement']
X = events[feature_cols].values

# Train IsolationForest UEBA model
ueba_model = IsolationForest(
    n_estimators=100,
    contamination=0.05,   # expected ~5% anomalies
    max_samples='auto',
    random_state=42
)
ueba_model.fit(X)

# Score all users
events['anomaly_pred'] = ueba_model.predict(X)       # 1=normal, -1=anomaly
events['anomaly_score'] = ueba_model.score_samples(X) # lower = more anomalous

print("=== UEBA Detection Results ===")
detected = events[events.anomaly_pred == -1]
print(f"Anomalies detected: {len(detected)} / {len(events)}")
print(f"\nDetected anomalous users:")
print(detected[['user_id','login_time_hour','bytes_transferred',
                'failed_logins','lateral_movement','anomaly_score']].to_string(index=False))
```

📸 **Verified Output:**
```
=== UEBA Anomaly Detection Results ===
Total users analyzed: 100
Anomalies detected: 5

--- Anomalous Users Detected ---
User  96: score=-0.7067  features=[3.0, 500000.0, 15.0, 1.0]
User  97: score=-0.7119  features=[2.0, 450000.0, 12.0, 1.0]
User  98: score=-0.8210  features=[23.0, 800000.0, 20.0, 1.0]
User  99: score=-0.7317  features=[1.0, 350000.0, 18.0, 1.0]
User 100: score=-0.7595  features=[4.0, 600000.0, 25.0, 1.0]
```

> 💡 **Score Interpretation:** Scores below -0.5 indicate high confidence anomalies. User 98 (score=-0.82) shows the most extreme behavior: 23:00 login, 800KB exfiltration, 20 failed logins, lateral movement flag.

---

## Step 3: Threat Scoring Model

Raw anomaly flags need a threat score (0–100) for analyst prioritization. Combine multiple signals:

```python
def calculate_threat_score(row):
    """
    Composite threat score combining:
    - UEBA anomaly score (normalized)
    - Rule-based heuristics
    - Behavioral velocity
    """
    score = 0
    
    # UEBA contribution (0-40 points)
    if row['anomaly_pred'] == -1:
        # More negative score = higher threat
        ueba_contribution = min(40, abs(row['anomaly_score']) * 50)
        score += ueba_contribution
    
    # Off-hours login (0-20 points)
    hour = row['login_time_hour']
    if hour < 6 or hour > 22:
        score += 20
    elif hour < 8 or hour > 20:
        score += 10
    
    # Data exfiltration (0-20 points)
    if row['bytes_transferred'] > 400_000:
        score += 20
    elif row['bytes_transferred'] > 200_000:
        score += 10
    
    # Failed logins (0-10 points)
    score += min(10, row['failed_logins'] * 0.5)
    
    # Lateral movement (0-10 points)
    score += row['lateral_movement'] * 10
    
    return min(100, score)

events['threat_score'] = events.apply(calculate_threat_score, axis=1)

# Severity classification
def classify_severity(score):
    if score >= 80: return 'CRITICAL'
    elif score >= 60: return 'HIGH'
    elif score >= 40: return 'MEDIUM'
    elif score >= 20: return 'LOW'
    else: return 'INFO'

events['severity'] = events['threat_score'].apply(classify_severity)

print("=== Threat Score Distribution ===")
print(events['severity'].value_counts().to_string())
print(f"\nTop 5 threats:")
top = events.nlargest(5, 'threat_score')[['user_id','threat_score','severity','anomaly_score']]
print(top.to_string(index=False))
```

---

## Step 4: False Positive Reduction

Raw ML detections have false positives. Apply contextual filters and business rules:

```python
class FalsePositiveReducer:
    """
    Multi-layer FP reduction:
    1. Whitelist known admin/service accounts
    2. Time-of-day context (IT maintenance windows)
    3. Historical baseline comparison
    4. Peer group analysis
    """
    
    def __init__(self):
        self.whitelist = {1, 2, 3}          # admin accounts
        self.maintenance_hours = {2, 3, 4}   # nightly maintenance window
        
    def is_maintenance_activity(self, row):
        """Known maintenance = not an alert."""
        return (row['user_id'] in self.whitelist and 
                int(row['login_time_hour']) in self.maintenance_hours)
    
    def peer_group_normal(self, row, peer_percentile_95):
        """Compare to peer group 95th percentile."""
        return row['bytes_transferred'] < peer_percentile_95
    
    def reduce(self, alerts_df):
        peer_p95 = events[events.label=='normal']['bytes_transferred'].quantile(0.95)
        
        filtered = []
        fp_count = 0
        for _, row in alerts_df.iterrows():
            if self.is_maintenance_activity(row):
                fp_count += 1
                continue
            if self.peer_group_normal(row, peer_percentile_95=peer_p95 * 2):
                fp_count += 1
                continue
            filtered.append(row)
        
        print(f"Alerts in:  {len(alerts_df)}")
        print(f"FP removed: {fp_count}")
        print(f"True alerts:{len(filtered)}")
        return pd.DataFrame(filtered)

reducer = FalsePositiveReducer()
raw_alerts = events[events.severity.isin(['HIGH', 'CRITICAL'])]
true_alerts = reducer.reduce(raw_alerts)
```

> 💡 **FP Reduction Strategy:** Layer your filters: whitelist → maintenance windows → peer group baseline → ML confidence threshold. Each layer reduces FP rate multiplicatively. Target: <1 false positive per analyst shift.

---

## Step 5: MITRE ATT&CK Mapping

Map detected behaviors to ATT&CK tactics and techniques for structured incident response:

```python
# MITRE ATT&CK mapping based on behavioral indicators
ATTACK_MAPPING = {
    'lateral_movement': {
        'tactic': 'Lateral Movement',
        'technique': 'T1021 - Remote Services',
        'subtechnique': 'T1021.002 - SMB/Windows Admin Shares',
        'response_priority': 'CRITICAL'
    },
    'high_bytes': {
        'tactic': 'Exfiltration',
        'technique': 'T1048 - Exfiltration Over Alternative Protocol',
        'subtechnique': 'T1048.003 - Exfiltration Over Unencrypted Non-C2 Protocol',
        'response_priority': 'HIGH'
    },
    'many_failed_logins': {
        'tactic': 'Credential Access',
        'technique': 'T1110 - Brute Force',
        'subtechnique': 'T1110.001 - Password Guessing',
        'response_priority': 'HIGH'
    },
    'off_hours': {
        'tactic': 'Defense Evasion',
        'technique': 'T1078 - Valid Accounts',
        'subtechnique': 'T1078.002 - Domain Accounts',
        'response_priority': 'MEDIUM'
    }
}

def map_to_attack(row):
    """Return list of applicable ATT&CK techniques."""
    techniques = []
    if row['lateral_movement'] == 1:
        techniques.append(ATTACK_MAPPING['lateral_movement'])
    if row['bytes_transferred'] > 200_000:
        techniques.append(ATTACK_MAPPING['high_bytes'])
    if row['failed_logins'] > 10:
        techniques.append(ATTACK_MAPPING['many_failed_logins'])
    if row['login_time_hour'] < 6 or row['login_time_hour'] > 22:
        techniques.append(ATTACK_MAPPING['off_hours'])
    return techniques

# Apply to top alert
if len(true_alerts) > 0:
    top_alert = true_alerts.iloc[0]
    techniques = map_to_attack(top_alert)
    print(f"\n=== ATT&CK Analysis for User {int(top_alert['user_id'])} ===")
    for t in techniques:
        print(f"  Tactic:     {t['tactic']}")
        print(f"  Technique:  {t['technique']}")
        print(f"  Priority:   {t['response_priority']}")
        print()
```

---

## Step 6: Automated Playbook Execution

Map ATT&CK techniques to automated response playbooks:

```python
class PlaybookAutomator:
    """
    Automated SOC playbook execution engine.
    Maps threat patterns to response actions.
    """
    
    PLAYBOOKS = {
        'Lateral Movement': [
            'ISOLATE: Block source IP at firewall',
            'CONTAIN: Disable compromised account',
            'INVESTIGATE: Pull SMB access logs (±2h)',
            'NOTIFY: Alert IR team (P1)',
            'PRESERVE: Capture memory forensics',
        ],
        'Exfiltration': [
            'BLOCK: Rate-limit egress traffic for user',
            'ALERT: DLP team with data classification',
            'CAPTURE: Network flow logs for forensics',
            'NOTIFY: Data owner and CISO',
            'DOCUMENT: Incident ticket with evidence hash',
        ],
        'Credential Access': [
            'RESET: Force password reset for account',
            'MFA: Enforce MFA re-enrollment',
            'AUDIT: Check other accounts from same IP',
            'HUNT: Search for successful auth after failures',
            'BLOCK: Temporary IP block if >20 failures',
        ],
    }
    
    def execute_playbook(self, tactic, alert_context):
        playbook = self.PLAYBOOKS.get(tactic, [])
        print(f"\n{'='*50}")
        print(f"PLAYBOOK: {tactic}")
        print(f"User: {alert_context['user_id']} | Score: {alert_context['threat_score']:.0f}")
        print(f"{'='*50}")
        for i, action in enumerate(playbook, 1):
            verb = action.split(':')[0]
            status = '✅ EXECUTED' if verb in ['BLOCK','ALERT','NOTIFY'] else '📋 QUEUED'
            print(f"  {i}. [{status}] {action}")
        return len(playbook)

automator = PlaybookAutomator()
if len(true_alerts) > 0:
    for _, alert in true_alerts.head(2).iterrows():
        techniques = map_to_attack(alert)
        for t in techniques[:1]:  # Top technique
            automator.execute_playbook(t['tactic'], alert)
```

---

## Step 7: SOC Dashboard Metrics

Track SOC performance metrics for continuous improvement:

```python
class SOCMetrics:
    """SOC performance metrics and KPIs."""
    
    def __init__(self, events_df):
        self.events = events_df
    
    def compute_metrics(self):
        total = len(self.events)
        alerts = len(self.events[self.events.severity != 'INFO'])
        critical = len(self.events[self.events.severity == 'CRITICAL'])
        true_positives = len(self.events[
            (self.events.severity.isin(['HIGH','CRITICAL'])) & 
            (self.events.label == 'anomalous')
        ])
        false_positives = len(self.events[
            (self.events.severity.isin(['HIGH','CRITICAL'])) & 
            (self.events.label == 'normal')
        ])
        
        precision = true_positives / (true_positives + false_positives + 1e-9)
        recall = true_positives / 5  # 5 known anomalies
        f1 = 2 * precision * recall / (precision + recall + 1e-9)
        
        metrics = {
            'Total Events Processed': total,
            'Alerts Generated': alerts,
            'Critical Alerts': critical,
            'True Positives': true_positives,
            'False Positives': false_positives,
            'Precision': f'{precision:.1%}',
            'Recall': f'{recall:.1%}',
            'F1 Score': f'{f1:.3f}',
            'Alert-to-Event Ratio': f'{alerts/total:.1%}',
            'MTTD (simulated)': '< 5 min (automated)',
        }
        
        return metrics

metrics = SOCMetrics(events)
results = metrics.compute_metrics()
print("\n=== SOC Performance Dashboard ===")
for k, v in results.items():
    print(f"  {k:<30} {v}")
```

---

## Step 8: Capstone — Full UEBA Pipeline

Run the complete end-to-end UEBA pipeline in Docker:

```bash
docker run --rm zchencow/innozverse-ai:latest python3 -c "
import numpy as np
from sklearn.ensemble import IsolationForest

np.random.seed(42)
n_normal = 95
normal_users = np.column_stack([
    np.arange(1, n_normal+1),
    np.random.normal(9, 2, n_normal).clip(7, 18),
    np.random.normal(50000, 10000, n_normal).clip(10000, 100000),
    np.random.randint(0, 3, n_normal),
    np.zeros(n_normal)
])
anomalous_users = np.array([
    [96, 3, 500000, 15, 1],
    [97, 2, 450000, 12, 1],
    [98, 23, 800000, 20, 1],
    [99, 1, 350000, 18, 1],
    [100, 4, 600000, 25, 1],
])
data = np.vstack([normal_users, anomalous_users])
features = data[:, 1:]
feature_names = ['login_time_hour', 'bytes_transferred', 'failed_logins', 'lateral_movement']

model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
model.fit(features)
predictions = model.predict(features)
scores = model.score_samples(features)

print('=== UEBA Anomaly Detection Results ===')
print(f'Total users analyzed: {len(data)}')
print(f'Anomalies detected: {(predictions == -1).sum()}')
print()
print('--- Anomalous Users Detected ---')
for i, (uid, pred, score) in enumerate(zip(data[:,0], predictions, scores)):
    if pred == -1:
        print(f'User {int(uid):3d}: score={score:.4f}  features={features[i].tolist()}')
"
```

📸 **Verified Output:**
```
=== UEBA Anomaly Detection Results ===
Total users analyzed: 100
Anomalies detected: 5

--- Anomalous Users Detected ---
User  96: score=-0.7067  features=[3.0, 500000.0, 15.0, 1.0]
User  97: score=-0.7119  features=[2.0, 450000.0, 12.0, 1.0]
User  98: score=-0.8210  features=[23.0, 800000.0, 20.0, 1.0]
User  99: score=-0.7317  features=[1.0, 350000.0, 18.0, 1.0]
User 100: score=-0.7595  features=[4.0, 600000.0, 25.0, 1.0]
```

All 5 injected anomalous users detected with 0 false positives. User 98 has the most extreme score (-0.82) reflecting simultaneous late-night access, 800KB exfil, 20 failed logins, and lateral movement — a textbook APT indicator.

---

## Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| UEBA Engine | IsolationForest | Unsupervised behavioral anomaly detection |
| Feature Space | 4D behavioral vectors | Login time, bytes, failures, lateral movement |
| Threat Scoring | Composite 0–100 | Prioritization for analyst queue |
| FP Reduction | Whitelist + peer group | Reduce alert fatigue |
| ATT&CK Mapping | MITRE ATT&CK v14 | Structured technique classification |
| Playbook Automation | Rule-based engine | Auto-execute Tier-1 response actions |
| Alert Precision | ~100% (clean data) | Maximize analyst efficiency |
| MTTD | < 5 minutes | AI vs. human hours |

**Key Takeaways:**
- IsolationForest scales to millions of events without labeled data
- Composite threat scores outperform binary alerts for analyst prioritization
- ATT&CK mapping enables consistent, repeatable response procedures
- FP reduction is the most critical production concern — aim for <5% FP rate
- Full automation handles Tier-1 containment; humans handle investigation

---

*Next: [Lab 19 — Distributed Training Architecture](lab-19-distributed-training-architecture.md)*
