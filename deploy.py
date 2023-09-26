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
    price = req.json()['result']["usd"]
    return price


def sqrtPriceX96(price_ratio):
    xn = 2**96
    p = math.sqrt(price_ratio) * 2**96
    return p


def approve(token, amount):
    erc20 = w3.eth.contract(address=token, abi=erc20_abi)
    tx = erc20.functions.approve(
        "0xAE8fbE656a77519a7490054274910129c9244FA3", amount
    ).buildTransaction(
        {
            "from": acc.address,
            "nonce": w3.eth.getTransactionCount(w3.eth.accounts[0]),
            "gas": 100000,
            "gasPrice": w3.toWei("5", "gwei"),
        }
    )
    signed_tx = w3.eth.account.sign_transaction(
        tx, private_key=os.environ["PRIVATE_KEY"]
    )
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(w3.eth.waitForTransactionReceipt(tx_hash))


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
    sqrt_price = sqrtPriceX96(price_ratio)
    
    # Amounts to LP
    amount0 = price0 / token0["amountUSD"]
    amount1 = price1 / token1["amountUSD"]
    
    # Approve the tokens
    approve(token0["address"], amount0)
    approve(token1["address"], amount1)
    
    uni.functions.createAndInitializePoolIfNecessary(token0, token1, p["fee"], sqrt_price).buildTransaction(
        {
            "from": acc.address,
            "nonce": w3.eth.getTransactionCount(w3.eth.accounts[0]),
            "gas": 7000000,
            "gasPrice": w3.toWei("5", "gwei"),
        }
    )
    signed_tx = w3.eth.account.sign_transaction(
        tx, private_key=os.environ["PRIVATE_KEY"]
    )
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(w3.eth.waitForTransactionReceipt(tx_hash))
    
    t_10 = datetime.now() + timedelta(minutes=10)
    timestamp = int(t_10.timestamp())

    uni.functions.mint(token0, token1, p["fee"], p["tickLower"], p["tickUpper"] amount0, amount1, amount0*0.98, amount1*0.98, acc.address, timestamp).buildTransaction(
        {
            "from": acc.address,
            "nonce": w3.eth.getTransactionCount(w3.eth.accounts[0]),
            "gas": 2000000,
            "gasPrice": w3.toWei("5", "gwei"),
        }
    )
    signed_tx = w3.eth.account.sign_transaction(
        tx, private_key=os.environ["PRIVATE_KEY"]
    )
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(w3.eth.waitForTransactionReceipt(tx_hash))
    