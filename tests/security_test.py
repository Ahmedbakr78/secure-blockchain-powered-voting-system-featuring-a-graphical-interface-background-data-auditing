import json
import os
import sys
from web3 import Web3

def get_app_contract(w3):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "contract_data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    return w3.eth.contract(address=data["SafeVotingApp"]["address"], abi=data["SafeVotingApp"]["abi"])

def main():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("Not connected to Ganache.")
        return
        
    app_contract = get_app_contract(w3)
    admin_account = w3.eth.accounts[0]
    normal_account = w3.eth.accounts[1]
    
    print(f"Admin: {admin_account}")
    print(f"Normal User: {normal_account}")
    
    print("\nAttempting Admin action (add candidate) as Normal User...")
    try:
        tx_hash = app_contract.functions.batchUpdateCandidates([0], ["Hacker Candidate"]).transact({'from': normal_account})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("FAIL: Action succeeded. Security test failed.")
        sys.exit(1)
    except Exception as e:
        print(f"SUCCESS: Action blocked as expected. Error: {str(e)}")

if __name__ == "__main__":
    main()
