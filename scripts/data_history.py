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
    
    print("Reading blockchain history for votes...")
    
    latest_block = w3.eth.get_block_number()
    vote_counts = {}
    
    for i in range(latest_block + 1):
        block = w3.eth.get_block(i, full_transactions=True)
        for tx in block.transactions:
            if tx['to'] == app_contract.address:
                try:
                    func_obj, func_params = app_contract.decode_function_input(tx['input'])
                    if func_obj.fn_name == 'vote':
                        c_id = func_params['_candidateId']
                        vote_counts[c_id] = vote_counts.get(c_id, 0) + 1
                except ValueError:
                    pass
        
    count = app_contract.functions.candidateCount().call()
    
    print("\n--- Data History Report ---")
    print(f"{'Candidate Name':<20} | {'Total Votes'}")
    print("-" * 35)
    
    for i in range(1, count + 1):
        cand = app_contract.functions.candidates(i).call()
        name = cand[0]
        votes = vote_counts.get(i, 0)
        print(f"{name:<20} | {votes}")

if __name__ == "__main__":
    main()
