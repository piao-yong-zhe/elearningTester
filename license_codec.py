import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta

DATE_PATTERN = re.compile(r"^\d{8}$")
SHARED_RULE_KEY = "EXAM-LICENSE-KEY"


def derive_key(password: str, salt: bytes, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000, dklen=length)


def encode_payload(payload: dict, password: str) -> str:
    data = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    salt = os.urandom(16)
    key = derive_key(password, salt, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, key))
    token = salt + ciphertext
    return base64.urlsafe_b64encode(token).decode("utf-8").rstrip("=")


def decode_payload(token: str, password: str) -> dict:
    try:
        padding = "=" * ((4 - len(token) % 4) % 4)
        token_bytes = base64.urlsafe_b64decode(token + padding)
        if len(token_bytes) <= 16:
            raise ValueError("无效的许可证数据")
        salt = token_bytes[:16]
        ciphertext = token_bytes[16:]
        key = derive_key(password, salt, len(ciphertext))
        plaintext = bytes(a ^ b for a, b in zip(ciphertext, key))
        return json.loads(plaintext.decode("utf-8"))
    except (base64.binascii.Error, ValueError, json.JSONDecodeError) as exc:
        raise ValueError("无效的码，无法解码。请检查密码和输入的编码文本。") from exc


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
    digest = hashlib.sha256(f"{SHARED_RULE_KEY}:{date_str}".encode("utf-8")).hexdigest()[:12]
    return digest.upper()


def create_license(date_str: str, password: str) -> str:
    if not validate_date(date_str):
        raise ValueError("日期格式必须为 YYYYMMDD")

    rule = build_rule_value(date_str)
    payload = {
        "date": date_str,
        "rule": rule,
        "created": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    return encode_payload(payload, password)


def verify_license(token: str, password: str, allow_days: int = None) -> dict:
    payload = decode_payload(token, password)

    if "date" not in payload or "rule" not in payload:
        raise ValueError("许可证内容缺少必须字段")

    if not validate_date(payload["date"]):
        raise ValueError("许可证中的日期格式无效")

    expected_rule = build_rule_value(payload["date"])
    if payload["rule"] != expected_rule:
        raise ValueError("许可证中的规则数据不符合当前密钥规则")

    if allow_days is not None:
        issued = datetime.strptime(payload["date"], "%Y%m%d")
        expire = issued + timedelta(days=allow_days)
        if datetime.utcnow() > expire:
            raise ValueError("许可证已过期")

    return payload


if __name__ == "__main__":
    secret = "admin-secret"
    token = create_license("20260707", secret)
    print("生成许可证：", token)
    print("解码后内容：", verify_license(token, secret, allow_days=365))
