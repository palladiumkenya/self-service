"""Grant permissions added in Superset 6.x to custom roles that have users.

`superset init` only updates built-in roles, so organization roles migrated from
earlier versions lack these. Safe to run more than once.
"""
from superset.app import create_app

BUILT_IN_ROLES = {"Admin", "Alpha", "Gamma", "Public", "sql_lab"}
PERMISSIONS = [
    ("can_read", "CurrentUserRestApi"),
    ("can_read", "Theme"),
    ("can_language_pack", "Superset"),
    ("can_drill", "Dashboard"),
    ("can_view_chart_as_table", "Dashboard"),
    ("can_get_drill_info", "Dataset"),
]

app = create_app()
with app.app_context():
    sm = app.appbuilder.sm
    permission_views = []
    for permission, view in PERMISSIONS:
        permission_view = sm.find_permission_view_menu(permission, view)
        if permission_view is None:
            raise SystemExit(f"Missing permission {permission} on {view}: run superset init first")
        permission_views.append(permission_view)

    roles = [r for r in sm.get_all_roles() if r.name not in BUILT_IN_ROLES and r.user]
    added = 0
    for role in roles:
        for permission_view in permission_views:
            if permission_view not in role.permissions:
                sm.add_permission_role(role, permission_view)
                added += 1
    print(f"Updated {len(roles)} roles, added {added} permissions")
