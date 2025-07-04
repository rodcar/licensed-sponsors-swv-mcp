# Localhost Domain Mapping Guide

Configure your hosts file to map `my.localdomain` to your local network IP for Companies House API integration.

## Why This is Needed

The Companies House API requires authorized domains. For local development:
1. Set `http://my.localdomain` as an authorized JavaScript domain in your API key settings
2. Map `my.localdomain` to your actual network IP in your hosts file

---

## Windows

**Find your IP address:**
```cmd
ipconfig | findstr "IPv4"
```

**Edit hosts file:**
1. Open `C:\Windows\System32\drivers\etc\hosts` as Administrator
*(Replace `192.168.1.100` with your actual IP)*
2. Add at the end: `192.168.1.100    my.localdomain`
3. Save and run: `ipconfig /flushdns`



---

## macOS/Linux

**Find your IP address:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Edit hosts file:**
1. Open `/etc/hosts` with sudo privileges
*(Replace `192.168.1.100` with your actual IP)*
2. Add at the end: `192.168.1.100    my.localdomain`
3. Save and run:
   - macOS: `sudo dscacheutil -flushcache`
   - Linux: `sudo systemctl restart systemd-resolved`

---

## Verify

Test the mapping:
```bash
ping my.localdomain
```
You should see responses from your IP (192.168.x.x).