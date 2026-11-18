import base64
import logging
import urllib.parse
from typing import Optional, Tuple
import httpx
from backend.app.core.config import settings

logger = logging.getLogger("sharkmmo.vietqr")

BANK_BIN_MAP = {
    "VPB": "970432",
    "VPBANK": "970432",
    "VBA": "970405",
    "AGRIBANK": "970405",
    "MB": "970422",
    "MBBANK": "970422",
    "VCB": "970436",
    "VIETCOMBANK": "970436",
    "TCB": "970407",
    "TECHCOMBANK": "970407",
    "ACB": "970416",
    "BIDV": "970418",
    "CTG": "970415",
    "VIETINBANK": "970415",
    "TPB": "970423",
    "TPBANK": "970423",
    "STB": "970403",
    "SACOMBANK": "970403",
    "VIB": "970441",
    "HDB": "970437",
    "MSB": "970426",
    "SHB": "970443",
    "LPB": "970449",
    "OCB": "970448",
    "SEAB": "970440",
    "CAKE": "546034",
    "TIMO": "963388"
}


def get_vietqr_url(
    amount: float,
    transfer_content: str,
    bank_code: str = None,
    account_no: str = None,
    account_name: str = None,
    template: str = None
) -> str:
    b_code = (bank_code or settings.BANK_CODE).upper()
    acc_no = account_no or settings.BANK_ACCOUNT_NO
    tmpl = template or settings.VIETQR_TEMPLATE
    acc_name = account_name or settings.BANK_ACCOUNT_NAME

    encoded_content = urllib.parse.quote(transfer_content)
    encoded_name = urllib.parse.quote(acc_name)
    int_amount = int(amount)

    return (
        f"https://img.vietqr.io/image/{b_code}-{acc_no}-{tmpl}.png"
        f"?amount={int_amount}&addInfo={encoded_content}&accountName={encoded_name}"
    )


async def get_vietqr_png_bytes(
    amount: float,
    transfer_content: str,
    bank_code: Optional[str] = None,
    account_no: Optional[str] = None,
    account_name: Optional[str] = None,
    template: Optional[str] = None
) -> Optional[bytes]:
    """
    Generate official base64 PNG directly from VietQR API v2.
    Returns raw bytes suitable for aiogram BufferedInputFile.
    """
    b_code = (bank_code or settings.BANK_CODE).upper()
    acc_no = account_no or settings.BANK_ACCOUNT_NO
    acc_name = account_name or settings.BANK_ACCOUNT_NAME
    tmpl = template or settings.VIETQR_TEMPLATE

    bin_code = BANK_BIN_MAP.get(b_code, "970432")

    payload = {
        "accountNo": acc_no,
        "accountName": acc_name,
        "acqId": bin_code,
        "amount": int(amount),
        "addInfo": transfer_content,
        "format": "text",
        "template": tmpl
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://api.vietqr.io/v2/generate", json=payload)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "00" and "data" in data:
                    qr_url = data["data"].get("qrDataURL", "")
                    if "base64," in qr_url:
                        b64_str = qr_url.split("base64,")[1]
                        return base64.b64decode(b64_str)
    except Exception as e:
        logger.error(f"Failed to fetch VietQR v2 API: {e}")

    # Fallback to qrserver.com with VietQR quicklink payload
    try:
        quick_url = get_vietqr_url(amount, transfer_content, b_code, acc_no, acc_name, tmpl)
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Generate a standard QR code containing the VietQR deeplink
            fallback_qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=450x450&data={urllib.parse.quote(quick_url)}"
            r = await client.get(fallback_qr_api)
            if r.status_code == 200:
                return r.content
    except Exception as e2:
        logger.error(f"Fallback QR generator failed: {e2}")

    return None
