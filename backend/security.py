import secrets
from fastapi import Header, HTTPException, Request
def check_bearer(header: str | None, expected: str) -> None:
    if not header or not header.startswith("Bearer "): raise HTTPException(401, "Autenticación requerida")
    if not expected or not secrets.compare_digest(header[7:], expected): raise HTTPException(403, "Credencial sin permiso")
def require_admin(request: Request, authorization: str | None = Header(default=None)): check_bearer(authorization, request.app.state.settings.admin_token.get_secret_value())
def require_collector(request: Request, authorization: str | None = Header(default=None)): check_bearer(authorization, request.app.state.settings.collector_token.get_secret_value())
