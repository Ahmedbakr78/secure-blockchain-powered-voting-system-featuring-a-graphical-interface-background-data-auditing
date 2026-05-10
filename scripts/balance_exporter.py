import json
import os
import csv
from web3 import Web3

def get_contracts(w3):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "contract_data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    
    app_contract = w3.eth.contract(address=data["SafeVotingApp"]["address"], abi=data["SafeVotingApp"]["abi"])
    coin_contract = w3.eth.contract(address=data["VotingCoin"]["address"], abi=data["VotingCoin"]["abi"])
    
    return app_contract, coin_contract

def main():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("Not connected to Ganache.")
        return
        
    app_contract, coin_contract = get_contracts(w3)
    
    print("Scanning blocks to find accounts...")
    latest_block = w3.eth.get_block_number()
    accounts = set()
    
    for i in range(latest_block + 1):
        block = w3.eth.get_block(i, full_transactions=True)
        for tx in block.transactions:
            accounts.add(tx['from'])
            if tx['to']:
                accounts.add(tx['to'])
                
    for acc in w3.eth.accounts:
        accounts.add(acc)
        
    accounts.discard(None)
    accounts.discard(app_contract.address)
    accounts.discard(coin_contract.address)
    
    decimals = coin_contract.functions.decimals().call()
    
    out_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "balances_snapshot.csv")
    
    print("Exporting balances to CSV...")
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Address", "Voting Coin Balance", "ETH Balance"])
        
        for acc in accounts:
            eth_bal = w3.from_wei(w3.eth.get_balance(acc), 'ether')
            coin_bal = coin_contract.functions.balanceOf(acc).call() / (10**decimals)
            writer.writerow([acc, coin_bal, eth_bal])
            
    print(f"Snapshot saved to {out_file}")

if __name__ == "__main__":
    main()
