from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException

ROLE_PERMISSIONS = {
    "viewer": {"read"},
    "reviewer": {"read", "review"},
    "editor": {"read", "edit_layout"},
    "publisher": {"read", "review", "publish"},
    "admin": {"read", "review", "publish", "edit_layout", "manage_jobs"},
}


@dataclass(frozen=True)
class Actor:
    email: str
    role: str


def require_permission(permission: str):
    def dependency(
        x_user_email: str = Header(default="system@trackreco.local"),
        x_user_role: str = Header(default="admin"),
    ) -> Actor:
        allowed = ROLE_PERMISSIONS.get(x_user_role, set())
        if permission not in allowed:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "permission_denied",
                    "message": f"Role '{x_user_role}' lacks '{permission}' permission",
                },
            )
        return Actor(email=x_user_email, role=x_user_role)

    return Depends(dependency)
