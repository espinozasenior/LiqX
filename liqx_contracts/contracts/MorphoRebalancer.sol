// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MorphoRebalancer
 * @notice Shared rebalancing logic contract for EIP-7702 delegation
 * @dev This contract is designed to be used via EIP-7702 delegation, allowing EOAs
 *      to temporarily execute this contract's code for rebalancing operations.
 *
 * KEY CONCEPT: This is ONE shared contract for ALL users
 * - Users don't deploy their own contracts
 * - Users sign EIP-7702 authorization to delegate to this contract's code
 * - When rebalancing executes, the user's EOA temporarily "becomes" this contract
 * - User assets never leave their EOA - they stay in full control
 */

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
}

interface IERC4626 {
    function deposit(uint256 assets, address receiver) external returns (uint256 shares);
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256 assets);
    function withdraw(uint256 assets, address receiver, address owner) external returns (uint256 shares);
    function balanceOf(address account) external view returns (uint256);
    function convertToAssets(uint256 shares) external view returns (uint256);
}

contract MorphoRebalancer {
    // USDC on Base mainnet
    address public constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;

    // Events for tracking rebalancing operations
    event RebalanceExecuted(
        address indexed user,
        address indexed fromVault,
        address indexed toVault,
        uint256 amount,
        uint256 timestamp
    );

    event PartialRebalanceExecuted(
        address indexed user,
        address indexed fromVault,
        address indexed toVault,
        uint256 sharesRedeemed,
        uint256 assetsReceived,
        uint256 timestamp
    );

    /**
     * @notice Execute a full rebalance from one Morpho vault to another
     * @dev When called via EIP-7702, msg.sender is the user's EOA
     *      The EOA temporarily executes this contract's code
     * @param fromVault The Morpho vault to withdraw from (ERC4626)
     * @param toVault The Morpho vault to deposit to (ERC4626)
     * @param shares The number of shares to redeem from the source vault
     */
    function executeRebalance(
        address fromVault,
        address toVault,
        uint256 shares
    ) external {
        require(fromVault != address(0), "Invalid from vault");
        require(toVault != address(0), "Invalid to vault");
        require(fromVault != toVault, "Cannot rebalance to same vault");
        require(shares > 0, "Shares must be greater than 0");

        IERC4626 sourceVault = IERC4626(fromVault);
        IERC4626 targetVault = IERC4626(toVault);
        IERC20 usdc = IERC20(USDC);

        // 1. Redeem shares from source vault (withdraw USDC)
        //    When called via EIP-7702, msg.sender is the user's EOA
        //    So USDC goes directly to user's EOA
        uint256 assetsReceived = sourceVault.redeem(
            shares,
            msg.sender,  // Receiver: user's EOA
            msg.sender   // Owner: user's EOA
        );

        require(assetsReceived > 0, "No assets received from redemption");

        // 2. Approve target vault to spend USDC
        usdc.approve(toVault, assetsReceived);

        // 3. Deposit USDC to target vault
        //    Shares go to user's EOA
        uint256 sharesReceived = targetVault.deposit(assetsReceived, msg.sender);

        require(sharesReceived > 0, "No shares received from deposit");

        emit RebalanceExecuted(
            msg.sender,
            fromVault,
            toVault,
            assetsReceived,
            block.timestamp
        );
    }

    /**
     * @notice Execute a partial rebalance with explicit asset amount
     * @dev Useful when you want to rebalance a specific USDC amount rather than all shares
     * @param fromVault The Morpho vault to withdraw from (ERC4626)
     * @param toVault The Morpho vault to deposit to (ERC4626)
     * @param assets The amount of USDC to rebalance
     */
    function executePartialRebalance(
        address fromVault,
        address toVault,
        uint256 assets
    ) external {
        require(fromVault != address(0), "Invalid from vault");
        require(toVault != address(0), "Invalid to vault");
        require(fromVault != toVault, "Cannot rebalance to same vault");
        require(assets > 0, "Assets must be greater than 0");

        IERC4626 sourceVault = IERC4626(fromVault);
        IERC4626 targetVault = IERC4626(toVault);
        IERC20 usdc = IERC20(USDC);

        // 1. Withdraw specific asset amount from source vault
        uint256 sharesRedeemed = sourceVault.withdraw(
            assets,
            msg.sender,  // Receiver: user's EOA
            msg.sender   // Owner: user's EOA
        );

        require(sharesRedeemed > 0, "No shares redeemed");

        // 2. Approve target vault to spend USDC
        usdc.approve(toVault, assets);

        // 3. Deposit USDC to target vault
        uint256 sharesReceived = targetVault.deposit(assets, msg.sender);

        require(sharesReceived > 0, "No shares received from deposit");

        emit PartialRebalanceExecuted(
            msg.sender,
            fromVault,
            toVault,
            sharesRedeemed,
            assets,
            block.timestamp
        );
    }

    /**
     * @notice Emergency function to withdraw all USDC from a vault
     * @dev Only callable by the EOA owner via EIP-7702 delegation
     * @param vault The Morpho vault to withdraw from
     */
    function emergencyWithdraw(address vault) external {
        require(vault != address(0), "Invalid vault");

        IERC4626 vaultContract = IERC4626(vault);

        // Get all shares owned by user (msg.sender is user's EOA via EIP-7702)
        uint256 shares = vaultContract.balanceOf(msg.sender);
        require(shares > 0, "No shares to withdraw");

        // Redeem all shares
        vaultContract.redeem(shares, msg.sender, msg.sender);
    }

    /**
     * @notice Get the USDC balance of a user in a specific vault
     * @param vault The Morpho vault address
     * @param user The user's address
     * @return The USDC value of the user's shares in the vault
     */
    function getVaultBalance(address vault, address user) external view returns (uint256) {
        IERC4626 vaultContract = IERC4626(vault);
        uint256 shares = vaultContract.balanceOf(user);
        return vaultContract.convertToAssets(shares);
    }
}
