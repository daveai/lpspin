from web3 import Web3
import math, json, os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Connect to w3 instance
w3 = Web3(Web3.HTTPProvider("https://rpc.gnosischain.com"))

# Load the private key
acc = w3.eth.account.from_key(os.environ["PRIVATE_KEY"])

# Load the contract ABI and contract
abi = open("abi/unipm.json", "r").read()
uni = w3.eth.contract(address="0xAE8fbE656a77519a7490054274910129c9244FA3", abi=abi)

erc20_abi = open("abi/erc20.json", "r").read()


def fetch_price(address):
    req = requests.get(
        "https://api.coingecko.com/api/v3/simple/token_price/xdai?contract_addresses={}&vs_currencies=usd".format(
            address
        )
    )
    # Get the price from the response
    price = req.json()[address.lower()]["usd"]
    return price


def sqrtPriceX96(price_ratio):
    xn = 2**96
    p = math.sqrt(price_ratio) * 2**96
    return p


def approve(token, amount):
    erc20 = w3.eth.contract(address=token, abi=erc20_abi)
    tx = erc20.functions.approve(
        "0xAE8fbE656a77519a7490054274910129c9244FA3", amount
    ).build_transaction(
        {
            "from": acc.address,
            "nonce": w3.eth.get_transaction_count(acc.address),
            "gas": 100000,
            "gasPrice": w3.to_wei("5", "gwei"),
        }
    )
    signed_tx = w3.eth.account.sign_transaction(
        tx, private_key=os.environ["PRIVATE_KEY"]
    )
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(w3.eth.wait_for_transaction_receipt(tx_hash))


if __name__ == "__main__":
    # Load the payload
    payload = open("PAYLOAD.json", "r").read()
    p = json.loads(payload)
    # Get the lowest hex string token address
    token0 = p["tokens"][0]
    token1 = p["tokens"][1]
    assert token0["address"] < token1["address"], "Token addresses are not in order"

    # Fetch price
    price0 = fetch_price(token0["address"])
    price1 = fetch_price(token1["address"])

    # Calculate the price ratio
    price_ratio = price0 / price1
    # Calculate the sqrtPriceX96
    sqrt_price = int(sqrtPriceX96(price_ratio))

    # Amounts to LP
    amount0 = int(price0 / token0["amountUSD"] * 10**18)
    amount1 = int(price1 / token1["amountUSD"] * 10**18)

    # Approve the tokens
    approve(token0["address"], 115792089237316195423570985008687907853269984665640564039457584007913129639935)
    approve(token1["address"], 115792089237316195423570985008687907853269984665640564039457584007913129639935)

    create = uni.functions.createAndInitializePoolIfNecessary(
        token0['address'], token1['address'], p["fee"], sqrt_price
    ).build_transaction(
        {
            "from": acc.address,
            "nonce": w3.eth.get_transaction_count(acc.address),
            "gas": 7000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        }
    )
    signed_tx = w3.eth.account.sign_transaction(
        create, private_key=os.environ["PRIVATE_KEY"]
    )
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(w3.eth.wait_for_transaction_receipt(tx_hash))

    t_10 = datetime.now() + timedelta(minutes=10)
    timestamp = int(t_10.timestamp())

    mint = uni.functions.mint(
        (token0['address'],
        token1['address'],
        p["fee"],
        p["tickLower"],
        p["tickUpper"],
        amount0,
        amount1,
        int(amount0 * 0.98),
        int(amount1 * 0.98),
        acc.address,
        timestamp)
    ).build_transaction(
        {
            "from": acc.address,
            "nonce": w3.eth.get_transaction_count(acc.address),
            "gas": 2000000,
            "gasPrice": w3.to_wei("5", "gwei"),
        }
    )
    signed_tx = w3.eth.account.sign_transaction(
        mint, private_key=os.environ["PRIVATE_KEY"]
    )
    
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(w3.eth.wait_for_transaction_receipt(tx_hash))
