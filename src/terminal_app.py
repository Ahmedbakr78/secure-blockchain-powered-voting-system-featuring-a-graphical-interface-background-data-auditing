import sys
import getpass
from transaction_sender import TransactionSender

def print_header(name=None):
    print("\n" + "="*50)
    print("           SAFE VOTING APP TERMINAL")
    if name:
        print(f"           Welcome, {name}!")
    print("="*50)

class TerminalApp:
    def __init__(self):
        try:
            self.tx_sender = TransactionSender()
        except Exception as e:
            print(f"Error initializing: {e}")
            sys.exit(1)
        
        print("Available accounts:")
        for i, acc in enumerate(self.tx_sender.w3.eth.accounts):
            print(f"[{i}] {acc}")
        
        try:
            acc_idx = int(input("\nSelect your account index (0-9): "))
            self.user_address = self.tx_sender.w3.eth.accounts[acc_idx]
        except:
            print("Invalid selection. Exiting.")
            sys.exit(1)
            
        self.admin_address = self.tx_sender.call_func(self.tx_sender.app_contract.functions.getAdmin())
        self.is_admin_acc = (self.user_address == self.admin_address)
        self.user_name = None

    def check_registration(self):
        has_reg = self.tx_sender.call_func(self.tx_sender.app_contract.functions.hasRegistered(self.user_address))
        if has_reg:
            self.user_name = self.tx_sender.call_func(self.tx_sender.app_contract.functions.userNames(self.user_address))
        else:
            print("\n*** First Time Visitor! ***")
            name = input("Please register your display name: ")
            print("Registering on blockchain...")
            try:
                self.tx_sender.send_tx(self.tx_sender.app_contract.functions.registerUser(name), self.user_address)
                self.user_name = name
                print("Registration successful!")
            except Exception as e:
                print(f"Registration failed: {e}")

    def display_candidates(self):
        count = self.tx_sender.call_func(self.tx_sender.app_contract.functions.candidateCount())
        print("\n--- Candidates ---")
        for i in range(1, count + 1):
            cand = self.tx_sender.call_func(self.tx_sender.app_contract.functions.candidates(i))
            if cand[2]: # exists
                print(f"[{i}] {cand[0]} - Votes: {cand[1]}")

    def vote(self):
        self.display_candidates()
        try:
            c_id = int(input("Enter candidate ID to vote for: "))
            print("Casting vote...")
            self.tx_sender.send_tx(self.tx_sender.app_contract.functions.vote(c_id), self.user_address)
            print("Vote successfully cast!")
        except Exception as e:
            print(f"Vote failed: {e}")

    def check_balances(self):
        addr = input("Enter address to check: ")
        if not addr:
            addr = self.user_address
        
        try:
            eth_bal = self.tx_sender.w3.eth.get_balance(addr)
            eth_bal_readable = self.tx_sender.w3.from_wei(eth_bal, 'ether')
            
            coin_bal = self.tx_sender.call_func(self.tx_sender.coin_contract.functions.balanceOf(addr))
            decimals = self.tx_sender.call_func(self.tx_sender.coin_contract.functions.decimals())
            coin_bal_readable = coin_bal / (10**decimals)
            
            print(f"\n--- Balances for {addr} ---")
            print(f"{'ETH Balance':<20} | {'Voting Coin Balance':<20}")
            print("-" * 45)
            print(f"{eth_bal_readable:<20} | {coin_bal_readable:<20}")
        except Exception as e:
            print(f"Error checking balances: {e}")

    def personal_history(self):
        addr = input("Enter address to check history: ")
        if not addr:
            addr = self.user_address
            
        print("\nScanning blockchain for history...")
        try:
            latest_block = self.tx_sender.w3.eth.get_block_number()
            user_events = []
            
            for i in range(latest_block + 1):
                block = self.tx_sender.w3.eth.get_block(i, full_transactions=True)
                for tx in block.transactions:
                    if tx['from'] == addr or tx['to'] == addr:
                        action = "Standard ETH Transfer"
                        value = self.tx_sender.w3.from_wei(tx['value'], 'ether')
                        
                        if tx['to'] == self.tx_sender.app_contract.address:
                            try:
                                func_obj, func_params = self.tx_sender.app_contract.decode_function_input(tx['input'])
                                action = f"App: {func_obj.fn_name}"
                            except ValueError:
                                action = "App: Interaction"
                        elif tx['to'] == self.tx_sender.coin_contract.address:
                            try:
                                func_obj, func_params = self.tx_sender.coin_contract.decode_function_input(tx['input'])
                                action = f"Coin: {func_obj.fn_name}"
                            except ValueError:
                                action = "Coin: Interaction"
                        elif not tx['to']:
                            action = "Contract Deployment"
                        
                        user_events.append({
                            'blockNumber': block.number,
                            'actionType': action,
                            'value': f"{value} ETH"
                        })
            
            print(f"\n--- History for {addr} ---")
            print(f"{'Block':<10} | {'Action':<30} | {'Value':<10}")
            print("-" * 55)
            for e in user_events:
                block = e['blockNumber']
                action = e['actionType']
                val = e['value']
                print(f"{block:<10} | {action:<30} | {val:<10}")
        except Exception as e:
            print(f"Error fetching history: {e}")

    def hidden_admin_menu(self):
        pwd = getpass.getpass("Enter Admin Password: ")
        if pwd != "admin123":
            print("Incorrect password.")
            return

        while True:
            print("\n--- HIDDEN ADMIN MENU ---")
            print("1. Add Candidate")
            print("2. Mint Coins")
            print("3. Pause System")
            print("4. Resume System")
            print("5. Exit Admin Menu")
            
            choice = input("Select an option: ")
            
            if choice == '1':
                name = input("Enter candidate name: ")
                try:
                    self.tx_sender.send_tx(self.tx_sender.app_contract.functions.batchUpdateCandidates([0], [name]), self.user_address)
                    print("Candidate added!")
                except Exception as e:
                    print(f"Failed: {e}")
            elif choice == '2':
                to = input("Enter recipient address: ")
                amt = int(input("Enter amount (raw units): "))
                try:
                    self.tx_sender.send_tx(self.tx_sender.coin_contract.functions.mint(to, amt), self.user_address)
                    print("Coins minted!")
                except Exception as e:
                    print(f"Failed: {e}")
            elif choice == '3':
                try:
                    self.tx_sender.send_tx(self.tx_sender.app_contract.functions.pause(), self.user_address)
                    print("System paused!")
                except Exception as e:
                    print(f"Failed: {e}")
            elif choice == '4':
                try:
                    self.tx_sender.send_tx(self.tx_sender.app_contract.functions.resume(), self.user_address)
                    print("System resumed!")
                except Exception as e:
                    print(f"Failed: {e}")
            elif choice == '5':
                break

    def run(self):
        self.check_registration()
        
        while True:
            print_header(self.user_name)
            print("1. View Candidates")
            print("2. Vote for Candidate")
            print("3. Check Balances")
            print("4. View Personal Activity History")
            print("5. Exit")
            print("99. (Hidden) Admin Login")
            
            choice = input("Select an option: ")
            
            if choice == '1':
                self.display_candidates()
            elif choice == '2':
                self.vote()
            elif choice == '3':
                self.check_balances()
            elif choice == '4':
                self.personal_history()
            elif choice == '5':
                print("Goodbye!")
                break
            elif choice == '99':
                self.hidden_admin_menu()
            else:
                print("Invalid choice.")

if __name__ == "__main__":
    app = TerminalApp()
    app.run()
