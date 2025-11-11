# -*- coding: utf-8 -*-
"""
与 descrypt.ts 等效的 Python 解密实现：
1) 使用 UTC 日期构造密钥: "benson66" + YYYYMMDD
2) AES-ECB + PKCS7 解密 Base64 密文
3) zlib 解压得到 UTF-8 文本
4) JSON 解析为 Python 对象
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional
import base64, json, zlib

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

def build_key(date: Optional[datetime] = None) -> bytes:
    if date is None:
        date = datetime.now(timezone.utc)
    else:
        # 严格按 TS 的 UTC 取年月日
        date = (date if date.tzinfo else date.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)
    key_str = "benson66" + f"{date.year:04d}{date.month:02d}{date.day:02d}"
    return key_str.encode("utf-8")  # 16 字节，AES-128

def _inflate_auto(data: bytes) -> bytes:
    """
    依次尝试 zlib → raw deflate → gzip 三种解压封装。
    TS 的 pako.inflate 对 zlib OK；如果后端换了封装，这里能自动兜底。
    """
    # zlib 包装（等价 pako.inflate 默认）
    try:
        return zlib.decompress(data)
    except zlib.error:
        pass
    # 原始 deflate（无 zlib/gzip 头）
    try:
        return zlib.decompress(data, wbits=-zlib.MAX_WBITS)
    except zlib.error:
        pass
    # gzip 包装
    try:
        return zlib.decompress(data, wbits=zlib.MAX_WBITS | 16)
    except zlib.error as e:
        raise ValueError(f"zlib 解压失败（尝试 zlib/raw/gzip 均不成功）: {e}") from e

def aes_decrypt_koma(base64_ciphertext: str, date: Optional[datetime] = None) -> Any:
    key = build_key(date)

    # Base64
    try:
        ct = base64.b64decode(base64_ciphertext)
    except Exception as e:
        raise ValueError(f"Base64 解码失败: {e}") from e

    # AES-ECB + PKCS7
    try:
        cipher = AES.new(key, AES.MODE_ECB)
        padded_plain = cipher.decrypt(ct)
        plain = unpad(padded_plain, block_size=16, style="pkcs7")
    except Exception as e:
        raise ValueError(f"AES 解密/去填充失败: {e}") from e

    # 解压（自动探测封装）
    decompressed = _inflate_auto(plain)

    # UTF-8 → JSON
    try:
        text = decompressed.decode("utf-8")
        return json.loads(text)
    except Exception as e:
        raise ValueError(f"解析 JSON 失败: {e}") from e



if __name__ == "__main__":
    # 测试示例
    test_key = build_key()
    print(f"测试密钥: {test_key}")

    # 实际使用时需要真实的加密数据
    en = "UUwkntRP+Yv1pisW+WXa0qWDvaKW915ue+tdTPemmE13dai/MdL5mc/gkHimjEj6WaC72q7O4KXN1LyMT0srIG+T+fs8damVabKZLd02eIc="
    result = aes_decrypt_koma(en)
    print(result)
