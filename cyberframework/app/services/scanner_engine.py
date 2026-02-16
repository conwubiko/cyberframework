"""Scanner engine — modular infrastructure scan with 5 modules."""
import subprocess
import os
import json
import platform
from datetime import datetime, timezone
from app.extensions import db
from app.models.scan import ScanJob, ScanFinding


SCAN_MODULES = [
    {'id': 'backup_config', 'name': 'Backup Configuration', 'weight': 20},
    {'id': 'network_isolation', 'name': 'Network Isolation', 'weight': 20},
    {'id': 'access_controls', 'name': 'Access Controls', 'weight': 20},
    {'id': 'patch_status', 'name': 'Patch Status', 'weight': 20},
    {'id': 'policy_files', 'name': 'Policy Files', 'weight': 20},
]


def run_scan(scan_job_id, app):
    """Run all scan modules for a scan job. Called in background thread."""
    with app.app_context():
        job = db.session.get(ScanJob, scan_job_id)
        if not job:
            return
        job.status = 'running'
        job.started_at = datetime.now(timezone.utc)
        db.session.commit()

        try:
            total_modules = len(SCAN_MODULES)
            for i, module in enumerate(SCAN_MODULES):
                findings = _run_module(module['id'], job.target)
                for f in findings:
                    finding = ScanFinding(
                        scan_job_id=job.id,
                        control_id=f.get('control_id', ''),
                        severity=f.get('severity', 'info'),
                        title=f.get('title', ''),
                        description=f.get('description', ''),
                        remediation=f.get('remediation', ''),
                    )
                    db.session.add(finding)

                job.progress = int(((i + 1) / total_modules) * 100)
                db.session.commit()

            job.status = 'completed'
            job.completed_at = datetime.now(timezone.utc)

            # Send email notification
            try:
                from app.models.user import User
                from app.services.email import notify_scan_complete
                user = db.session.get(User, job.user_id)
                if user:
                    notify_scan_complete(user, job)
            except Exception:
                pass  # non-critical

        except Exception as e:
            job.status = 'failed'
            job.completed_at = datetime.now(timezone.utc)
            db.session.add(ScanFinding(
                scan_job_id=job.id,
                severity='critical',
                title='Scan Engine Error',
                description=str(e),
                remediation='Check scanner configuration and target accessibility.',
            ))
        db.session.commit()


def _run_module(module_id, target):
    """Dispatch to the correct scan module."""
    dispatch = {
        'backup_config': _scan_backup_config,
        'network_isolation': _scan_network_isolation,
        'access_controls': _scan_access_controls,
        'patch_status': _scan_patch_status,
        'policy_files': _scan_policy_files,
    }
    func = dispatch.get(module_id, lambda t: [])
    return func(target)


def _safe_run(cmd, timeout=10):
    """Safely run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, shell=True
        )
        return result.stdout.strip(), result.returncode
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return '', -1


def _scan_backup_config(target):
    findings = []
    is_windows = platform.system() == 'Windows'

    # Check for scheduled backup tasks
    if is_windows:
        out, rc = _safe_run('schtasks /query /fo CSV /nh')
        if rc == 0 and out:
            has_backup = any(kw in out.lower() for kw in ['backup', 'veeam', 'rsync', 'robocopy'])
            if not has_backup:
                findings.append({
                    'control_id': 'CT-01',
                    'severity': 'high',
                    'title': 'No scheduled backup tasks detected',
                    'description': 'No scheduled tasks related to backup operations were found on this system.',
                    'remediation': 'Configure automated backup schedules using enterprise backup software or built-in tools.',
                })
            else:
                findings.append({
                    'control_id': 'CT-01',
                    'severity': 'info',
                    'title': 'Scheduled backup tasks detected',
                    'description': 'Backup-related scheduled tasks were found on this system.',
                    'remediation': 'Verify these tasks run successfully and cover all critical data.',
                })
    else:
        out, rc = _safe_run('crontab -l 2>/dev/null')
        if rc != 0 or not out:
            findings.append({
                'control_id': 'CT-01',
                'severity': 'high',
                'title': 'No crontab backup jobs detected',
                'description': 'No crontab entries found that could indicate scheduled backups.',
                'remediation': 'Configure automated backup schedules via cron or enterprise backup software.',
            })
        elif not any(kw in out.lower() for kw in ['backup', 'rsync', 'tar', 'dump', 'borg']):
            findings.append({
                'control_id': 'CT-01',
                'severity': 'medium',
                'title': 'No backup-related cron jobs found',
                'description': 'Crontab exists but no backup-related entries were identified.',
                'remediation': 'Review crontab entries and ensure backup jobs are properly scheduled.',
            })

    # Check for backup directories
    backup_dirs = ['C:\\Backup', 'C:\\Backups', 'D:\\Backup'] if is_windows else ['/backup', '/var/backup', '/mnt/backup']
    found_dirs = [d for d in backup_dirs if os.path.isdir(d)]
    if not found_dirs:
        findings.append({
            'control_id': 'MP-04',
            'severity': 'medium',
            'title': 'No standard backup directories found',
            'description': f'Checked {", ".join(backup_dirs)} — none exist.',
            'remediation': 'Ensure backup storage locations are properly configured and accessible.',
        })

    return findings


def _scan_network_isolation(target):
    findings = []
    is_windows = platform.system() == 'Windows'

    if is_windows:
        out, rc = _safe_run('netsh advfirewall show allprofiles state')
        if rc == 0:
            if 'OFF' in out.upper():
                findings.append({
                    'control_id': 'CT-02',
                    'severity': 'critical',
                    'title': 'Windows Firewall has disabled profiles',
                    'description': 'One or more Windows Firewall profiles are disabled.',
                    'remediation': 'Enable Windows Firewall for all profiles (Domain, Private, Public).',
                })
            else:
                findings.append({
                    'control_id': 'CT-02',
                    'severity': 'info',
                    'title': 'Windows Firewall is active',
                    'description': 'All Windows Firewall profiles appear to be enabled.',
                    'remediation': 'Review firewall rules to ensure backup infrastructure is properly segmented.',
                })
        # Check for open high-risk ports
        out, rc = _safe_run('netstat -an')
        if rc == 0:
            risky_ports = ['0.0.0.0:3389', '0.0.0.0:445', '0.0.0.0:23']
            open_risky = [p for p in risky_ports if p in out]
            if open_risky:
                findings.append({
                    'control_id': 'CT-02',
                    'severity': 'high',
                    'title': 'High-risk ports open on all interfaces',
                    'description': f'Ports listening on all interfaces: {", ".join(open_risky)}',
                    'remediation': 'Restrict high-risk services to specific interfaces/VLANs.',
                })
    else:
        out, rc = _safe_run('iptables -L -n 2>/dev/null || ufw status 2>/dev/null')
        if 'inactive' in out.lower() or (rc != 0 and not out):
            findings.append({
                'control_id': 'CT-02',
                'severity': 'critical',
                'title': 'No active firewall detected',
                'description': 'Neither iptables rules nor ufw appear to be active.',
                'remediation': 'Enable and configure host-based firewall (iptables/ufw/firewalld).',
            })

    return findings


def _scan_access_controls(target):
    findings = []
    is_windows = platform.system() == 'Windows'

    if is_windows:
        out, rc = _safe_run('net user')
        if rc == 0:
            # Check for default/guest accounts
            if 'Guest' in out:
                out2, _ = _safe_run('net user Guest')
                if 'Account active' in out2 and 'Yes' in out2:
                    findings.append({
                        'control_id': 'CT-01',
                        'severity': 'high',
                        'title': 'Guest account is active',
                        'description': 'The built-in Guest account is enabled on this system.',
                        'remediation': 'Disable the Guest account: net user Guest /active:no',
                    })
        # Check password policy
        out, rc = _safe_run('net accounts')
        if rc == 0 and 'Minimum password length' in out:
            for line in out.splitlines():
                if 'Minimum password length' in line:
                    try:
                        length = int(line.split(':')[-1].strip())
                        if length < 12:
                            findings.append({
                                'control_id': 'CT-01',
                                'severity': 'medium',
                                'title': f'Weak minimum password length ({length})',
                                'description': f'Minimum password length is {length} characters.',
                                'remediation': 'Set minimum password length to 12+ characters via Group Policy.',
                            })
                    except ValueError:
                        pass
    else:
        # Check for passwordless sudo
        out, rc = _safe_run("grep -r 'NOPASSWD' /etc/sudoers /etc/sudoers.d/ 2>/dev/null")
        if out:
            findings.append({
                'control_id': 'CT-01',
                'severity': 'high',
                'title': 'NOPASSWD sudo entries found',
                'description': 'Some users can execute sudo commands without a password.',
                'remediation': 'Remove NOPASSWD entries from sudoers and require password for privileged operations.',
            })

    return findings


def _scan_patch_status(target):
    findings = []
    is_windows = platform.system() == 'Windows'

    if is_windows:
        # Check last update date via PowerShell
        out, rc = _safe_run(
            'powershell -Command "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1 -ExpandProperty InstalledOn"',
            timeout=30
        )
        if rc == 0 and out:
            try:
                last_update = datetime.strptime(out.strip().split()[0], '%m/%d/%Y')
                days_ago = (datetime.now() - last_update).days
                if days_ago > 90:
                    findings.append({
                        'control_id': 'IM-04',
                        'severity': 'critical',
                        'title': f'System not patched in {days_ago} days',
                        'description': f'Last Windows update was installed on {out.strip()}, which is {days_ago} days ago.',
                        'remediation': 'Apply pending Windows updates immediately and enable automatic updates.',
                    })
                elif days_ago > 30:
                    findings.append({
                        'control_id': 'IM-04',
                        'severity': 'high',
                        'title': f'System patches are {days_ago} days old',
                        'description': f'Last update: {out.strip()}.',
                        'remediation': 'Review and apply pending updates within the maintenance window.',
                    })
                else:
                    findings.append({
                        'control_id': 'IM-04',
                        'severity': 'info',
                        'title': 'System patches are current',
                        'description': f'Last update installed {days_ago} days ago.',
                        'remediation': 'Continue regular patching schedule.',
                    })
            except (ValueError, IndexError):
                findings.append({
                    'control_id': 'IM-04',
                    'severity': 'medium',
                    'title': 'Could not determine patch date',
                    'description': 'Unable to parse last update date.',
                    'remediation': 'Manually verify Windows Update status.',
                })
    else:
        out, rc = _safe_run('apt list --upgradable 2>/dev/null | wc -l')
        if rc == 0:
            try:
                count = int(out.strip()) - 1
                if count > 50:
                    findings.append({
                        'control_id': 'IM-04',
                        'severity': 'critical',
                        'title': f'{count} packages need updating',
                        'description': f'There are {count} packages with available updates.',
                        'remediation': 'Apply updates: sudo apt update && sudo apt upgrade',
                    })
                elif count > 10:
                    findings.append({
                        'control_id': 'IM-04',
                        'severity': 'high',
                        'title': f'{count} packages need updating',
                        'description': f'There are {count} packages with available updates.',
                        'remediation': 'Schedule maintenance window to apply pending updates.',
                    })
            except ValueError:
                pass

    return findings


def _scan_policy_files(target):
    findings = []
    is_windows = platform.system() == 'Windows'

    # Check for common security policy documents
    policy_locations = []
    if is_windows:
        for drive in ['C:', 'D:']:
            for folder in ['Policies', 'Security', 'IT Policies', 'Documentation']:
                policy_locations.append(os.path.join(drive, os.sep, folder))
    else:
        policy_locations = ['/etc/security', '/opt/policies', '/var/lib/security']

    found_policies = [p for p in policy_locations if os.path.isdir(p)]
    if not found_policies:
        findings.append({
            'control_id': 'PL-01',
            'severity': 'medium',
            'title': 'No policy document directories found',
            'description': f'Checked: {", ".join(policy_locations[:4])}...',
            'remediation': 'Create and maintain security policy documentation in a standard location.',
        })

    # Check for encryption configuration
    if is_windows:
        out, rc = _safe_run('manage-bde -status C: 2>nul')
        if rc == 0:
            if 'Fully Encrypted' in out or 'Protection On' in out:
                findings.append({
                    'control_id': 'CT-03',
                    'severity': 'info',
                    'title': 'BitLocker encryption is active on C:',
                    'description': 'The system drive is encrypted with BitLocker.',
                    'remediation': 'Ensure recovery keys are securely stored and backup volumes are also encrypted.',
                })
            else:
                findings.append({
                    'control_id': 'CT-03',
                    'severity': 'high',
                    'title': 'BitLocker not active on system drive',
                    'description': 'The C: drive does not appear to be encrypted with BitLocker.',
                    'remediation': 'Enable BitLocker encryption on all drives containing sensitive data.',
                })
    else:
        out, rc = _safe_run('lsblk -o NAME,FSTYPE,TYPE | grep -i crypt')
        if not out:
            findings.append({
                'control_id': 'CT-03',
                'severity': 'high',
                'title': 'No encrypted volumes detected',
                'description': 'No LUKS or dm-crypt volumes were found.',
                'remediation': 'Enable disk encryption for volumes containing backup or sensitive data.',
            })

    return findings
