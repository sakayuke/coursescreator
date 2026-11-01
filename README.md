# Course Platform (LMS) 🚀

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask%203.x-black.svg)](https://flask.palletsprojects.com/)
[![ORM](https://img.shields.io/badge/ORM-SQLAlchemy%202.x-red.svg)](https://www.sqlalchemy.org/)
[![Database](https://img.shields.io/badge/database-MSSQL%20%2F%20SQLite-green.svg)](https://www.microsoft.com/sql-server)
[![Security Audited](https://img.shields.io/badge/security-OWASP%20Hardened-purple.svg)](#security--defense-in-depth)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

A robust, enterprise-grade **Learning Management System (LMS)** and course management web platform engineered with **Python, Flask, and SQLAlchemy**. Features multi-tenant Role-Based Access Control (RBAC), topic hierarchies, lecture material distribution, automated submission lifecycles, and teacher evaluation workflows.

---

## 🌟 Key Highlights & Architecture

- **Hierarchical Course Structure**: Courses contain structured Topics, which hold downloadable lecture materials and student assignments.
- **Role-Based Access Control (RBAC)**: Fine-grained declarative decorators (`@role_required`) governing Students, Teachers, Admins, and Superadmins.
- **Full Assignment Lifecycle**: Students submit solutions; instructors review, grade (0–100), and return structured feedback.
- **Teacher Request Workflow**: Students can formally apply for instructor privileges with administrative approval mechanisms.
- **Dual Engine Database Support**: Ready for production **Microsoft SQL Server (T-SQL)** with zero-configuration fallback to **SQLite** for rapid local development.
- **Adaptive UI**: High-contrast modern interface with native Dark/Light mode theme switching and responsive mobile ergonomics.

---

## 🛡️ Security & Defense-in-Depth

The codebase has undergone defensive auditing and security fortification against OWASP Top-10 vulnerabilities:

| Category | Defense Mechanism | Implementation |
| :--- | :--- | :--- |
| **Account Takeover Prevention** | Mandatory Current Password Re-auth | Email modifications and credential updates strictly mandate active password re-verification via secure password hashes. |
| **Session & Cookie Security** | Strict Cookie Attributes | `HttpOnly`, `SameSite=Lax`, and conditional HTTPS `Secure` flags configured to prevent cookie theft via XSS. |
| **Denial of Service (DoS)** | Strict Payload & Upload Limits | `MAX_CONTENT_LENGTH` enforced at 50 MB to prevent disk exhaustion and memory exhaustion attacks. |
| **IDOR Protection** | Object-Level Ownership Checks | Strict verification ensuring instructors can only modify and grade submissions belonging to their assigned courses. |
| **Sanitized Storage** | UUIDv4 & Extension Whitelisting | File uploads are assigned randomized UUIDs and validated against a strict MIME/extension whitelist, preventing remote code execution. |

---

## 👥 User Roles & Permissions Matrix

| Feature / Capability | Student | Teacher | Admin / Superadmin |
| :--- | :---: | :---: | :---: |
| Browse & Search Courses | ✅ | ✅ | ✅ |
| Enroll in Courses | ✅ | — | — |
| View Topics & Download Materials | ✅ (Enrolled) | ✅ (Owner) | ✅ (All) |
| Submit Assignment Solutions | ✅ | — | — |
| Create Courses & Topics | — | ✅ | ✅ |
| Upload & Delete Materials | — | ✅ (Owner) | ✅ |
| Grade Submissions & Give Feedback | — | ✅ (Owner) | ✅ |
| Manage User Roles & System Logs | — | — | ✅ |
| Review Teacher Applications | — | — | ✅ |

---

## 💻 Quick Start & Setup

### 1. Clone the repository
```bash
git clone https://github.com/sakayuke/coursescreator.git
cd coursescreator
```

### 2. Set up virtual environment
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/macOS:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration (.env)
```bash
cp .env.example .env
```
*Note: If no `DATABASE_URL` is specified in `.env`, the platform automatically initializes a local SQLite database (`app.db`) with zero configuration!*

### 5. Initialize Database & Seed Demo Accounts
```bash
# Optional: Seed pre-configured test users
flask --app run:app create-test-users

# Optional: Create master superadmin account
flask --app run:app create-admin
```

### 6. Run Development Server
```bash
flask --app run:app run
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 🧪 Testing Suite

Automated integration and permission tests are managed via `pytest`:

```bash
pytest -v
```

---

## 📄 License
This project is licensed under the MIT License.
