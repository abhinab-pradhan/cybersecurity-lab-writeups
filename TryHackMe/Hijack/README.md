# 🔐 TryHackMe — Hijack

> **NFS Enumeration | UID Manipulation | FTP Enumeration | Credential Discovery | MD5 | Base64 | Cookie Manipulation | Burp Suite Intruder**


![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
<img src="https://img.shields.io/badge/Platform-TryHackMe-00a98f?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/OS-Ubuntu-e95420?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/FTP-vsFTPd%203.0.3-4d908e?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/Web-Apache%202.4.18-d22128?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/NFS-Enabled-577590?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/Tools-Nmap%20%7C%20Burp%20%7C%20FTP-6f42c1?style=flat-square&labelColor=555555" />

---

## 📌 Overview

**Hijack** is a TryHackMe Linux-based penetration-testing lab focused on:

- Network enumeration
- NFS enumeration
- UID/GID manipulation
- FTP credential discovery
- Sensitive file exposure
- Password/hash analysis
- MD5 hashing
- Base64 encoding
- Session cookie manipulation
- Burp Suite Intruder

The initial attack path in this write-up is:

```text
Nmap
  ↓
NFS Enumeration
  ↓
/mnt/share
  ↓
UID/GID Manipulation
  ↓
for_employees.txt
  ↓
FTP Credentials
  ↓
FTP Enumeration
  ↓
.from_admin.txt
.passwords_list.txt
  ↓
Password Candidate List
  ↓
MD5 + Base64 Generation
  ↓
PHPSESSID Manipulation
  ↓
Burp Suite Intruder
  ↓
Administrative Session
