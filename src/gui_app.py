import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, scrolledtext
import sys
import os
import threading
import time
from transaction_sender import TransactionSender

class SafeVotingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Safe Voting App - Final Edition")
        self.root.geometry("750x750")
        
        try:
            self.tx_sender = TransactionSender()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to Ganache: {e}")
            sys.exit(1)
            
        self.user_address = None
        self.user_name = "Guest"
        self.admin_address = self.tx_sender.call_func(self.tx_sender.app_contract.functions.getAdmin())
        self.is_running = False  # Track if dashboard is active
        
        self.build_login_screen()

    def build_login_screen(self):
        self.is_running = False # Stop background threads
        self.clear_window()
        tk.Label(self.root, text="Safe Voting App", font=("Arial", 26, "bold"), fg="#2c3e50").pack(pady=40)
        tk.Label(self.root, text="Select account to connect (Loading chain data...):", font=("Arial", 11)).pack()
        
        self.account_var = tk.StringVar()
        self.acc_dropdown = ttk.Combobox(self.root, textvariable=self.account_var, width=80, state="readonly")
        self.acc_dropdown.pack(pady=15)
        
        loading_lbl = tk.Label(self.root, text="Reading Ganache balances...", font=("Arial", 9), fg="blue")
        loading_lbl.pack()
        
        def load_accounts():
            options = []
            try:
                for i, acc in enumerate(self.tx_sender.w3.eth.accounts):
                    bal = self.tx_sender.w3.eth.get_balance(acc)
                    eth = self.tx_sender.w3.from_wei(bal, 'ether')
                    reg = "✅ Registered" if self.tx_sender.call_func(self.tx_sender.app_contract.functions.hasRegistered(acc)) else "❌ New"
                    label = f"[{i}] {acc[:10]}... | {eth:.2f} ETH | {reg}"
                    options.append(label)
                
                def _update():
                    self.acc_dropdown['values'] = options
                    self.acc_dropdown.current(0)
                    loading_lbl.config(text="Ready to connect.", fg="green")
                self.root.after(0, _update)
            except Exception as e:
                self.root.after(0, lambda: loading_lbl.config(text=f"Connection Error: {e}", fg="red"))
        
        threading.Thread(target=load_accounts, daemon=True).start()
        
        tk.Button(self.root, text="Connect to Wallet", command=self.handle_login, bg="#3498db", fg="white", font=("Arial", 12, "bold"), width=30, height=2).pack(pady=20)
        tk.Label(self.root, text="⚠️ Local test accounts only. Never use real private keys.", font=("Arial", 9), fg="#7f8c8d").pack(side="bottom", pady=10)

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def handle_login(self):
        idx_str = self.account_var.get()
        if not idx_str: return
        idx = int(idx_str.split("]")[0][1:])
        self.user_address = self.tx_sender.w3.eth.accounts[idx]
        
        # Small delay before registration dialog to ensure window focus on macOS
        self.root.after(100, self._check_registration)

    def _check_registration(self):
        has_reg = self.tx_sender.call_func(self.tx_sender.app_contract.functions.hasRegistered(self.user_address))
        if has_reg:
            self.user_name = self.tx_sender.call_func(self.tx_sender.app_contract.functions.userNames(self.user_address))
            self.build_dashboard()
        else:
            name = simpledialog.askstring("Register", "First-time visitor! Please enter your name to register on-chain:")
            if name:
                try:
                    self.tx_sender.send_tx(self.tx_sender.app_contract.functions.registerUser(name), self.user_address)
                    self.user_name = name
                    messagebox.showinfo("Success", f"Welcome {name}! Your profile is now saved on the blockchain.")
                    self.build_dashboard()
                except Exception as e:
                    messagebox.showerror("Error", f"Registration failed: {e}")
            else:
                messagebox.showwarning("Warning", "Blockchain registration is required.")

    def build_dashboard(self):
        self.is_running = True
        self.clear_window()
        
        # Header Area
        header_frame = tk.Frame(self.root, bg="#2c3e50", pady=15)
        header_frame.pack(fill="x")
        
        role = "ADMIN" if self.user_address == self.admin_address else "VOTER"
        tk.Label(header_frame, text=f"👤 {self.user_name} ({role})", font=("Arial", 14, "bold"), fg="white", bg="#2c3e50").pack(side="left", padx=20)
        tk.Label(header_frame, text=f"{self.user_address[:15]}...", font=("Arial", 10), fg="#bdc3c7", bg="#2c3e50").pack(side="left")
        
        admin_btn_text = "🔒 Admin Panel" if role == "ADMIN" else "🚫 Admin Locked"
        self.admin_btn = tk.Button(header_frame, text=admin_btn_text, command=self.admin_login, 
                                   bg="#e74c3c" if role == "ADMIN" else "#7f8c8d", 
                                   fg="white", relief="flat", font=("Arial", 10, "bold"))
        self.admin_btn.pack(side="right", padx=20)
        
        # Main Dashboard Layout
        content_frame = tk.Frame(self.root, pady=20, padx=20)
        content_frame.pack(fill="both", expand=True)
        
        # Left Side (Data & Info)
        left_side = tk.Frame(content_frame)
        left_side.pack(side="left", fill="both", expand=True)
        
        bal_box = tk.LabelFrame(left_side, text=" Live Balances ", font=("Arial", 10, "bold"), padx=10, pady=10)
        bal_box.pack(fill="x", pady=(0, 20))
        
        self.lbl_eth = tk.Label(bal_box, text="ETH: Loading...", font=("Arial", 12))
        self.lbl_eth.pack(anchor="w")
        self.lbl_vtc = tk.Label(bal_box, text="VTC: Loading...", font=("Arial", 12))
        self.lbl_vtc.pack(anchor="w")
        
        self.lbl_status = tk.Label(bal_box, text="System: Syncing...", font=("Arial", 10, "bold"), pady=5)
        self.lbl_status.pack(anchor="w")
        
        tk.Label(left_side, text="Available Candidates", font=("Arial", 12, "bold")).pack(anchor="w")
        
        # Using Treeview for a professional table look
        cols = ("name", "votes")
        self.cand_tree = ttk.Treeview(left_side, columns=cols, show="headings", height=8)
        self.cand_tree.heading("name", text="Candidate Name")
        self.cand_tree.heading("votes", text="Vote Count")
        self.cand_tree.column("name", width=250)
        self.cand_tree.column("votes", width=100, anchor="center")
        self.cand_tree.pack(fill="both", expand=True, pady=5)
        
        # Right Side (Controls)
        right_side = tk.Frame(content_frame, padx=20)
        right_side.pack(side="right", fill="y")
        
        tk.Button(right_side, text="Cast Vote", command=self.vote, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=20, height=2).pack(pady=10)
        tk.Button(right_side, text="View My History", command=self.show_history, width=20, height=1).pack(pady=5)
        tk.Button(right_side, text="Refresh Data", command=self.refresh_data, width=20, height=1).pack(pady=5)
        tk.Button(right_side, text="Disconnect", command=self.build_login_screen, width=20, height=1).pack(pady=20)
        
        # Bottom Area (System Logs & Alerts)
        log_label = tk.Label(self.root, text="System Logs & On-Chain Alerts", font=("Arial", 10, "bold"), fg="#7f8c8d")
        log_label.pack(anchor="w", padx=20)
        
        self.log_area = scrolledtext.ScrolledText(self.root, height=12, font=("Courier", 10), bg="#1e1e1e", fg="#00ff00")
        self.log_area.pack(fill="x", padx=20, pady=(0, 20))
        
        self.log("Connected to SafeVotingApp. State: OK.")
        self.refresh_data()
        self.start_alert_daemon()

    def log(self, msg):
        def _append():
            timestamp = time.strftime("[%H:%M:%S] ")
            self.log_area.insert(tk.END, f"{timestamp} {msg}\n")
            self.log_area.see(tk.END)
        self.root.after(0, _append)

    def refresh_data(self):
        def _task():
            try:
                # Refresh Balances
                eth_bal = self.tx_sender.w3.eth.get_balance(self.user_address)
                eth_str = f"ETH: {self.tx_sender.w3.from_wei(eth_bal, 'ether'):.4f}"
                
                coin_bal = self.tx_sender.call_func(self.tx_sender.coin_contract.functions.balanceOf(self.user_address))
                decimals = self.tx_sender.call_func(self.tx_sender.coin_contract.functions.decimals())
                vtc_str = f"VTC: {coin_bal / (10**decimals):.2f}"
                
                # Candidates
                c_data = []
                count = self.tx_sender.call_func(self.tx_sender.app_contract.functions.candidateCount())
                new_ids = []
                for i in range(1, count + 1):
                    cand = self.tx_sender.call_func(self.tx_sender.app_contract.functions.candidates(i))
                    if cand[2]:
                        c_data.append((cand[0], cand[1]))
                        new_ids.append(i)
                
                is_paused = self.tx_sender.call_func(self.tx_sender.app_contract.functions.paused())
                
                def _ui():
                    self.lbl_eth.config(text=eth_str)
                    self.lbl_vtc.config(text=vtc_str)
                    for item in self.cand_tree.get_children(): self.cand_tree.delete(item)
                    for d in c_data: self.cand_tree.insert("", tk.END, values=d)
                    self.candidate_ids = new_ids
                    if is_paused: self.lbl_status.config(text="🔴 SYSTEM PAUSED", fg="red")
                    else: self.lbl_status.config(text="🟢 SYSTEM ACTIVE", fg="green")
                    self.log("Syncing with Blockchain... Success.")
                
                if self.is_running: self.root.after(0, _ui)
            except Exception as e:
                self.log(f"Refresh failed: {e}")
        
        threading.Thread(target=_task, daemon=True).start()

    def vote(self):
        selection = self.cand_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a candidate from the table.")
            return
        
        item_idx = self.cand_tree.index(selection[0])
        c_id = self.candidate_ids[item_idx]
        self.log(f"Initiating vote for Candidate ID: {c_id}...")
        try:
            receipt = self.tx_sender.send_tx(self.tx_sender.app_contract.functions.vote(c_id), self.user_address)
            self.log(f"TX Confirmed! Hash: {receipt.transactionHash.hex()[:10]}... Block: {receipt.blockNumber}")
            messagebox.showinfo("Success", "Your vote has been recorded on the blockchain!")
            self.refresh_data()
        except Exception as e:
            self.log(f"TX REVERTED: {e}")
            messagebox.showerror("Error", str(e))

    def show_history(self):
        hist_win = tk.Toplevel(self.root)
        hist_win.title("Blockchain Activity Ledger")
        hist_win.geometry("900x550")
        
        columns = ("block", "time", "from", "action", "value")
        tree = ttk.Treeview(hist_win, columns=columns, show="headings")
        tree.heading("block", text="Block")
        tree.heading("time", text="Timestamp")
        tree.heading("from", text="Sender")
        tree.heading("action", text="Type")
        tree.heading("value", text="Details / Value")
        
        tree.column("block", width=60, anchor="center")
        tree.column("time", width=140, anchor="center")
        tree.column("from", width=120, anchor="center")
        tree.column("action", width=150)
        tree.column("value", width=380)
        
        # Scrollbar for the table
        vsb = ttk.Scrollbar(hist_win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        tree.pack(fill="both", expand=True, padx=15, pady=5)
        
        lbl = tk.Label(hist_win, text="Scanning for relevant transactions...", font=("Arial", 10, "italic"))
        lbl.pack()
        
        def run_scan():
            for item in tree.get_children(): tree.delete(item)
            lbl.config(text="Scanning blockchain... Please wait.", fg="blue")
            try:
                cand_map = {}
                try:
                    c_count = self.tx_sender.call_func(self.tx_sender.app_contract.functions.candidateCount())
                    for i in range(1, c_count + 1):
                        c = self.tx_sender.call_func(self.tx_sender.app_contract.functions.candidates(i))
                        cand_map[i] = c[0]
                except: pass

                latest = self.tx_sender.w3.eth.get_block_number()
                found_count = 0
                for i in range(latest + 1):
                    block = self.tx_sender.w3.eth.get_block(i, full_transactions=True)
                    b_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(block.timestamp))
                    
                    for tx in block.transactions:
                        is_app_tx = tx['to'] == self.tx_sender.app_contract.address
                        is_coin_tx = tx['to'] == self.tx_sender.coin_contract.address
                        is_from_me = tx['from'] == self.user_address
                        
                        if self.user_address == self.admin_address:
                            is_relevant = is_app_tx or is_coin_tx
                        else:
                            is_relevant = (is_app_tx or is_coin_tx) and is_from_me

                        if is_relevant:
                            action = "Contract Call"
                            details = "0.00 ETH"
                            sender = f"{tx['from'][:6]}...{tx['from'][-4:]}"
                            tx_input = tx.get('input', '0x').hex() if isinstance(tx.get('input'), bytes) else tx.get('input', '0x')
                            
                            if is_app_tx:
                                try:
                                    func_obj, func_params = self.tx_sender.app_contract.decode_function_input(tx_input)
                                    fname = func_obj.fn_name
                                    action = f"App: {fname}"
                                    if fname == "vote":
                                        c_id = func_params['_candidateId']
                                        details = f"Voted for: {cand_map.get(c_id, f'ID {c_id}')}"
                                    elif fname == "registerUser":
                                        details = f"Registered: {func_params['name']}"
                                    elif fname == "batchUpdateCandidates":
                                        details = f"Batch added {len(func_params['names'])} candidates"
                                    elif fname == "transferOwnership":
                                        details = f"New Admin: {func_params['newAdmin'][:10]}..."
                                    elif fname in ["pause", "resume"]:
                                        details = f"State: {fname.upper()}"
                                    else: details = "Logic Call"
                                except: action, details = "App: Interaction", "Manual"
                                
                            elif is_coin_tx:
                                try:
                                    func_obj, func_params = self.tx_sender.coin_contract.decode_function_input(tx_input)
                                    fname = func_obj.fn_name
                                    action = f"Coin: {fname}"
                                    if fname == "mint":
                                        amt = func_params['amount'] / (10**18)
                                        details = f"Minted {amt:.1f} VTC"
                                    elif fname == "transfer":
                                        amt = func_params['value'] / (10**18)
                                        details = f"Sent {amt:.1f} VTC"
                                    else: details = "Token Logic"
                                except: action, details = "Coin: Interaction", "Manual"
                                
                            found_count += 1
                            self.root.after(0, lambda b=block.number, t=b_time, s=sender, a=action, d=details: 
                                            tree.insert("", tk.END, values=(b, t, s, a, d)))
                
                self.root.after(0, lambda: lbl.config(text=f"Scan Complete. Found {found_count} relevant events.", fg="green"))
            except Exception as e:
                self.root.after(0, lambda err=e: lbl.config(text=f"Scan Error: {err}", fg="red"))
        
        tk.Button(hist_win, text="🔄 Refresh History", command=lambda: threading.Thread(target=run_scan, daemon=True).start()).pack(pady=5)
        threading.Thread(target=run_scan, daemon=True).start()

    def admin_login(self):
        live_admin = self.tx_sender.call_func(self.tx_sender.app_contract.functions.getAdmin())
        if self.user_address != live_admin:
            messagebox.showerror("Access Denied", f"You are not the Admin. Current Admin: {live_admin[:10]}...")
            return
        
        pwd = simpledialog.askstring("Admin Unlock", "Enter System Password:", show="*")
        if pwd == "admin123":
            self.build_admin_panel()
        elif pwd is not None:
            messagebox.showerror("Error", "Incorrect password.")

    def build_admin_panel(self):
        admin_win = tk.Toplevel(self.root)
        admin_win.title("Master Admin Panel")
        admin_win.geometry("450x400")
        
        tk.Label(admin_win, text="System Controls", font=("Arial", 16, "bold"), pady=15).pack()
        
        def add_cand():
            n = simpledialog.askstring("Add", "Enter candidate name:", parent=admin_win)
            if n:
                try:
                    self.tx_sender.send_tx(self.tx_sender.app_contract.functions.batchUpdateCandidates([0], [n]), self.user_address)
                    self.log(f"Admin: Added candidate '{n}'")
                    self.refresh_data()
                except Exception as e: self.log(f"Admin Error: {e}")
        
        def mint():
            mint_win = tk.Toplevel(admin_win)
            mint_win.title("Mint Voting Coins")
            mint_win.geometry("400x300")
            
            tk.Label(mint_win, text="Select Target Account:", font=("Arial", 10)).pack(pady=10)
            
            # Filter: Admin cannot mint to themselves
            accounts = [f"[{i}] {acc}" for i, acc in enumerate(self.tx_sender.w3.eth.accounts) if acc != self.admin_address]
            acc_var = tk.StringVar()
            acc_drop = ttk.Combobox(mint_win, textvariable=acc_var, values=accounts, width=45, state="readonly")
            acc_drop.pack(pady=5)
            acc_drop.current(0)
            
            tk.Label(mint_win, text="Amount to Mint (VTC):", font=("Arial", 10)).pack(pady=10)
            amt_entry = tk.Entry(mint_win, width=20)
            amt_entry.pack(pady=5)
            amt_entry.insert(0, "100")
            
            def do_mint():
                to_str = acc_var.get()
                amt_str = amt_entry.get()
                if not to_str or not amt_str: return
                
                try:
                    to_addr = to_str.split("] ")[1]
                    amt_val = float(amt_str)
                    if amt_val <= 0:
                        messagebox.showerror("Error", "Amount must be greater than 0.", parent=mint_win)
                        return
                    
                    amount = int(amt_val * (10**18))
                    self.tx_sender.send_tx(self.tx_sender.coin_contract.functions.mint(to_addr, amount), self.user_address)
                    self.log(f"Admin: Successfully minted {amt_str} VTC to {to_addr[:10]}...")
                    messagebox.showinfo("Success", f"Minted {amt_str} VTC!", parent=mint_win)
                    self.refresh_data()
                    mint_win.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Invalid amount. Please enter a number.", parent=mint_win)
                except Exception as e:
                    self.log(f"Minting failed: {e}")
                    messagebox.showerror("Blockchain Error", str(e), parent=mint_win)
            
            tk.Button(mint_win, text="Confirm Mint", command=do_mint, bg="#27ae60", fg="white", font=("Arial", 10, "bold"), width=20).pack(pady=20)

        def toggle(p):
            try:
                if p: self.tx_sender.send_tx(self.tx_sender.app_contract.functions.pause(), self.user_address)
                else: self.tx_sender.send_tx(self.tx_sender.app_contract.functions.resume(), self.user_address)
                self.log(f"Admin: System {'Paused' if p else 'Resumed'}")
                self.refresh_data()
            except Exception as e: self.log(f"Admin Error: {e}")

        def batch_add():
            names_raw = simpledialog.askstring("Batch Add", "Enter names separated by commas (e.g. Dave,Eve,Frank):", parent=admin_win)
            if names_raw:
                names = [n.strip() for n in names_raw.split(",") if n.strip()]
                ids = [0] * len(names)
                try:
                    self.tx_sender.send_tx(self.tx_sender.app_contract.functions.batchUpdateCandidates(ids, names), self.user_address)
                    self.log(f"Admin: Batch added {len(names)} candidates.")
                    self.refresh_data()
                except Exception as e: self.log(f"Admin Error: {e}")

        tk.Button(admin_win, text="Add Single Candidate", command=add_cand, width=30).pack(pady=5)
        tk.Button(admin_win, text="Batch Add Candidates", command=batch_add, width=30).pack(pady=5)
        tk.Button(admin_win, text="Mint Voting Coins", command=mint, width=30).pack(pady=5)
        tk.Button(admin_win, text="PAUSE ALL VOTING", command=lambda: toggle(True), bg="#e67e22", fg="white", width=30).pack(pady=10)
        tk.Button(admin_win, text="RESUME ALL VOTING", command=lambda: toggle(False), bg="#2ecc71", fg="white", width=30).pack(pady=5)

    def start_alert_daemon(self):
        def poll():
            try:
                lb = self.tx_sender.w3.eth.get_block_number()
                while self.is_running:
                    c = self.tx_sender.w3.eth.get_block_number()
                    if c > lb:
                        for i in range(lb + 1, c + 1):
                            b = self.tx_sender.w3.eth.get_block(i, full_transactions=True)
                            for tx in b.transactions:
                                if tx['to'] == self.tx_sender.app_contract.address:
                                    try:
                                        f, _ = self.tx_sender.app_contract.decode_function_input(tx['input'])
                                        if f.fn_name == 'vote':
                                            self.log("🔔 ALERT: A NEW VOTE JUST HAPPENED!")
                                            self.refresh_data()
                                    except: pass
                        lb = c
                    time.sleep(2)
            except: pass
        threading.Thread(target=poll, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    SafeVotingGUI(root)
    root.mainloop()
