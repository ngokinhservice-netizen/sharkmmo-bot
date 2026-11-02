import urllib.parse
from backend.app.core.config import settings


def generate_transfer_content(user_id: int, tx_id: int) -> str:
    """
    Format standard memo content without special characters:
    Example: SHARK NAP 1234 5678
    """
    return f"SHARK NAP {user_id} {tx_id}"


def get_vietqr_url(
    amount: float,
    transfer_content: str,
    bank_code: str = None,
    account_no: str = None,
    account_name: str = None,
    template: str = None
) -> str:
    """
    Generate official VietQR image link:
    https://img.vietqr.io/image/<BANK_CODE>-<ACCOUNT_NO>-<TEMPLATE>.png?amount=<AMOUNT>&addInfo=<CONTENT>&accountName=<NAME>
    """
    b_code = bank_code or settings.BANK_CODE
    acc_no = account_no or settings.BANK_ACCOUNT_NO
    tmpl = template or settings.VIETQR_TEMPLATE
    acc_name = account_name or settings.BANK_ACCOUNT_NAME

    encoded_content = urllib.parse.quote(transfer_content)
    encoded_name = urllib.parse.quote(acc_name)
    int_amount = int(amount)

    url = (
        f"https://img.vietqr.io/image/{b_code}-{acc_no}-{tmpl}.png"
        f"?amount={int_amount}&addInfo={encoded_content}&accountName={encoded_name}"
    )
    return url
