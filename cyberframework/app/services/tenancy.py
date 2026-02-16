"""Multi-tenancy helpers for organisation isolation."""
from flask_login import current_user


def get_user_org_id():
    """Return the current user's organisation_id, or None."""
    if current_user and current_user.is_authenticated:
        return current_user.organisation_id
    return None


def org_query_filter(query, model):
    """Scope a query by organisation for non-admin users.

    - Admins/auditors see all data within their org.
    - Regular users see only their own data.
    - If user has no org, no org filter is applied.
    """
    if not current_user or not current_user.is_authenticated:
        return query

    org_id = current_user.organisation_id
    if org_id and hasattr(model, 'organisation_id'):
        if current_user.role in ('admin', 'auditor'):
            query = query.filter(model.organisation_id == org_id)
        else:
            query = query.filter(model.user_id == current_user.id)
    else:
        if current_user.role not in ('admin', 'auditor'):
            query = query.filter(model.user_id == current_user.id)

    return query
