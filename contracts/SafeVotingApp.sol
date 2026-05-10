// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IVotingCoin {
    function balanceOf(address account) external view returns (uint256);
    function burn(address from, uint256 amount) external;
}

contract SafeVotingApp {
    address public admin;
    bool public paused;
    address public votingCoinAddress;
    
    struct Candidate {
        string name;
        uint256 voteCount;
        bool exists;
    }
    
    mapping(uint256 => Candidate) public candidates;
    uint256 public candidateCount;
    
    mapping(address => string) public userNames;
    mapping(address => bool) public hasRegistered;
    
    event CandidateAdded(uint256 indexed id, string name);
    event CandidateUpdated(uint256 indexed id, string name);
    event UserRegistered(address indexed user, string name);
    event VoteCast(address indexed voter, uint256 indexed candidateId);
    event SystemPaused(address indexed admin);
    event SystemResumed(address indexed admin);
    event OwnershipTransferred(address indexed oldAdmin, address indexed newAdmin);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "Not an admin");
        _;
    }
    
    modifier whenNotPaused() {
        require(!paused, "System is paused");
        _;
    }
    
    constructor(address _votingCoinAddress) {
        admin = msg.sender;
        paused = false;
        votingCoinAddress = _votingCoinAddress;
    }
    
    function getAdmin() public view returns (address) {
        return admin;
    }
    
    function transferOwnership(address newAdmin) public onlyAdmin {
        require(newAdmin != address(0), "Invalid address");
        address oldAdmin = admin;
        admin = newAdmin;
        emit OwnershipTransferred(oldAdmin, newAdmin);
    }
    
    function pause() public onlyAdmin {
        paused = true;
        emit SystemPaused(admin);
    }
    
    function resume() public onlyAdmin {
        paused = false;
        emit SystemResumed(admin);
    }
    
    function registerUser(string memory name) public whenNotPaused {
        require(!hasRegistered[msg.sender], "User already registered");
        userNames[msg.sender] = name;
        hasRegistered[msg.sender] = true;
        emit UserRegistered(msg.sender, name);78
    }
    
    function batchUpdateCandidates(uint256[] memory ids, string[] memory names) public onlyAdmin {
        require(ids.length == names.length, "Arrays length mismatch");
        for (uint i = 0; i < ids.length; i++) {
            require(bytes(names[i]).length > 0, "Invalid candidate name");
            if (ids[i] == 0) {
                // Add
                candidateCount++;
                candidates[candidateCount] = Candidate(names[i], 0, true);
                emit CandidateAdded(candidateCount, names[i]);
            } else {
                // Update
                require(candidates[ids[i]].exists, "Candidate does not exist");
                candidates[ids[i]].name = names[i];
                emit CandidateUpdated(ids[i], names[i]);
            }
        }
    }
    
    function vote(uint256 _candidateId) public whenNotPaused {
        require(hasRegistered[msg.sender], "Must register first");
        require(candidates[_candidateId].exists, "Invalid candidate");
        
        // CHECK AND SPEND VTC
        IVotingCoin coin = IVotingCoin(votingCoinAddress);
        require(coin.balanceOf(msg.sender) >= 1 * 10**18, "You need at least 1 VTC to vote!");
        
        // Consume the ticket
        coin.burn(msg.sender, 1 * 10**18);
        
        candidates[_candidateId].voteCount++;
        emit VoteCast(msg.sender, _candidateId);
    }
}
