import base64
import requests
from config import ANUBIS_PUBLIC_KEY, ANUBIS_PRIVATE_KEY

def create_pix_charge(value: float, txid: str):
    url = "https://api.anubispay.com.br/v1/transactions"

    # Gera autenticação Basic com chave pública e privada
    credentials = f"{ANUBIS_PUBLIC_KEY}:{ANUBIS_PRIVATE_KEY}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {base64_credentials}",
        "Content-Type": "application/json"
    }

    payload = {
        "amount": int(value * 100),         # valor em centavos
        "paymentMethod": "pix",
        "reference": txid,
        "expiresIn": 28800                  # validade: 8 horas (em segundos)
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Ajuste conforme a estrutura da resposta real
        pix_code = data.get("pixCode") or data.get("payload")
        qr_code_base64 = data.get("qrCodeBase64") or data.get("qr_code_base64")

        return pix_code, qr_code_base64
    except requests.exceptions.RequestException as e:
        print(f"Erro ao criar cobrança Anubis: {e}")
        if e.response:
            print(f"Resposta da API: {e.response.text}")
        return None, None
