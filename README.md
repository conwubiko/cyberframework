**CROF — Cyber Recovery Operational Framework**
A web application for assessing, scoring, and improving an organisation's cyber recovery posture. Built with Flask, SQLite, and a dark-themed Bootstrap 5 UI.

**What is CROF?**
CROF defines 8 functions and 49 controls that cover the full cyber recovery lifecycle:

Function	ID	Focus
Identify	ID	Critical assets, dependencies, recovery priorities
Control	CT	Backup access, network isolation, encryption, immutability
Map	MP	Recovery architecture, data flows, backup coverage
Plan	PL	Recovery plans, runbooks, decision trees, compliance
Playbook	PB	Ransomware, insider threat, supply chain response
Metrics	MT	RPO/RTO, backup success rate, MTTR, executive reporting
Test	TS	Recovery testing, tabletop exercises, red team validation
Improve	IM	Post-incident review, threat intel, training, automation
Assessments produce a maturity score (0-100%) mapped to five levels: Initial, Developing, Defined, Managed, and Optimising.

**Features**
Questionnaire-based assessments — guided wizard across all 8 CROF functions
Automated infrastructure scanning — 5 scan modules (backup config, network isolation, access controls, patch status, policy files)
Scoring engine — weighted per-control scoring with radar and bar charts
Report generation — PDF and HTML reports via WeasyPrint
Advisory engine — prioritised recommendations and phased remediation roadmap
Backup orchestration — rsync, Veeam, AWS Backup, Azure (encrypted credentials)
REST API — JWT-authenticated endpoints for assessments and framework data
Audit log — tracks login, assessment, scan, backup, and report events
User management — admin panel with role editing, account activation/deactivation
Multi-tenancy — organisation-based data isolation for admins and auditors
Email notifications — SMTP notifications for scan, backup, and assessment completion (console fallback in dev)
CSV/Excel export — download assessment responses and scan findings
Scheduled scans — daily, weekly, or monthly automated scans via background scheduler
Comparison view — side-by-side assessment comparison with dual radar charts and per-control diff
