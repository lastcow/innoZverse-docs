# Wireless Security

## Wi-Fi Security Standards

| Standard | Encryption | Status |
|----------|-----------|--------|
| WEP | RC4 | ❌ Broken — never use |
| WPA | TKIP | ❌ Deprecated |
| WPA2 | AES-CCMP | ✅ Acceptable |
| WPA3 | SAE | ✅ Best current standard |

## Wi-Fi Analysis Tools

```bash
# List wireless interfaces
iwconfig
iw dev

# Scan for networks
sudo iw dev wlan0 scan | grep -E "SSID|signal|freq"
nmcli dev wifi list

# Monitor mode (for authorized testing)
sudo airmon-ng start wlan0      # Enable monitor mode
sudo airodump-ng wlan0mon       # Capture packets
sudo airmon-ng stop wlan0mon    # Disable monitor mode
```

## Securing Your Wi-Fi

```
✅ Use WPA3 (or WPA2-AES at minimum)
✅ Strong, unique password (20+ characters)
✅ Disable WPS
✅ Change default router credentials
✅ Enable network isolation for IoT devices
✅ Use guest network for visitors
✅ Keep router firmware updated
❌ Never use WEP or open networks
❌ Don't use SSID that reveals your identity/location
```
