import json
import os
from web3 import Web3

class TransactionSender:
    def __init__(self, rpc_url="http://127.0.0.1:8545"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node.")
        
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(self.base_dir, "contract_data.json")
        self._load_contracts()

    def _load_contracts(self):
        if not os.path.exists(self.data_path):
            raise FileNotFoundError("contract_data.json not found. Run auto_setup.py first.")
        with open(self.data_path, "r") as f:
            data = json.load(f)
        
        self.coin_address = data["VotingCoin"]["address"]
        self.coin_abi = data["VotingCoin"]["abi"]
        self.coin_contract = self.w3.eth.contract(address=self.coin_address, abi=self.coin_abi)
        
        self.app_address = data["SafeVotingApp"]["address"]
        self.app_abi = data["SafeVotingApp"]["abi"]
        self.app_contract = self.w3.eth.contract(address=self.app_address, abi=self.app_abi)

    def send_tx(self, contract_func, from_address):
        try:
            tx_hash = contract_func.transact({'from': from_address})
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt
        except Exception as e:
            raise Exception(f"Transaction failed on-chain: {e}")

    def call_func(self, contract_func):
        return contract_func.call()
