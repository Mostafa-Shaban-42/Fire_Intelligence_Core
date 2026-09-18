from typing import Optional, Dict, Any
import uuid
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from db.repositories.audit import AuditRepository

async def record_audit_event(
    session: AsyncSession,
    action: str,
    resource_type: str,
    actor_user_id: Optional[uuid.UUID] = None,
    resource_id: Optional[str] = None,
    request: Optional[Request] = None,
    metadata_payload: Optional[Dict[str, Any]] = None,
    result: str = "SUCCESS",
) -> None:
    audit_repo = AuditRepository(session)
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    request_id = request.headers.get("x-request-id") if request else None

    clean_metadata = None
    if metadata_payload:
        clean_metadata = {
            k: v for k, v in metadata_payload.items()
            if k.lower() not in ["password", "token", "access_token", "secret"]
        }

    await audit_repo.log(
        action=action,
        resource_type=resource_type,
        actor_user_id=actor_user_id,
        resource_id=resource_id,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_payload=clean_metadata,
        result=result,
    )