# Incident Response

## The IR Lifecycle (NIST)

```
Preparation → Detection → Containment → Eradication → Recovery → Lessons Learned
```

## Incident Response Checklist

### 🔴 Detection Phase
- [ ] Alert triggered (SIEM, IDS, user report)
- [ ] Confirm it's a real incident (not false positive)
- [ ] Classify severity (Critical/High/Medium/Low)
- [ ] Notify incident response team

### 🟠 Containment Phase
- [ ] Isolate affected systems from network
- [ ] Preserve evidence (memory dump, disk image)
- [ ] Block malicious IPs/domains at firewall
- [ ] Reset compromised credentials

### 🟡 Eradication Phase
- [ ] Identify root cause
- [ ] Remove malware and backdoors
- [ ] Patch exploited vulnerabilities
- [ ] Audit all affected accounts

### 🟢 Recovery Phase
- [ ] Restore from clean backup
- [ ] Monitor for re-infection
- [ ] Gradually restore services
- [ ] Verify system integrity

### 📝 Lessons Learned
- [ ] Document timeline of events
- [ ] Identify detection gaps
- [ ] Update policies and procedures
- [ ] Train staff on new threats

## Forensic Commands

```bash
# Capture memory (requires avml or similar tool)
sudo avml /tmp/memory.lime

# List network connections
ss -tlnp
netstat -tlnp

# Check recently modified files
find / -mtime -1 -type f 2>/dev/null | head -20

# Check running processes
ps auxf
ls -la /proc/*/exe 2>/dev/null | grep -v "No such"

# Check persistence mechanisms
crontab -l
ls -la /etc/cron*
ls -la ~/.bashrc ~/.bash_profile /etc/profile.d/
```
