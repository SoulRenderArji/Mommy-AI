USERS = {
    "brandon": ["super_admin"],
    "hailey": ["protected_user", "web_search"],
    "rowan": ["system_agent", "web_search"], # My own permissions
    "fenrir": ["super_admin", "system_agent"] # Security & DevOps agent
}

USER_ROLES = {
    "super_admin": {"system_update", "web_search"},
    "protected_user": {"web_search"},
}


def has_privilege(user: str, privilege: str) -> bool:
    """
    Checks if a user has the required privilege based on their assigned roles.
    """
    user_roles = USERS.get(user, [])
    for role in user_roles:
        if privilege in USER_ROLES.get(role, set()):
            return True
    return False