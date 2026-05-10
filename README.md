# Safe Voting App
*A secure, blockchain-powered voting system featuring a graphical interface, background data auditing, and strict access controls.*

---

##  PART 1: Project Overview (Plain English)
This project is a decentralized application (DApp) that ensures voting integrity. It connects a **Blockchain backend** (Smart Contracts) to a **Python frontend** (GUI).
- **The Engine:** Smart Contracts on the blockchain manage candidates and "Voting Coins." Only the Admin can print coins or add candidates.
- **The Interface:** A GUI allows users to register, vote, and see their transaction history.
- **The Security:** Since it's on a blockchain, votes cannot be deleted or changed once cast.

##  PART 2: Project Defense (How we met the Rubric)
*Use this as your cheat sheet to explain your work to the grader.*

1. **Smart Contracts (Task A1-A2):** Built using Solidity. Uses `onlyOwner` modifiers for security.
2. **Custom Coin:** We built a full ERC-20 coin without external libraries to follow the strict project rules.
3. **Manual Block Scanning (Task U4, S3, S5):** Instead of using easy event-filters, we manually scan the chain from block 0 using `w3.eth.get_block()` to tally votes and history, meeting the "full marks" checklist.
4. **Error Handling (Task U1):** Every transaction is wrapped in `try/except` with a mandatory `wait_for_transaction_receipt` to ensure the UI never crashes.
5. **Bonus GUI:** Built using native `tkinter` to ensure a premium visual experience without breaking the "no external framework" rule.

---

##  PART 3: Instruction Manual (User Guide)

### 1. Setup Instructions
1. Start **Ganache** on port `8545`.
2. Open your terminal in this folder and run:
   ```bash
   ./run_project.sh
   ```
   *This script installs dependencies, deploys contracts, runs security tests, and launches the GUI in one go.*

### 2. How to Use (Users)
1. Select your account and click **Connect**.
2. If new, enter your name to register on-chain.
3. View candidates, select one, and click **Cast Vote**.
4. Click **View My History** to see your blockchain transaction record.

### 3. How to Use (Administrators)
1. Login as **Account 0**.
2. Click ** Admin Panel** (Password: `admin123`).
3. Add candidates, mint coins, or use the **Emergency Pause** button to stop all voting.

### 4. Background Monitoring
- **Live Alerts:** The bottom of the GUI features a **System Log** that alerts you instantly when a new vote happens on the blockchain.
- **CSV Export:** Run `./run_project.sh` to generate a `balances_snapshot.csv` containing all account balances.
