import json
import os
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
    original_admin = w3.eth.accounts[0]
    new_admin = w3.eth.accounts[2]
    
    print(f"Original Admin: {original_admin}")
    print(f"New Admin candidate: {new_admin}")
    
    print("\n1. Doing an admin action as the original admin...")
    try:
        tx_hash = app_contract.functions.batchUpdateCandidates([0], ["Temp1"]).transact({'from': original_admin})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Action succeeded.")
    except Exception as e:
        print(f"Action failed: {e}")
        return
        
    print("\n2. Transferring ownership to the new account...")
    try:
        tx_hash = app_contract.functions.transferOwnership(new_admin).transact({'from': original_admin})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Ownership transferred.")
    except Exception as e:
        print(f"Transfer failed: {e}")
        return
        
    print("\n3. Confirming the same action now fails from the original admin...")
    try:
        tx_hash = app_contract.functions.batchUpdateCandidates([0], ["Temp2"]).transact({'from': original_admin})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("FAIL: Action succeeded from original admin.")
    except Exception as e:
        print(f"SUCCESS: Action blocked from original admin. Error: {e}")
        
    print("\n4. Confirming the action succeeds from the new admin...")
    try:
        tx_hash = app_contract.functions.batchUpdateCandidates([0], ["Temp3"]).transact({'from': new_admin})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("SUCCESS: Action succeeded from new admin.")
    except Exception as e:
        print(f"FAIL: Action failed from new admin. Error: {e}")

    print("\n5. Restoring ownership to original admin for manual GUI testing...")
    try:
        tx_hash = app_contract.functions.transferOwnership(original_admin).transact({'from': new_admin})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Ownership restored.")
    except Exception as e:
        print(f"Failed to restore ownership: {e}")

if __name__ == "__main__":
    main()
