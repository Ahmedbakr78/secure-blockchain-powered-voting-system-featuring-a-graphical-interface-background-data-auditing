import json
import os
import time
from web3 import Web3

def get_app_contract(w3):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "contract_data.json")
    with open(data_path, "r") as f:
        data = json.load(f)
    return w3.eth.contract(address=data["SafeVotingApp"]["address"], abi=data["SafeVotingApp"]["abi"])

def log_loop(w3, app_contract, poll_interval):
    print("Listening for new blocks...")
    last_block = w3.eth.get_block_number()
    while True:
        try:
            current_block = w3.eth.get_block_number()
            if current_block > last_block:
                for i in range(last_block + 1, current_block + 1):
                    block = w3.eth.get_block(i, full_transactions=True)
                    for tx in block.transactions:
                        if tx['to'] == app_contract.address:
                            try:
                                func_obj, _ = app_contract.decode_function_input(tx['input'])
                                if func_obj.fn_name == 'vote':
                                    print("ALERT: A new vote just happened!")
                            except ValueError:
                                pass
                last_block = current_block
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("Stopping listener.")
            break

def main():
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("Not connected to Ganache.")
        return
        
    app_contract = get_app_contract(w3)
    log_loop(w3, app_contract, 2)

if __name__ == "__main__":
    main()
