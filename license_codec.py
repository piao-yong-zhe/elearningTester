import base64
import hashlib
import json
import os
import re
from datetime import datetime

DATE_PATTERN = re.compile(r"^\d{8}$")
SHARED_RULE_KEY = "EXAM-LICENSE-KEY"
SHARED_SECRET = "EXAM-LICENSE-SECRET"
RULE_TEXT = "EXAM-VALID"


def derive_key(password: str, salt: bytes, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, dklen=length)


def _get_secret(password: str | None) -> str:
    return password if password else SHARED_SECRET


def encode_payload(payload: dict, password: str | None = None) -> str:
    password = _get_secret(password)
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _encode_bytes(data, password)


def decode_payload(token: str, password: str | None = None) -> dict:
    password = _get_secret(password)
    try:
        plaintext = _decode_bytes(token, password)
        return json.loads(plaintext.decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ValueError("无效的码，无法解码。请检查密码和输入的编码文本。") from exc


def _encode_bytes(data: bytes, password: str) -> str:
    salt = os.urandom(16)
    key = derive_key(password, salt, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, key))
    token = salt + ciphertext
    return base64.urlsafe_b64encode(token).decode("utf-8").rstrip("=")


def _decode_bytes(token: str, password: str) -> bytes:
    padding = "=" * ((4 - len(token) % 4) % 4)
    token_bytes = base64.urlsafe_b64decode(token + padding)
    if len(token_bytes) <= 16:
        raise ValueError("无效的许可证数据")
    salt = token_bytes[:16]
    ciphertext = token_bytes[16:]
    key = derive_key(password, salt, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, key))


def encode_text(value: str, password: str | None = None) -> str:
    password = _get_secret(password)
    return _encode_bytes(value.encode("utf-8"), password)


def decode_text(token: str, password: str | None = None) -> str:
    password = _get_secret(password)
    return _decode_bytes(token, password).decode("utf-8")


def validate_date(date_str: str) -> bool:
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, "%Y%m%d")
        return True
    except ValueError:
        return False


def build_rule_value(date_str: str) -> str:
    if not validate_date(date_str):
        raise ValueError("日期格式必须为 YYYYMMDD")
    return RULE_TEXT


def create_license(date_str: str) -> str:
    if not validate_date(date_str):
        raise ValueError("日期格式必须为 YYYYMMDD")
    plain_text = f"{date_str}-{build_rule_value(date_str)}"
    return encode_text(plain_text)


def verify_license(code: str) -> dict:
    if not isinstance(code, str) or not code.strip():
        raise ValueError("请输入验证码")

    try:
        plain_text = decode_text(code)
    except Exception as exc:
        raise ValueError("验证码无法解码") from exc

    value = plain_text.strip().upper()
    if not re.fullmatch(r"^\d{8}-[A-Z0-9-]+$", value):
        raise ValueError("验证码格式无效")

    date_str = value.split("-", 1)[0]
    if not validate_date(date_str):
        raise ValueError("验证码中的日期格式无效")

    today_str = datetime.utcnow().strftime("%Y%m%d")
    if date_str != today_str:
        raise ValueError("验证码日期不是今天")

    expected_rule = build_rule_value(date_str)
    if value != f"{date_str}-{expected_rule}":
        raise ValueError("验证码规则不匹配")

    return {"date": date_str, "rule": expected_rule}


def create_machine_binding(machine_id: str, code: str) -> str:
    payload = {
        "machine_id": machine_id,
        "code": code,
        "date": code.split("-", 1)[0] if isinstance(code, str) else "",
    }
    return encode_payload(payload)


def verify_machine_binding(token: str, expected_machine_id: str) -> dict:
    payload = decode_payload(token)
    if payload.get("machine_id") != expected_machine_id:
        raise ValueError("机器绑定不匹配")
    if not payload.get("code"):
        raise ValueError("验证码绑定内容缺失")

    try:
        verify_license(payload.get("code"))
    except Exception as exc:
        raise ValueError("绑定的验证码无效") from exc

    return payload


if __name__ == "__main__":
    token = create_license(datetime.utcnow().strftime("%Y%m%d"))
    print("生成验证码：", token)
    print("验证结果：", verify_license(token))
