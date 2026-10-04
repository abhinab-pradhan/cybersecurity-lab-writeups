# 🥷 TryHackMe — Hacker vs Hacker

> **Web Enumeration | File Upload Bypass | Webshell | Remote Command Execution | Credential Discovery | SSH | Cron Misconfiguration | PATH Hijacking | Privilege Escalation**

![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square)
![Difficulty](https://img.shields.io/badge/Difficulty-Medium-orange?style=flat-square)
![Category](https://img.shields.io/badge/Category-Web%20%7C%20Linux%20Privilege%20Escalation-red?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

---

## 📌 Overview

**Hacker vs Hacker** is a TryHackMe Linux machine focused on web application enumeration, insecure file uploads, remote command execution, credential discovery, SSH access, and Linux privilege escalation.

The machine hosts a recruitment website called **RecruitSec**. The website contains a CV upload functionality that attempts to restrict uploaded files to PDF documents.

However, the upload validation can be bypassed by manipulating the filename.

This allows a PHP webshell to be uploaded and executed on the server, providing command execution as the `www-data` user.

After obtaining access, the `/home/lachlan` directory is investigated. The user's `.bash_history` contains credentials that can be reused to obtain SSH access as `lachlan`.

Further enumeration reveals a custom cron configuration:

```text
PATH=/home/lachlan/bin:/bin:/usr/bin
* * * * * root backup.sh
```
Because `/home/lachlan/bin` appears first in the root cron job's `PATH`, a malicious `backup.sh` placed there can be executed by root.

This results in a root reverse shell

---

# 🎯 Attack Path


```
Nmap Enumeration
       │
       ▼
RecruitSec Web Application
       │
       ▼
CV Upload Function
       │
       ▼
Upload Validation Bypass
       │
       ▼
PHP Webshell
       │
       ▼
www-data Shell
       │
       ▼
Lachlan Enumeration
       │
       ▼
.bash_history
       │
       ▼
Password Discovery
       │
       ▼
SSH as lachlan
       │
       ▼
Cron Enumeration
       │
       ▼
PATH Hijacking
       │
       ▼
Malicious backup.sh
       │
       ▼
Root Reverse Shell
       │
       ▼
🏆 Root Flag
```

---

# 🔎 1. Initial Enumeration
I started with an Nmap service and version scan against the target.
```
nmap -sV -A <TARGET_IP>
```

<img width="700" height="258" alt="1" src="https://github.com/user-attachments/assets/4943aa7e-be28-41d0-967d-d0cb2916556c" />

The scan identified two open TCP ports:
```
22/tcp    open    ssh
80/tcp    open    http
```

The HTTP service was running an application called:
```
RecruitSec
```
This became the primary target for further enumeration.

---

# 🌐 2. Web Enumeration
I opened the web server:
```
http://<TARGET_IP>
```
The website displayed a recruitment-themed page.

 <img width="1249" height="571" alt="2" src="https://github.com/user-attachments/assets/4b92c98e-e59b-4c06-ad49-6b9c317b1ac1" />

<img width="909" height="300" alt="2-2" src="https://github.com/user-attachments/assets/cdbebc26-3b34-4b0e-b0db-d530024aec7a" />

The page contained a CV upload form.
The website stated that users could upload their CV for consideration.
This functionality was interesting because file upload features can sometimes lead to arbitrary file upload or remote code execution if the server-side validation is weak.

---

# 📤 3. Investigating the File Upload
The upload functionality was located at:
```
/upload.php
```
I inspected the source code of the upload page.
```
http://<TARGET_IP>/upload.php
```

 <img width="785" height="375" alt="2-3" src="https://github.com/user-attachments/assets/0f9ed862-d664-4f85-8e00-6806d79273aa" />

The source code contained the following validation logic:

```
$target_dir = "cvs/";
$target_file = $target_dir . basename($_FILES["fileToUpload"]["name"]);

if (!strpos($target_file, ".pdf")) {
    echo "Only PDF CVs are accepted.";
} else if (file_exists($target_file)) {
    echo "This CV has already been uploaded!";
} else if (move_uploaded_file($_FILES["fileToUpload"]["tmp_name"], $target_file)) {
    echo "Success! We will get back to you.";
}
```
Two important observations were made.

## Upload Directory

The source code revealed:
```
$target_dir = "cvs/";
```
Therefore, uploaded files should be stored under:
```
/cvs/
```
This was the next directory to investigate.

## Weak File Extension Validation

The application checks:
```
strpos($target_file, ".pdf")
```
This does not strictly verify that the file ends with `.pdf`.

---

# 4. 📂 Checking the /cvs/ Directory

Since the source code explicitly revealed:
```
$target_dir = "cvs/";
```
the next step was to check the directory:
```
http://<TARGET_IP>/cvs/
```
<img width="646" height="124" alt="3" src="https://github.com/user-attachments/assets/e43d9ee5-f729-49fd-a470-4bf5c9c0835f" />



This step confirmed that the `/cvs/` location was accessible and was the directory associated with uploaded files.

The attack path was therefore:
```
Source Code
     ↓
$target_dir = "cvs/"
     ↓
/cvs/
```

---

# 5. 🧪 Bypassing the Upload Validation

Based on the source-code analysis, a filename containing `.pdf` but ending in `.php` could potentially bypass the application's check.

The filename used was:
```
shell.pdf.php
```
The important point is that:
```
shell.pdf.php
     ↑
   contains ".pdf"
```
while still ending with:
```
.php
```
If the web server executes `PHP` files inside the upload directory, this can result in arbitrary PHP code execution.

---
