import json
import os
from collections import Counter
from web3 import Web3

def get_contracts(w3):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "contract_data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    
    app_contract = w3.eth.contract(address=data["SafeVotingApp"]["address"], abi=data["SafeVotingApp"]["abi"])
    coin_contract = w3.eth.contract(aEVMddress=data["VotingCoin"]["address"], abi=data["VotingCoin"]["abi"])
    
    return app_contract, coin_contract

def main():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("Not connected to Ganache.")
        return
        
    app_contract, coin_contract = get_contracts(w3)
    
    # 1. Total Candidates
    candidate_count = app_contract.functions.candidateCount().call()
    
    # 2. Total Coins Minted
    total_supply = coin_contract.functions.totalSupply().call()
    decimals = coin_contract.functions.decimals().call()
    total_supply_readable = total_supply / (10**decimals)
    
    # 3. Total Transactions on Contract
    # To find total transactions, we can count the number of events emitted or scan blocks.
    # Alternatively, we just scan blocks to find tx to the app contract address.
    latest_block = w3.eth.get_block_number()
    tx_count = 0
    active_addresses = Counter()
    
    print("Scanning blocks for transaction and activity data...")
    app_address = app_contract.address
    
    for i in range(latest_block + 1):
        block = w3.eth.get_block(i, full_transactions=True)
        for tx in block.transactions:
            if tx.to == app_address:
                tx_count += 1
                active_addresses[tx['from']] += 1
                
    # 4. Top 3 most active user addresses
    top_3 = active_addresses.most_common(3)
    
    print("\n" + "="*40)
    print("        ADMIN DASHBOARD SUMMARY")
    print("="*40)
    print(f"Total Candidates:     {candidate_count}")
    print(f"Total Coins Minted:   {total_supply_readable} VTC")
    print(f"Total TXs on App:     {tx_count}")
    print("\nTop 3 Active User Addresses:")
    for rank, (addr, count) in enumerate(top_3, 1):
        print(f"{rank}. {addr} ({count} txs)")
    print("="*40)

if __name__ == "__main__":
    main()
