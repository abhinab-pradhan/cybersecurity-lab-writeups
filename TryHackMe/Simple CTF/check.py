import hashlib

salt = "1dac0d92e9fa6bb2"
target = "0c01f4468bd75d7a84c7eb73846e8d96"

with open("/usr/share/wordlists/rockyou.txt", "r", errors="ignore") as f:
    for line in f:
        password = line.rstrip("\n")
        digest = hashlib.md5((salt + password).encode()).hexdigest()

        if digest == target:
            print("[+] Password found:", password)
            break

