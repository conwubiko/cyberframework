"""Backup orchestrator — unified interface for rsync, Veeam, AWS, Azure providers."""
import json
import os
import subprocess
import threading
from datetime import datetime, timezone

from app.extensions import db
from app.models.backup import BackupJob


def get_fernet():
    """Get Fernet cipher for encrypting credentials."""
    from cryptography.fernet import Fernet
    from flask import current_app
    key = current_app.config.get('FERNET_KEY', '')
    if not key:
        key = Fernet.generate_key().decode()
        current_app.config['FERNET_KEY'] = key
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_config(config_dict):
    """Encrypt a config dict to a string."""
    f = get_fernet()
    return f.encrypt(json.dumps(config_dict).encode()).decode()


def decrypt_config(encrypted_str):
    """Decrypt a config string back to a dict."""
    if not encrypted_str:
        return {}
    f = get_fernet()
    return json.loads(f.decrypt(encrypted_str.encode()).decode())


def run_backup(job_id, app):
    """Execute a backup job in background thread."""
    with app.app_context():
        job = db.session.get(BackupJob, job_id)
        if not job:
            return
        job.status = 'running'
        job.started_at = datetime.now(timezone.utc)
        job.progress = 0
        db.session.commit()

        try:
            config = decrypt_config(job.target_config) if job.target_config else {}
            dispatch = {
                'rsync': _run_rsync,
                'veeam': _run_veeam,
                'aws': _run_aws,
                'azure': _run_azure,
            }
            runner = dispatch.get(job.provider, _run_unsupported)
            log = runner(job, config)

            job.status = 'completed'
            job.progress = 100
            job.log = log
        except Exception as e:
            job.status = 'failed'
            job.log = f"Error: {str(e)}"

        job.completed_at = datetime.now(timezone.utc)
        db.session.commit()

        # Send email notification
        try:
            from app.models.user import User
            from app.services.email import notify_backup_result
            user = db.session.get(User, job.user_id)
            if user:
                notify_backup_result(user, job)
        except Exception:
            pass  # non-critical


def _run_rsync(job, config):
    """Execute rsync backup."""
    source = config.get('source', '.')
    dest = config.get('destination', '/tmp/backup')
    options = config.get('options', '-avz --progress')

    os.makedirs(dest, exist_ok=True)
    cmd = f'rsync {options} "{source}" "{dest}"'

    job.progress = 10
    db.session.commit()

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=3600, shell=True
        )
        job.progress = 90
        db.session.commit()

        if result.returncode == 0:
            return f"rsync completed successfully.\n{result.stdout[-500:]}"
        else:
            raise RuntimeError(f"rsync failed (exit {result.returncode}): {result.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("rsync timed out after 60 minutes.")


def _run_veeam(job, config):
    """Execute Veeam backup via REST API."""
    import requests
    host = config.get('host', 'localhost')
    port = config.get('port', 9419)
    username = config.get('username', '')
    password = config.get('password', '')
    job_name = config.get('job_name', '')

    base = f"https://{host}:{port}/api"

    # Authenticate
    job.progress = 10
    db.session.commit()

    auth_resp = requests.post(
        f"{base}/oauth2/token",
        data={'grant_type': 'password', 'username': username, 'password': password},
        verify=False, timeout=30
    )
    if auth_resp.status_code != 200:
        raise RuntimeError(f"Veeam auth failed: {auth_resp.status_code}")

    token = auth_resp.json().get('access_token', '')
    headers = {'Authorization': f'Bearer {token}'}

    # Start backup job
    job.progress = 30
    db.session.commit()

    jobs_resp = requests.get(f"{base}/v1/jobs", headers=headers, verify=False, timeout=30)
    if jobs_resp.status_code != 200:
        raise RuntimeError("Failed to list Veeam jobs.")

    target_job = None
    for j in jobs_resp.json().get('data', []):
        if j.get('name', '') == job_name:
            target_job = j
            break

    if not target_job:
        raise RuntimeError(f"Veeam job '{job_name}' not found.")

    start_resp = requests.post(
        f"{base}/v1/jobs/{target_job['id']}/start",
        headers=headers, verify=False, timeout=30
    )

    job.progress = 80
    db.session.commit()

    return f"Veeam job '{job_name}' started. Response: {start_resp.status_code}"


def _run_aws(job, config):
    """Execute AWS Backup via boto3."""
    try:
        import boto3
    except ImportError:
        raise RuntimeError("boto3 not installed. Install with: pip install boto3")

    vault_name = config.get('vault_name', 'Default')
    resource_arn = config.get('resource_arn', '')
    iam_role = config.get('iam_role_arn', '')
    region = config.get('region', 'us-east-1')

    job.progress = 10
    db.session.commit()

    client = boto3.client(
        'backup',
        region_name=region,
        aws_access_key_id=config.get('access_key', ''),
        aws_secret_access_key=config.get('secret_key', ''),
    )

    job.progress = 30
    db.session.commit()

    resp = client.start_backup_job(
        BackupVaultName=vault_name,
        ResourceArn=resource_arn,
        IamRoleArn=iam_role,
    )

    job.progress = 90
    db.session.commit()

    return f"AWS Backup job started: {resp.get('BackupJobId', 'unknown')}"


def _run_azure(job, config):
    """Execute Azure Backup (placeholder)."""
    job.progress = 50
    db.session.commit()
    return "Azure Backup integration is configured but requires azure-mgmt-recoveryservices. Configure in production."


def _run_unsupported(job, config):
    raise RuntimeError(f"Unsupported backup provider: {job.provider}")
