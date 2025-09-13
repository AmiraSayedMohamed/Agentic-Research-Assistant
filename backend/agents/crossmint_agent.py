import os
import requests

CROSSMINT_API_KEY = os.getenv("CROSSMINT_API_KEY")
CROSSMINT_API_URL = "https://staging.crossmint.com/api/2022-06-09/collections/default/nfts"

def mint_nft(metadata: dict):
    headers = {
        "x-api-key": CROSSMINT_API_KEY,
        "Content-Type": "application/json"
    }
    response = requests.post(CROSSMINT_API_URL, json=metadata, headers=headers)
    response.raise_for_status()
    return response.json()
