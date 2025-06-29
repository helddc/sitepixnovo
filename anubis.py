# anubis.py
import requests
from config import ANUBIS_API_URL, ANUBIS_PUBLIC_KEY, ANUBIS_PRIVATE_KEY

def create_pix_charge(value: float, txid: str):
    url = f"{ANUBIS_API_URL}/pix/charge"
    # ADICIONADO VALIDADE DE 8 HORAS (28800 segundos)
    payload = {"value": value, "txid": txid, "expires_in": 28800}
    headers = {
        "Authorization": f"Bearer {ANUBIS_PUBLIC_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data.get("success"):
            return data.get("pix"), data.get("qr_code_base64")
        return None, None
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar cobrança Anubis: {e}")
        if e.response:
            print(f"Resposta da API: {e.response.text}")
        return None, None

def send_pix_payout(value: float, pix_key: str, pix_key_type: str):
    url = f"{ANUBIS_API_URL}/pix/send"
    payload = {"value": value, "pix_key": pix_key, "pix_key_type": pix_key_type}
    headers = {
        "Authorization": f"Bearer {ANUBIS_PRIVATE_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("success", False), data
    except requests.exceptions.RequestException as e:
        print(f"Erro ao realizar saque Anubis: {e}")
        if e.response:
            print(f"Resposta da API: {e.response.text}")
        error_response = e.response.json() if e.response else {"error": str(e)}
        return False, error_response
