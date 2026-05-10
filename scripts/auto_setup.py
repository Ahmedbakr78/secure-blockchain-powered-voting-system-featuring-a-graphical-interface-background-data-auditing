import json
import os
from web3 import Web3
import solcx

# Ensure solc is installed
try:
    solcx.install_solc('0.8.19')
    solcx.set_solc_version('0.8.19')
except Exception as e:
    print(f"Failed to install/set solc 0.8.19: {e}")

# Connect to local Ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

if not w3.is_connected():
    print("Failed to connect to local blockchain. Is Ganache running?")
    exit(1)

admin_account = w3.eth.accounts[0]
w3.eth.default_account = admin_account
print(f"Connected. Admin account: {admin_account}")

def compile_contract(file_path, contract_name):
    print(f"Compiling {contract_name}...")
    with open(file_path, "r") as f:
        source = f.read()
    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version="0.8.19"
    )
    contract_id = f"<stdin>:{contract_name}"
    interface = compiled[contract_id]
    return interface['abi'], interface['bin']

def deploy_contract(abi, bytecode, *args):
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = Contract.constructor(*args).transact({'from': admin_account})
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Deployed to: {tx_receipt.contractAddress}")
    return tx_receipt.contractAddress

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    coin_path = os.path.join(base_dir, "contracts", "VotingCoin.sol")
    app_path = os.path.join(base_dir, "contracts", "SafeVotingApp.sol")

    # Compile
    coin_abi, coin_bin = compile_contract(coin_path, "VotingCoin")
    app_abi, app_bin = compile_contract(app_path, "SafeVotingApp")

    # Deploy
    print("Deploying VotingCoin...")
    coin_address = deploy_contract(coin_abi, coin_bin)
    
    print("Deploying SafeVotingApp...")
    app_address = deploy_contract(app_abi, app_bin, coin_address)

    # Authorize App to burn coins
    print("Authorizing SafeVotingApp to consume coins...")
    coin_contract = w3.eth.contract(address=coin_address, abi=coin_abi)
    tx_hash = coin_contract.functions.setAuthorizedApp(app_address).transact({'from': admin_account})
    w3.eth.wait_for_transaction_receipt(tx_hash)

    # Initialize fake candidates
    print("Adding fake candidates...")
    app_contract = w3.eth.contract(address=app_address, abi=app_abi)
    
    ids = [0, 0, 0, 0, 0]
    names = ["ali ezz alyan", "ahmed abobaker", "ahmed sabry", "ahmed abdalnaser", "ahmed mohamed"]
    
    tx_hash = app_contract.functions.batchUpdateCandidates(ids, names).transact({'from': admin_account})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Fake candidates added.")

    # Initial Minting
    print("Seeding users with initial VotingCoins (5 VTC each)...")
    coin_contract = w3.eth.contract(address=coin_address, abi=coin_abi)
    
    # Seeding for users (Admin already has 100 VTC from constructor)
    for i in range(1, 10):
        acc = w3.eth.accounts[i]
        amount = 5 * (10**18)
        tx_hash = coin_contract.functions.mint(acc, amount).transact({'from': admin_account})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"Minted 5 VTC to {acc[:10]}...")

    # Save addresses and ABI
    out_data = {
        "VotingCoin": {
            "address": coin_address,
            "abi": coin_abi
        },
        "SafeVotingApp": {
            "address": app_address,
            "abi": app_abi
        }
    }
    out_path = os.path.join(base_dir, "contract_data.json")
    with open(out_path, "w") as f:
        json.dump(out_data, f, indent=4)
    print(f"Deployment data saved to {out_path}")

if __name__ == "__main__":
    main()
