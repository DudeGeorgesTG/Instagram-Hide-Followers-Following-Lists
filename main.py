import base64
import getpass
import json
import logging
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("instagram.hide_lists")


class HideListsError(RuntimeError):
    pass


class ValidationError(HideListsError):
    pass


class InstagramError(HideListsError):
    pass


@dataclass(frozen=True, slots=True)
class Session:
    user_id: str
    sessionid: str

    @property
    def cookie_header(self) -> str:
        return f"sessionid={self.sessionid}; ds_user_id={self.user_id}"

    @classmethod
    def parse(cls, raw: str) -> "Session":
        if not raw:
            raise ValidationError("Session id must not be empty.")
        if any(ord(c) <= 32 or ord(c) >= 127 or c in ';,"\\' for c in raw):
            raise ValidationError(
                "Enter only the sessionid cookie value, without 'sessionid='."
            )
        match = re.fullmatch(r"([1-9][0-9]*)(?::|%3[aA]).+", raw)
        if not match:
            raise ValidationError(
                "Invalid sessionid format: expected a numeric user ID "
                "followed by ':' or '%3A'."
            )
        return cls(user_id=match.group(1), sessionid=raw)

    def build_authorization(self) -> str:
        payload = {
            "ds_user_id": self.user_id,
            "sessionid": self.sessionid,
            "should_use_header_over_cookies": True,
        }
        encoded = base64.b64encode(
            json.dumps(payload, separators=(",", ":")).encode()
        ).decode("ascii")
        return f"Bearer IGT:2:{encoded}"


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        raise HideListsError("Redirect refused; credentials were not forwarded.")


def _build_request(session: Session) -> urllib.request.Request:
    authorization = session.build_authorization()
    body = {
        "method": "post",
        "format": "json",
        "server_timestamps": "true",
        "locale": "user",
        "fb_api_req_friendly_name": "IGSettingsBooleanMutation",
        "client_doc_id": "2669261950526978627082629536",
        "variables": json.dumps(
            {
                "setting_id": "hide_followers_following_list",
                "allow_error_codes": True,
                "callsite": "account_privacy",
                "value": True,
            }
        ),
    }
    headers = {
        "Authorization": authorization,
        "Cookie": session.cookie_header,
        "IG-INTENDED-USER-ID": session.user_id,
        "X-IG-App-ID": "124024574287414",
        "X-Auth-Type": "instagram",
        "User-Agent": "Instagram 453.0.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "identity",
        "X-GraphQL-Client-Library": "pando",
        "X-FB-Friendly-Name": "IGSettingsBooleanMutation",
    }
    return urllib.request.Request(
        "https://i.instagram.com/graphql/query",
        data=urllib.parse.urlencode(body).encode(),
        headers=headers,
        method="POST",
    )


def _redact(text: str, session: Session, authorization: str) -> str:
    secrets = {
        authorization,
        session.sessionid,
        urllib.parse.unquote(session.sessionid),
        urllib.parse.quote(session.sessionid, safe=""),
    }
    for secret in sorted(secrets, key=len, reverse=True):
        if secret:
            text = text.replace(secret, "<REDACTED>")
    return text


def _extract_error_details(raw: bytes) -> dict[str, Any]:
    if len(raw) > 16384:
        return {}
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError):
        return {}
    if not isinstance(body, dict):
        return {}
    return {
        key: body[key]
        for key in ("message", "error_type", "status", "code")
        if isinstance(body.get(key), (str, int, bool))
    }


def _http_error(
    error: urllib.error.HTTPError, request: urllib.request.Request
) -> InstagramError:
    with error:
        raw = error.read(16385)
    details = _extract_error_details(raw)
    text = json.dumps(details) if details else "No selected JSON error details."

    authorization = request.get_header("Authorization") or ""
    session_cookie = request.get_header("Cookie") or ""
    sessionid = ""
    for part in session_cookie.split(";"):
        key, _, value = part.strip().partition("=")
        if key == "sessionid":
            sessionid = value
            break
    text = _redact(text, Session(user_id="", sessionid=sessionid), authorization)

    return InstagramError(f"HTTP {error.code}: {text[:1500]}.")


def _execute(request: urllib.request.Request) -> dict[str, Any]:
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirectHandler()
    )
    try:
        with opener.open(request, timeout=15) as response:
            raw = response.read(1024 * 1024 + 1)
            if len(raw) > 1024 * 1024:
                raise InstagramError("Response too large.")
            return json.loads(raw)
    except urllib.error.HTTPError as error:
        raise _http_error(error, request) from None
    except urllib.error.URLError as error:
        raise HideListsError(f"Network/TLS failure: {error.reason}.") from None
    except TimeoutError:
        raise HideListsError("Request timed out.") from None
    except json.JSONDecodeError:
        raise InstagramError("Invalid JSON response.") from None


def _is_success(body: Any) -> bool:
    if not isinstance(body, dict):
        return False
    if body.get("errors") or body.get("error") or body.get("status") == "fail":
        return False
    data = body.get("data")
    if not isinstance(data, dict):
        return False
    root = "xdt_api__v1__settings__set_bool"
    matches = [
        value
        for key, value in data.items()
        if key == root or key.startswith(root + "(")
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        return False
    result = matches[0]
    if result.get("value") is not True:
        return False
    return not any(
        result.get(key)
        for key in (
            "error_name_value",
            "errorNameValue",
            "fallback_message",
            "fallbackMessage",
        )
    )


def hide_lists(sessionid: str) -> dict[str, Any]:
    session = Session.parse(sessionid)
    request = _build_request(session)
    body = _execute(request)
    if not _is_success(body):
        raise InstagramError(
            "Instagram did not confirm enabling the setting. No retry performed."
        )
    logger.info("Instagram confirmed the setting (value=true).")
    return body


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    try:
        sessionid = getpass.getpass("Your Instagram sessionid value: ").strip()
        hide_lists(sessionid)
    except ValidationError as error:
        logger.error("%s", error)
        return 2
    except InstagramError as error:
        logger.error("%s", error)
        return 1
    except HideListsError as error:
        logger.error("%s", error)
        return 1
    except KeyboardInterrupt:
        logger.error(
            "Interrupted. The update may have been applied; check before retrying."
        )
        return 130
    print("Enabled: Instagram returned value=true.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
