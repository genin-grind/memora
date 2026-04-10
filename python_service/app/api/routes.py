from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.auth_service import validate_org_user
from app.services.explorer_service import get_explorer_workspace
from app.services.org_service import get_org_summary
from app.services.org_service import get_source_status
from app.services.query_service import analyze_query
from app.services.sync_service import get_sync_status
from app.services.sync_service import run_sync_now


router = APIRouter()


class LoginRequest(BaseModel):
    email: str


class QueryRequest(BaseModel):
    question: str


@router.get("/health")
def health():
    return {"ok": True, "service": "memora-python-service"}


@router.get("/org/summary")
def org_summary():
    return get_org_summary()


@router.get("/org/sources/status")
def org_sources_status():
    return get_source_status()


@router.get("/explorer/workspace")
def explorer_workspace():
    return get_explorer_workspace()


@router.post("/auth/login")
def login(payload: LoginRequest):
    allowed, message, user = validate_org_user(payload.email)
    if not allowed:
        raise HTTPException(status_code=403, detail=message)

    return {
        "ok": True,
        "message": message,
        "user": user,
    }


@router.get("/auth/me")
def me():
    return {
        "authenticated": False,
        "user": None,
    }


@router.post("/query")
def query(payload: QueryRequest):
    try:
        return analyze_query(payload.question)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.post("/sync/run")
def sync_run():
    try:
        return run_sync_now()
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@router.get("/sync/status")
def sync_status():
    return get_sync_status()
