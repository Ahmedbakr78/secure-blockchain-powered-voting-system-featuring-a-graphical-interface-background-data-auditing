// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VotingCoin {
    string public name = "Voting Coin";
    string public symbol = "VTC";
    uint8 public decimals = 18;
    uint256 public totalSupply;

    address public admin;
    address public authorizedApp;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event CoinMinted(address indexed to, uint256 amount);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }

    constructor() {
        admin = msg.sender;
        // Give the Admin a fixed pool of 100 VTC to distribute
        totalSupply = 100 * (10**18);
        balanceOf[admin] = totalSupply;
        emit Transfer(address(0), admin, totalSupply);
    }

    function setAuthorizedApp(address _app) public onlyAdmin {
        authorizedApp = _app;
    }

    function mint(address to, uint256 amount) public onlyAdmin {
        require(balanceOf[admin] >= amount, "Insufficient Admin balance to distribute");
        balanceOf[admin] -= amount;
        balanceOf[to] += amount;
        emit Transfer(admin, to, amount);
        emit CoinMinted(to, amount);
    }

    function burn(address from, uint256 amount) public {
        require(msg.sender == admin || msg.sender == from || msg.sender == authorizedApp, "Not authorized");
        require(balanceOf[from] >= amount, "Insufficient balance");
        balanceOf[from] -= amount;
        totalSupply -= amount;
        emit Transfer(from, address(0), amount);
    }

    function transfer(address to, uint256 value) public returns (bool success) {
        require(balanceOf[msg.sender] >= value, "Insufficient balance");
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        emit Transfer(msg.sender, to, value);
        return true;
    }

    function approve(address spender, uint256 value) public returns (bool success) {
        allowance[msg.sender][spender] = value;
        emit Approval(msg.sender, spender, value);
        return true;
    }

    function transferFrom(address from, address to, uint256 value) public returns (bool success) {
        require(value <= balanceOf[from], "Insufficient balance");
        require(value <= allowance[from][msg.sender], "Allowance exceeded");
        
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        
        emit Transfer(from, to, value);
        return true;
    }
}
