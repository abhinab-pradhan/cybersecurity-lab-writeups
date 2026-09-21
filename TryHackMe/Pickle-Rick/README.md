# 🥒 TryHackMe — Pickle Rick

> **Web Enumeration | Command Execution | Linux Privilege Escalation**


![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Target-Linux-orange?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Focus-Web%20Enumeration-blue?style=flat-square&labelColor=555555)
![Difficulty](https://img.shields.io/badge/Status-Completed-success?style=flat-square&labelColor=555555)

---

## 📌 Objective

The objective of this lab was to compromise a vulnerable Linux web server, enumerate the web application, obtain command execution, locate the three hidden ingredients, and ultimately access the final ingredient through privilege escalation.

The attack involved:

- Network reconnaissance
- Web enumeration
- Inspecting webpage source
- Discovering a username
- Finding a password through robots.txt
- Logging into the web application
- Obtaining command execution
- Linux filesystem enumeration
- Finding the first and second ingredients
- Enumerating sudo permissions
- Accessing the final ingredient as root


# 🔗 Attack Chain

```text
                    ┌──────────────┐
                    │   Nmap Scan  │
                    └──────┬───────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ Open Ports Found │
                 │ 22 / 80         │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Web Enumeration  │
                 │ Gobuster         │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ robots.txt       │
                 │ login.php        │
                 │ portal.php       │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Login Portal     │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Command Execution│
                 └────────┬─────────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
     ┌───────────────┐          ┌───────────────┐
     │ First         │          │ clue.txt      │
     │ Ingredient    │          └───────┬───────┘
     └───────────────┘                  │
                                        ▼
                                ┌───────────────┐
                                │ /home/rick    │
                                │ Second        │
                                │ Ingredient    │
                                └───────┬───────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ sudo -l       │
                                └───────┬───────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ Root Access   │
                                └───────┬───────┘
                                        │
                                        ▼
                                ┌───────────────┐
                                │ Third         │
                                │ Ingredient    │
                                └───────────────┘
```

---

# 1. 🔎 Reconnaissance

I started by performing a service and version detection scan against the target.
```
nmap -sV -sC <TARGET_IP>
```
The scan identified the following services:
```
22/tcp    SSH
80/tcp    HTTP
```
Port 80 was particularly interesting because a web application was exposed.

<img width="830" height="322" alt="1" src="https://github.com/user-attachments/assets/d96daf23-1257-4924-8cc3-47153265d4f2" />


---

# 3. Web Enumeration

I opened the web server in a browser:
```
http://<TARGET_IP>
```
The page displayed content related to Rick and Morty.

At this point, instead of immediately trying to brute-force the login page, I inspected the webpage and its source for information that could be useful for authentication.

**Inspecting the Webpage Source**

I inspected the HTML source of the webpage.

While examining the source, I discovered a username.

The username was:
```
R1ckRul3s
```
This was an important discovery because it provided one half of the credentials required to access the login portal.

<img width="1011" height="495" alt="2" src="https://github.com/user-attachments/assets/7ee225ac-02c6-44cf-ad7b-de9d15ab9867" />


At this stage, I still needed to find the password.

---

# 4. Directory Enumeration

I performed directory/file enumeration against the web server using Gobuster.
```
gobuster dir -u http://<TARGET_IP>/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,txt,js
```
The enumeration revealed several interesting resources, including:
```
/login.php
/portal.php
/robots.txt
/assets/
Screenshot
```
The discovery of robots.txt was particularly interesting because it could contain information intentionally hidden from search engines.

<img width="1080" height="390" alt="3" src="https://github.com/user-attachments/assets/634e8852-d8dd-4f3f-86c1-6fbc4619e09d" />

---

# 5. Finding the Password

I accessed the ```robots.txt``` file:
```
curl http://<TARGET_IP>/robots.txt
```
The file contained:
```
Wubbalubbadubdub
```
This appeared to be the password required for the login portal.

<img width="596" height="133" alt="4-1" src="https://github.com/user-attachments/assets/fdbd861f-d9b3-4864-8497-815f4b082e7d" />

**Credential Discovery**
At this point, I had obtained both parts of the login credentials:
```
Username: R1ckRul3s
Password: Wubbalubbadubdub
```
The important part of the enumeration was that the username and password were discovered through different sources:
```
Webpage Source
      │
      └── Username
           R1ckRul3s

robots.txt
      │
      └── Password
           Wubbalubbadubdub
```
These credentials could now be tested against the discovered login page.

---

# 6. Authentication

The Gobuster enumeration had revealed:
```
/login.php
```
I opened the login page:
```
http://<TARGET_IP>/login.php
```
<img width="784" height="596" alt="4-2" src="https://github.com/user-attachments/assets/a5ada5d3-cb43-4fc7-af82-208e1eb27853" />

I entered the credentials discovered during enumeration:
```
Username: R1ckRul3s
Password: Wubbalubbadubdub
```
The credentials were accepted and I successfully authenticated to the application.

---

# 7. Command Execution

After successful authentication, I was redirected to the application portal.

The portal provided functionality for executing commands on the underlying Linux system.

<img width="837" height="351" alt="4-3" src="https://github.com/user-attachments/assets/e6fcfd60-f4ec-4e9f-9094-730ffd1671b4" />

---

# 8. Finding the First Ingredient

I listed the contents of the current directory:
```
ls
```
The output contained several interesting files:
```
Sup3rS3cretPickl3ingred.txt
clue.txt
login.php
portal.php
robots.txt
Screenshot
```

<img width="413" height="407" alt="6" src="https://github.com/user-attachments/assets/72ced20a-1990-4a1b-ab42-f74c142531eb" />

The file:
```
Sup3rS3cretPickl3ingred.txt
```
looked particularly interesting.

I attempted to read it using:
```
cat Sup3rS3cretPickl3ingred.txt
```
However, the application prevented the use of ```cat```.

<img width="708" height="467" alt="7" src="https://github.com/user-attachments/assets/643eda88-f534-4219-a8fb-aa9f52a5b2ed" />


Instead of stopping there, I tried another Linux utility that can be used to read files:
```
less Sup3rS3cretPickl3ingred.txt
```

<img width="500" height="318" alt="7-2" src="https://github.com/user-attachments/assets/7218ec16-cc01-48db-9d9b-eda37cdb9a0b" />

The file was successfully displayed and the **first ingredient** was obtained.

---

# 9. Investigating clue.txt

I then examined the clue.txt file:
```
less clue.txt
```
<img width="580" height="327" alt="8" src="https://github.com/user-attachments/assets/7cede071-1cab-4ad8-bf22-85d82a10f1fb" />

The clue indicated that another ingredient was located somewhere else on the system.

Therefore, I moved from the web application's directory to broader filesystem enumeration.

---

# 10. Filesystem Enumeration

I first checked the root filesystem:
```
ls /
```
<img width="440" height="432" alt="8-2" src="https://github.com/user-attachments/assets/8f6e8436-3e62-4515-b9b2-6ac27d2d01fb" />

Then I examined the /home directory:
```
ls /home
```
<img width="409" height="357" alt="8-3" src="https://github.com/user-attachments/assets/367adc87-f607-476d-808e-611c15b6803c" />

A directory belonging to rick was present.

I enumerated it:
```
ls /home/rick
```
<img width="372" height="175" alt="8-4" src="https://github.com/user-attachments/assets/40e5b284-4673-47a1-a2b6-31c13ab5d1b1" />

An interesting file containing the second ingredient was found.

---

# 11. Finding the Second Ingredient

I read the file:
```
less "/home/rick/second ingredients"
```
<img width="371" height="191" alt="8-5" src="https://github.com/user-attachments/assets/5eef066b-d4c7-4d4e-b868-5b355c1876d1" />

The second ingredient was successfully obtained.

---

# 12. Privilege Escalation Enumeration

Since the final ingredient was expected to be protected, I checked the privileges available to the current user.

I ran:
```
sudo -l
```
<img width="953" height="234" alt="9-2" src="https://github.com/user-attachments/assets/06602346-14ed-41dd-821d-24ecbf0bc653" />

The output showed that the current user had permission to execute an allowed command with elevated privileges.

This provided a path to access files that were otherwise restricted to root.

---

# 13. Finding the Third Ingredient

The final ingredient was located inside the root user's directory.

I used the permitted command to read the file:
```
sudo less /root/3rd.txt
```
<img width="362" height="259" alt="9-4" src="https://github.com/user-attachments/assets/3fe9eb0b-bc39-4ee3-962f-04ae12d3d450" />


The file contained the third and final ingredient.
