import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# ---------- config ----------
SECRET = "support-portal-secret-do-not-use-in-prod"
ALGO = "HS256"
TKN_EXP = 60  # minutes


# ---------- auth ----------
def _h(val: str) -> str:
    return hashlib.sha256(val.encode()).hexdigest()


# ---------- data ----------
users_db: dict = {
    "u-001": {
        "id": "u-001",
        "username": "admin",
        "pw": _h("admin123"),
        "role": "admin",
        "email": "admin@example.com",
        "created_at": "2023-01-10T09:00:00",
    },
    "u-002": {
        "id": "u-002",
        "username": "alice",
        "pw": _h("password"),
        "role": "user",
        "email": "alice@example.com",
        "created_at": "2023-06-15T14:30:00",
    },
    "u-003": {
        "id": "u-003",
        "username": "bob",
        "pw": _h("password"),
        "role": "user",
        "email": "bob@example.com",
        "created_at": "2024-01-20T08:00:00",
    },
}

_uname_idx: dict = {v["username"]: k for k, v in users_db.items()}

support_requests_db: dict = {}


# ---------- utils (part 1) ----------
def gen_id() -> str:
    return str(uuid.uuid4())


def ts_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fmt_dt(iso: str) -> str:
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%Y-%m-%d %H:%M UTC")


# ---------- middleware ----------
class RqMw(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        rid = gen_id()
        request.state.rid = rid
        resp = await call_next(request)
        resp.headers["X-Request-ID"] = rid
        return resp


app = FastAPI(title="Support Portal API", version="1.0.0")
app.add_middleware(RqMw)


# ---------- utils (part 2) ----------
def mk_resp(data: object, msg: str = "ok") -> dict:
    return {"status": "success", "message": msg, "data": data}


def det_prio(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["urgent", "critical", "outage", "down", "asap", "emergency"]):
        return "high"
    if any(w in t for w in ["issue", "problem", "error", "broken", "fail", "not working"]):
        return "medium"
    return "low"


def cat_req(title: str, desc: str) -> str:
    t = (title + " " + desc).lower()
    if any(w in t for w in ["payment", "invoice", "billing", "charge", "refund", "subscription"]):
        return "billing"
    if any(w in t for w in ["password", "login", "access", "permission", "account", "locked"]):
        return "account"
    if any(w in t for w in ["bug", "error", "crash", "broken", "fail", "not working"]):
        return "technical"
    return "general"


def calc_dl(priority: str) -> str:
    hrs = {"high": 4, "medium": 24, "low": 72}
    deadline = datetime.now(timezone.utc) + timedelta(hours=hrs.get(priority, 24))
    return deadline.isoformat()


# ---------- token helpers ----------
def mk_tok(data: dict) -> str:
    d = data.copy()
    d["exp"] = datetime.now(timezone.utc) + timedelta(minutes=TKN_EXP)
    return jwt.encode(d, SECRET, algorithm=ALGO)


def v_tok(tok: str) -> dict:
    try:
        return jwt.decode(tok, SECRET, algorithms=[ALGO])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "token expired")
    except Exception:
        raise HTTPException(401, "invalid token")


def get_usr(creds: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> dict:
    payload = v_tok(creds.credentials)
    u = users_db.get(payload.get("uid"))
    if not u:
        raise HTTPException(401, "user not found")
    return u


# ---------- models ----------
class TknReq(BaseModel):
    username: str
    password: str


class SupportReqIn(BaseModel):
    title: str
    description: str
    priority: Optional[str] = None


# ---------- routes: auth ----------
@app.post("/auth/token")
def login(body: TknReq) -> dict:
    uid = _uname_idx.get(body.username)
    u = users_db.get(uid) if uid else None
    if not u or u["pw"] != _h(body.password):
        raise HTTPException(401, "invalid credentials")
    tok = mk_tok({"sub": body.username, "uid": uid, "role": u["role"]})
    return {"access_token": tok, "token_type": "bearer"}


# ---------- routes: users ----------
@app.get("/users")
def list_users(p: dict = Depends(get_usr)) -> list:
    if p["role"] != "admin":
        raise HTTPException(403, "admin only")
    out = []
    for uid, u in users_db.items():
        reqs = support_requests_db.get(uid, [])
        open_count = sum(1 for r in reqs if r["status"] != "closed")
        out.append(
            {
                "id": uid,
                "username": u["username"],
                "email": u["email"],
                "role": u["role"],
                "open_requests": open_count,
                "created_at": u["created_at"],
            }
        )
    return out


@app.get("/users/me")
def get_me(p: dict = Depends(get_usr)) -> dict:
    reqs = support_requests_db.get(p["id"], [])
    open_count = sum(1 for r in reqs if r["status"] != "closed")
    created = datetime.fromisoformat(p["created_at"])
    age_days = (datetime.now(timezone.utc) - created.replace(tzinfo=timezone.utc)).days
    return {
        "id": p["id"],
        "username": p["username"],
        "email": p["email"],
        "role": p["role"],
        "account_age_days": age_days,
        "open_requests": open_count,
        "total_requests": len(reqs),
        "member_since": fmt_dt(p["created_at"]),
    }


@app.get("/users/{user_id}")
def get_user(user_id: str, p: dict = Depends(get_usr)) -> dict:
    if p["role"] != "admin" and p["id"] != user_id:
        raise HTTPException(403, "forbidden")
    u = users_db.get(user_id)
    if not u:
        raise HTTPException(404, "user not found")
    reqs = support_requests_db.get(user_id, [])
    open_count = sum(1 for r in reqs if r["status"] != "closed")
    created = datetime.fromisoformat(u["created_at"])
    age_days = (datetime.now(timezone.utc) - created.replace(tzinfo=timezone.utc)).days
    return {
        "id": user_id,
        "username": u["username"],
        "email": u["email"],
        "role": u["role"],
        "account_age_days": age_days,
        "open_requests": open_count,
        "total_requests": len(reqs),
        "member_since": fmt_dt(u["created_at"]),
    }


# ---------- routes: support requests ----------
@app.get("/users/{user_id}/support-requests")
def list_support_reqs(user_id: str, status: Optional[str] = None, p: dict = Depends(get_usr)) -> list:
    if p["role"] != "admin" and p["id"] != user_id:
        raise HTTPException(403, "forbidden")
    if not users_db.get(user_id):
        raise HTTPException(404, "user not found")
    reqs = support_requests_db.get(user_id, [])
    if status:
        reqs = [r for r in reqs if r["status"] == status]
    return reqs


@app.post("/users/{user_id}/support-requests", status_code=201)
def create_support_req(user_id: str, body: SupportReqIn, p: dict = Depends(get_usr)) -> dict:
    if p["role"] != "admin" and p["id"] != user_id:
        raise HTTPException(403, "forbidden")
    if not users_db.get(user_id):
        raise HTTPException(404, "user not found")

    if len(body.title.strip()) < 5:
        raise HTTPException(422, "title too short (min 5 chars)")

    if body.priority:
        if body.priority not in ("low", "medium", "high"):
            raise HTTPException(422, "priority must be low, medium or high")
        prio = body.priority
    else:
        prio = det_prio(body.description)

    category = cat_req(body.title, body.description)
    deadline = calc_dl(prio)

    req = {
        "id": gen_id(),
        "user_id": user_id,
        "title": body.title.strip(),
        "description": body.description.strip(),
        "priority": prio,
        "category": category,
        "status": "open",
        "deadline": deadline,
        "created_by": p["id"],
        "created_at": ts_now(),
        "updated_at": ts_now(),
    }

    support_requests_db.setdefault(user_id, []).append(req)
    return mk_resp(req, "support request created")
