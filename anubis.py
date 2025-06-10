import base64
import requests
from config import ANUBIS_PUBLIC_KEY, ANUBIS_PRIVATE_KEY, ANUBIS_WITHDRAW_KEY

def create_pix_charge(value: float, txid: str):
    url = "https://api.anubispay.com.br/v1/transactions"

    credentials = f"{ANUBIS_PUBLIC_KEY}:{ANUBIS_PRIVATE_KEY}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/json"
    }

    payload = {
        "amount": int(value * 100),
        "paymentMethod": "pix",
        "reference": txid,
        "expiresIn": 28800,
        "description": "Cobrança via SitePixPix"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        pix_code = data.get("pixCode") or data.get("payload")
        qr_code_base64 = data.get("qrCodeBase64") or data.get("qr_code_base64")

        return pix_code, qr_code_base64
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar cobrança Anubis: {e}")
        if e.response:
            print(f"Resposta da API: {e.response.text}")
        return None, None

def send_pix_payout(amount: float, pix_key: str, pix_key_type: str):
    url = "https://api.anubispay.com.br/v1/transfers"

    credentials = f"{ANUBIS_PUBLIC_KEY}:{ANUBIS_PRIVATE_KEY}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "accept": "application/json",
        "x-withdraw-key": ANUBIS_WITHDRAW_KEY,
        "authorization": f"Basic {base64_credentials}",
        "content-type": "application/json"
    }

    # Monta o payload incluindo a chave Pix e tipo
    payload = {
        "method": "fiat",
        "amount": int(amount * 100),  # em centavos
        "pixKey": pix_key,
        "pixKeyType": pix_key_type  # cpf, email, phone, randomkey (depende da API)
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"Saque realizado com sucesso: {data}")
        return True, "Saque realizado com sucesso"
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer saque Anubis: {e}")
        if e.response:
            print(f"Resposta da API: {e.response.text}")
        return False, str(e)
