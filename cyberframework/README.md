# CROF — Cyber Recovery Operational Framework

A web application for assessing, scoring, and improving an organisation's cyber recovery posture. Built with Flask, SQLite, and a dark-themed Bootstrap 5 UI.

## What is CROF?

CROF defines **8 functions** and **49 controls** that cover the full cyber recovery lifecycle:

| Function | ID | Focus |
|---|---|---|
| Identify | ID | Critical assets, dependencies, recovery priorities |
| Control | CT | Backup access, network isolation, encryption, immutability |
| Map | MP | Recovery architecture, data flows, backup coverage |
| Plan | PL | Recovery plans, runbooks, decision trees, compliance |
| Playbook | PB | Ransomware, insider threat, supply chain response |
| Metrics | MT | RPO/RTO, backup success rate, MTTR, executive reporting |
| Test | TS | Recovery testing, tabletop exercises, red team validation |
| Improve | IM | Post-incident review, threat intel, training, automation |

Assessments produce a **maturity score** (0-100%) mapped to five levels: Initial, Developing, Defined, Managed, and Optimising.

## Features

- **Questionnaire-based assessments** — guided wizard across all 8 CROF functions
- **Automated infrastructure scanning** — 5 scan modules (backup config, network isolation, access controls, patch status, policy files)
- **Scoring engine** — weighted per-control scoring with radar and bar charts
- **Report generation** — PDF and HTML reports via WeasyPrint
- **Advisory engine** — prioritised recommendations and phased remediation roadmap
- **Backup orchestration** — rsync, Veeam, AWS Backup, Azure (encrypted credentials)
- **REST API** — JWT-authenticated endpoints for assessments and framework data
- **Audit log** — tracks login, assessment, scan, backup, and report events
- **User management** — admin panel with role editing, account activation/deactivation
- **Multi-tenancy** — organisation-based data isolation for admins and auditors
- **Email notifications** — SMTP notifications for scan, backup, and assessment completion (console fallback in dev)
- **CSV/Excel export** — download assessment responses and scan findings
- **Scheduled scans** — daily, weekly, or monthly automated scans via background scheduler
- **Comparison view** — side-by-side assessment comparison with dual radar charts and per-control diff

## Quick Start

```bash
# Clone and install
git clone https://github.com/conwubiko/cyberframework.git
cd cyberframework
pip install -r requirements.txt

# Run
python app.py
```

Open **http://localhost:5000**. The first registered user becomes admin.

## Configuration

Set these environment variables (or create a `.env` file):

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Flask session secret | `crof-dev-secret-change-in-prod` |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///instance/crof.db` |
| `FERNET_KEY` | Encryption key for backup credentials | Auto-generated |
| `JWT_SECRET` | JWT signing secret | `crof-jwt-secret-change-in-prod` |
| `MAIL_SERVER` | SMTP server (optional) | Empty (console logging) |
| `MAIL_PORT` | SMTP port | `587` |
| `MAIL_USERNAME` | SMTP username | Empty |
| `MAIL_PASSWORD` | SMTP password | Empty |
| `MAIL_DEFAULT_SENDER` | From address | `crof@localhost` |

## Project Structure

```
cyberframework/
├── app.py                          # Entry point
├── config.py                       # Configuration
├── requirements.txt                # Dependencies
├── app/
│   ├── __init__.py                 # App factory
│   ├── extensions.py               # Flask extensions
│   ├── models/                     # SQLAlchemy models
│   │   ├── user.py                 #   User, roles, org membership
│   │   ├── assessment.py           #   Assessment & responses
│   │   ├── scan.py                 #   ScanJob & findings
│   │   ├── report.py               #   Generated reports
│   │   ├── backup.py               #   Backup jobs
│   │   ├── audit.py                #   Audit log entries
│   │   ├── organisation.py         #   Multi-tenancy orgs
│   │   ├── notification.py         #   Email preferences
│   │   └── schedule.py             #   Scheduled scans
│   ├── routes/                     # Blueprint routes
│   │   ├── auth.py                 #   Login, register, logout
│   │   ├── dashboard.py            #   Dashboard
│   │   ├── assessment.py           #   Assessment CRUD & wizard
│   │   ├── scanner.py              #   Scan management
│   │   ├── report.py               #   Report generation
│   │   ├── backup.py               #   Backup operations
│   │   ├── advisory.py             #   Advisory & roadmap
│   │   ├── api.py                  #   REST API (JWT)
│   │   ├── admin.py                #   Audit log, users, orgs
│   │   ├── settings.py             #   Notification preferences
│   │   ├── export.py               #   CSV/Excel downloads
│   │   ├── schedule.py             #   Scheduled scans
│   │   └── compare.py              #   Assessment comparison
│   ├── services/                   # Business logic
│   │   ├── scoring.py              #   Scoring & comparison engine
│   │   ├── scanner_engine.py       #   5 scan modules
│   │   ├── report_generator.py     #   PDF/HTML reports
│   │   ├── advisory_engine.py      #   Recommendations
│   │   ├── backup_orchestrator.py  #   Backup providers
│   │   ├── audit.py                #   Audit logging
│   │   ├── email.py                #   Email notifications
│   │   ├── exporter.py             #   CSV/Excel export
│   │   ├── scheduler.py            #   Background scan scheduler
│   │   └── tenancy.py              #   Org-based query scoping
│   ├── data/
│   │   └── framework_controls.py   #   CROF framework definition
│   └── templates/                  #   Jinja2 templates (dark theme)
└── tests/
    └── test_app.py                 #   31 tests
```

## Tests

```bash
python -m pytest tests/ -v
```

31 tests covering framework data, scoring, authentication, and all 7 feature modules.

## Tech Stack

- **Backend:** Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- **Database:** SQLite
- **Frontend:** Bootstrap 5 (dark theme), Chart.js
- **Reports:** WeasyPrint
- **Auth:** Session-based (UI) + JWT (API)
- **Export:** openpyxl (Excel), csv (stdlib)

## License

MIT
