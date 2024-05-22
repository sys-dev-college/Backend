import re
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user_sessions.models import Session
from app.modules.users.models import UserFingerprint

_BROWSER_UA_PATTERN = {
    "Microsoft Edge": r"Edg/",
    "Opera": r"OPR/",
    "Firefox": r"Firefox/",
    "Chrome": r"Chrome/",
    "Safari": r"Safari/",
}


async def get_addition_session_details(
    session: AsyncSession,
    ws_session: Optional[Session] = None,
) -> Dict[str, Any]:
    addons = {
        "ip": None,
        "browser_version": None,
    }
    if not ws_session:
        return addons

    addons["ip"] = ws_session.ip
    browser_data = await session.scalar(
        select(UserFingerprint.fingerprint_data).where(
            UserFingerprint.id == ws_session.fingerprint_id
        )
    )
    browser_ua = browser_data["userAgent"]
    for browser, pattern in _BROWSER_UA_PATTERN.items():
        version = re.findall(pattern + r"(\S+)\s", browser_ua)
        if not version:
            continue
        addons["browser_version"] = f"{browser} {version[0]}"
        break
    return addons
