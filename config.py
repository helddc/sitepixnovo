import os

# --- Credenciais da Anubis ---
# O código agora pega as chaves diretamente do painel "Environment Variables" do Render.
# Suas chaves ficam seguras lá, e não aqui no código.
ANUBIS_PUBLIC_KEY = os.getenv("ANUBIS_PUBLIC_KEY")
ANUBIS_PRIVATE_KEY = os.getenv("ANUBIS_PRIVATE_KEY")

# --- Regras de Negócio ---
FIXED_FEE = 2.50  # Taxa fixa de R$ 2,50
PERCENTAGE_COMMISSION = 0.15  # Comissão de 15%
MINIMUM_VALUE = 20.00  # Valor líquido mínimo que o usuário pode solicitar

# --- URL da API Anubis ---
ANUBIS_API_URL = "https://api.anubis.gg/api"
