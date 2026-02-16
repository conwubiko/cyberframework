"""
CROF — Cyber Recovery Operational Framework
8 Functions, ~49 Controls with questions, weights (1-3), and guidance text.
"""

CROF_FUNCTIONS = [
    {
        "id": "ID",
        "name": "Identify",
        "description": "Identify critical assets, dependencies, and recovery priorities.",
        "controls": [
            {"id": "ID-01", "title": "Asset Inventory", "weight": 3,
             "question": "Does the organisation maintain a comprehensive, up-to-date inventory of all critical IT and OT assets?",
             "guidance": "Maintain an automated asset discovery and inventory system covering servers, endpoints, network devices, cloud resources, and data stores. Review quarterly."},
            {"id": "ID-02", "title": "Data Classification", "weight": 2,
             "question": "Are data assets classified by sensitivity and criticality with defined handling requirements?",
             "guidance": "Implement a data classification scheme (e.g. Public, Internal, Confidential, Restricted) with labelling, handling, and storage requirements for each tier."},
            {"id": "ID-03", "title": "Business Impact Analysis", "weight": 3,
             "question": "Has a Business Impact Analysis (BIA) been completed to identify critical processes and their recovery priorities?",
             "guidance": "Conduct a BIA annually that maps critical business processes to supporting IT systems and defines RPO/RTO targets."},
            {"id": "ID-04", "title": "Dependency Mapping", "weight": 2,
             "question": "Are inter-system and third-party dependencies documented for critical services?",
             "guidance": "Map upstream and downstream dependencies including cloud providers, SaaS applications, DNS, authentication, and supply chain integrations."},
            {"id": "ID-05", "title": "Recovery Priority List", "weight": 2,
             "question": "Is there a prioritised list of systems and data for recovery in order of business criticality?",
             "guidance": "Maintain a tiered recovery priority list (Tier 1: < 4 hrs, Tier 2: < 24 hrs, Tier 3: < 72 hrs) reviewed by business and IT stakeholders."},
            {"id": "ID-06", "title": "Crown Jewel Identification", "weight": 3,
             "question": "Has the organisation identified its 'crown jewel' assets — the systems and data whose loss would be existential?",
             "guidance": "Identify the top 10-20 assets whose compromise would cause maximum business impact. Apply the highest protection and recovery controls to these assets."},
        ]
    },
    {
        "id": "CT",
        "name": "Control",
        "description": "Implement access, network, and integrity controls to protect recovery infrastructure.",
        "controls": [
            {"id": "CT-01", "title": "Backup Access Controls", "weight": 3,
             "question": "Are backup systems protected with dedicated credentials, MFA, and role-based access?",
             "guidance": "Use separate privileged accounts for backup administration with MFA enforced. Implement RBAC limiting who can modify, delete, or restore backups."},
            {"id": "CT-02", "title": "Network Isolation", "weight": 3,
             "question": "Is the backup and recovery infrastructure on a separate, segmented network?",
             "guidance": "Place backup servers, management interfaces, and storage targets on an isolated VLAN/subnet with firewall rules restricting access to authorised systems only."},
            {"id": "CT-03", "title": "Encryption at Rest", "weight": 2,
             "question": "Are all backup data encrypted at rest using strong algorithms (AES-256 or equivalent)?",
             "guidance": "Enable encryption on all backup targets. Use AES-256 with keys managed in a separate key management system (KMS) not co-located with backup data."},
            {"id": "CT-04", "title": "Encryption in Transit", "weight": 2,
             "question": "Is data encrypted during transfer between production and backup environments?",
             "guidance": "Use TLS 1.2+ or IPsec for all backup data transfers. Verify certificate validation is enabled and reject self-signed certificates in production."},
            {"id": "CT-05", "title": "Immutable Backups", "weight": 3,
             "question": "Are critical backups stored in an immutable or WORM (Write Once Read Many) format?",
             "guidance": "Configure immutability locks on backup storage (e.g. AWS S3 Object Lock, Azure Immutable Blob, Veeam Hardened Repository) for at least 30 days."},
            {"id": "CT-06", "title": "Air-Gapped Copy", "weight": 3,
             "question": "Is at least one copy of critical backups stored in an air-gapped or logically isolated environment?",
             "guidance": "Maintain an offline or air-gapped backup copy that cannot be reached from the production network. Test restoration from this copy quarterly."},
            {"id": "CT-07", "title": "Integrity Verification", "weight": 2,
             "question": "Are backup integrity checks (checksums, verification restores) performed regularly?",
             "guidance": "Run automated integrity verification on all backups weekly. Perform sample restoration tests monthly to confirm data recoverability."},
        ]
    },
    {
        "id": "MP",
        "name": "Map",
        "description": "Map recovery processes, data flows, and infrastructure topology.",
        "controls": [
            {"id": "MP-01", "title": "Recovery Architecture Diagram", "weight": 2,
             "question": "Is there a documented architecture diagram showing backup and recovery infrastructure?",
             "guidance": "Maintain up-to-date architecture diagrams including backup servers, replication targets, network paths, and recovery sites. Update after any infrastructure change."},
            {"id": "MP-02", "title": "Data Flow Mapping", "weight": 2,
             "question": "Are data flows between production and backup environments documented?",
             "guidance": "Document all data flows including backup schedules, replication paths, bandwidth requirements, and retention policies for each data flow."},
            {"id": "MP-03", "title": "Recovery Site Documentation", "weight": 2,
             "question": "Are recovery sites (DR sites, cloud regions) documented with capacity and connectivity details?",
             "guidance": "Document each recovery site with compute capacity, storage availability, network bandwidth, and estimated failover time."},
            {"id": "MP-04", "title": "Backup Coverage Map", "weight": 3,
             "question": "Is there a documented map showing backup coverage for all critical systems?",
             "guidance": "Maintain a backup coverage matrix mapping every critical system to its backup method, schedule, retention, and verified recovery status."},
            {"id": "MP-05", "title": "Third-Party Recovery Mapping", "weight": 2,
             "question": "Are third-party and cloud service recovery capabilities documented?",
             "guidance": "Document SLA/SLO commitments from cloud and SaaS providers for data recovery, including RPO/RTO guarantees and shared responsibility boundaries."},
            {"id": "MP-06", "title": "Communication Channel Map", "weight": 1,
             "question": "Are out-of-band communication channels for use during a cyber incident documented?",
             "guidance": "Document alternative communication methods (satellite phones, personal mobiles, encrypted messaging) available when primary email and VoIP are compromised."},
        ]
    },
    {
        "id": "PL",
        "name": "Plan",
        "description": "Develop and maintain cyber recovery plans and runbooks.",
        "controls": [
            {"id": "PL-01", "title": "Cyber Recovery Plan", "weight": 3,
             "question": "Does the organisation have a dedicated Cyber Recovery Plan (distinct from traditional DR)?",
             "guidance": "Develop a Cyber Recovery Plan that specifically addresses recovery from destructive cyber attacks, ransomware, and data integrity compromises. Review annually."},
            {"id": "PL-02", "title": "Detailed Runbooks", "weight": 2,
             "question": "Are there detailed, step-by-step runbooks for recovering each critical system?",
             "guidance": "Create system-specific runbooks with exact commands, credentials (vault references), and validation steps. Ensure they work for staff unfamiliar with the system."},
            {"id": "PL-03", "title": "Decision Trees", "weight": 2,
             "question": "Do recovery plans include decision trees for different attack scenarios (ransomware, wiper, insider)?",
             "guidance": "Include decision trees that guide the recovery team based on attack type, scope of compromise, and available clean backups."},
            {"id": "PL-04", "title": "Stakeholder Roles & RACI", "weight": 2,
             "question": "Are roles and responsibilities for cyber recovery clearly defined in a RACI matrix?",
             "guidance": "Define a RACI matrix covering IT, Security, Executive, Legal, Communications, and external parties for each phase of recovery."},
            {"id": "PL-05", "title": "Plan Review Cycle", "weight": 1,
             "question": "Is the cyber recovery plan reviewed and updated at least annually or after significant changes?",
             "guidance": "Schedule formal plan reviews annually and after any major infrastructure change, organisational restructure, or lessons learned from incidents/tests."},
            {"id": "PL-06", "title": "Legal & Regulatory Compliance", "weight": 2,
             "question": "Does the plan address legal, regulatory, and contractual recovery obligations?",
             "guidance": "Include compliance requirements for GDPR, HIPAA, PCI-DSS, sector-specific regulations, and contractual SLAs in recovery planning and execution."},
        ]
    },
    {
        "id": "PB",
        "name": "Playbook",
        "description": "Define incident response playbooks integrated with recovery procedures.",
        "controls": [
            {"id": "PB-01", "title": "Ransomware Playbook", "weight": 3,
             "question": "Is there a specific playbook for responding to and recovering from ransomware attacks?",
             "guidance": "Develop a ransomware playbook covering containment, eradication, clean backup identification, restoration sequencing, and post-recovery validation."},
            {"id": "PB-02", "title": "Data Integrity Playbook", "weight": 2,
             "question": "Is there a playbook for recovering from data corruption or integrity attacks?",
             "guidance": "Address scenarios where data has been subtly modified rather than encrypted. Include forensic validation steps to identify the last known-good backup."},
            {"id": "PB-03", "title": "Insider Threat Playbook", "weight": 2,
             "question": "Is there a playbook for recovery from malicious insider actions?",
             "guidance": "Cover credential revocation, access log forensics, and recovery from deliberately deleted or modified backups by authorised personnel."},
            {"id": "PB-04", "title": "Supply Chain Playbook", "weight": 2,
             "question": "Is there a playbook for recovering from a supply chain or third-party compromise?",
             "guidance": "Address recovery when a trusted vendor update, library, or service has been compromised. Include isolation of affected components and clean rebuild procedures."},
            {"id": "PB-05", "title": "Escalation & Notification Procedures", "weight": 2,
             "question": "Do playbooks include clear escalation paths and notification procedures?",
             "guidance": "Define escalation thresholds, notification timelines for regulators and affected parties, and templates for internal and external communications."},
            {"id": "PB-06", "title": "Playbook Integration with IR", "weight": 2,
             "question": "Are recovery playbooks integrated with the broader incident response process?",
             "guidance": "Ensure recovery playbooks link to IR playbooks with clear handoff points between containment/eradication (IR) and restoration (Recovery) phases."},
        ]
    },
    {
        "id": "MT",
        "name": "Metrics",
        "description": "Define and track recovery metrics and KPIs.",
        "controls": [
            {"id": "MT-01", "title": "RPO/RTO Defined", "weight": 3,
             "question": "Are Recovery Point Objectives (RPO) and Recovery Time Objectives (RTO) formally defined for all critical systems?",
             "guidance": "Define RPO and RTO for each critical system based on BIA results. Ensure backup schedules and recovery capabilities can meet these objectives."},
            {"id": "MT-02", "title": "Backup Success Rate", "weight": 2,
             "question": "Is the backup job success rate tracked and reported regularly?",
             "guidance": "Monitor backup success rates daily with automated alerting for failures. Target 99%+ success rate with root cause analysis for all failures."},
            {"id": "MT-03", "title": "Recovery Test Results", "weight": 2,
             "question": "Are recovery test results measured against defined RPO/RTO targets?",
             "guidance": "Track actual recovery times and data currency against RPO/RTO targets during every test. Report gaps and remediation plans to management."},
            {"id": "MT-04", "title": "Mean Time to Recovery", "weight": 2,
             "question": "Is Mean Time to Recovery (MTTR) tracked for each critical system?",
             "guidance": "Measure MTTR during tests and actual incidents. Establish baselines and improvement targets for each system tier."},
            {"id": "MT-05", "title": "Coverage Metrics", "weight": 2,
             "question": "Is the percentage of critical systems with verified, tested backups tracked?",
             "guidance": "Maintain a dashboard showing backup coverage percentage, last verified restore date, and backup age for all critical systems."},
            {"id": "MT-06", "title": "Executive Reporting", "weight": 1,
             "question": "Are cyber recovery metrics reported to executive leadership and the board regularly?",
             "guidance": "Produce quarterly executive reports summarising recovery readiness, test results, compliance status, and risk posture changes."},
        ]
    },
    {
        "id": "TS",
        "name": "Test",
        "description": "Regularly test and validate recovery capabilities.",
        "controls": [
            {"id": "TS-01", "title": "Regular Recovery Testing", "weight": 3,
             "question": "Are full recovery tests conducted at least quarterly for critical systems?",
             "guidance": "Conduct quarterly recovery tests that include full system restoration from backup. Rotate which systems are tested to cover all Tier 1 systems annually."},
            {"id": "TS-02", "title": "Tabletop Exercises", "weight": 2,
             "question": "Are tabletop exercises conducted to rehearse cyber recovery scenarios?",
             "guidance": "Run semi-annual tabletop exercises involving IT, security, executives, and legal. Use realistic scenarios based on current threat landscape."},
            {"id": "TS-03", "title": "Red Team/Purple Team Testing", "weight": 2,
             "question": "Has red team or purple team testing been used to validate recovery controls?",
             "guidance": "Engage red team to test whether recovery infrastructure can be compromised during a simulated attack. Validate detection and response capabilities."},
            {"id": "TS-04", "title": "Isolated Recovery Environment Testing", "weight": 3,
             "question": "Are recovery tests performed in an isolated (clean room) environment?",
             "guidance": "Test recovery in a network-isolated environment to simulate recovery from a fully compromised production network. Verify systems function without production dependencies."},
            {"id": "TS-05", "title": "Backup Restoration Validation", "weight": 2,
             "question": "Are restored systems validated for integrity and absence of malware before going live?",
             "guidance": "Scan all restored systems with updated AV/EDR before reconnecting to production. Verify data integrity with checksums and application-level validation."},
            {"id": "TS-06", "title": "Test Documentation & Lessons Learned", "weight": 1,
             "question": "Are test results documented with formal lessons learned and remediation actions?",
             "guidance": "Document all test results with findings, gaps, and time-bound remediation actions. Track remediation to closure and feed into plan updates."},
        ]
    },
    {
        "id": "IM",
        "name": "Improve",
        "description": "Continuously improve recovery capabilities based on lessons learned.",
        "controls": [
            {"id": "IM-01", "title": "Post-Incident Review", "weight": 3,
             "question": "Are formal post-incident reviews conducted after every cyber incident or recovery test?",
             "guidance": "Conduct blameless post-incident reviews within 5 business days. Document root causes, what worked, what didn't, and specific improvement actions."},
            {"id": "IM-02", "title": "Remediation Tracking", "weight": 2,
             "question": "Are improvement actions from reviews and tests tracked to closure?",
             "guidance": "Use a formal tracking system (e.g. JIRA, ServiceNow) for all remediation actions with owners, due dates, and status reporting."},
            {"id": "IM-03", "title": "Threat Intelligence Integration", "weight": 2,
             "question": "Is threat intelligence used to update recovery plans and controls?",
             "guidance": "Subscribe to threat intelligence feeds and update recovery playbooks when new attack techniques target backup and recovery infrastructure."},
            {"id": "IM-04", "title": "Technology Refresh", "weight": 2,
             "question": "Is recovery technology evaluated and refreshed on a regular cycle?",
             "guidance": "Review backup and recovery technology annually against current requirements, vendor roadmaps, and emerging threats. Plan refresh cycles of 3-5 years."},
            {"id": "IM-05", "title": "Training & Awareness", "weight": 2,
             "question": "Do recovery team members receive regular training on tools, processes, and emerging threats?",
             "guidance": "Provide annual training on recovery tools and procedures. Include cyber recovery scenarios in general security awareness programmes."},
            {"id": "IM-06", "title": "Maturity Assessment", "weight": 1,
             "question": "Is the organisation's cyber recovery maturity assessed periodically against a framework?",
             "guidance": "Conduct annual maturity assessments using CROF or equivalent frameworks. Track maturity level progression and benchmark against industry peers."},
            {"id": "IM-07", "title": "Automation Improvement", "weight": 2,
             "question": "Is the organisation actively working to automate recovery processes?",
             "guidance": "Identify manual recovery steps that can be automated. Implement infrastructure-as-code, automated failover, and orchestrated recovery workflows."},
        ]
    }
]

# Maturity levels based on overall percentage score
MATURITY_LEVELS = [
    (0, 20, "Initial", "Ad-hoc, undocumented recovery processes with significant gaps."),
    (20, 40, "Developing", "Some recovery processes documented but inconsistently applied."),
    (40, 60, "Defined", "Recovery processes documented, standardised, and mostly followed."),
    (60, 80, "Managed", "Recovery processes measured, tested, and actively managed."),
    (80, 100.1, "Optimising", "Continuous improvement with automated, regularly tested recovery capabilities."),
]


def get_all_controls():
    """Return a flat list of all controls with their function info."""
    controls = []
    for func in CROF_FUNCTIONS:
        for ctrl in func["controls"]:
            controls.append({**ctrl, "function_id": func["id"], "function_name": func["name"]})
    return controls


def get_function_by_id(function_id):
    for func in CROF_FUNCTIONS:
        if func["id"] == function_id:
            return func
    return None


def get_maturity_level(score_pct):
    for low, high, name, desc in MATURITY_LEVELS:
        if low <= score_pct < high:
            return name, desc
    return "Initial", MATURITY_LEVELS[0][3]
