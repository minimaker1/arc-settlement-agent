// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title SettlementRouter
/// @notice Minimal FX-aware settlement router, live on Arc mainnet.
/// On Arc, USDC is the native gas token, so a settlement is simply native value
/// (USDC) forwarded to the recipient. The FX-aware Settlement Agent computes the
/// route off-chain (Pyth basis + confidence/staleness gate) and records the
/// rate used, the chosen route, and an invoice/payout memo on-chain — giving
/// every settlement a verifiable, reconcilable receipt.
contract SettlementRouter {
    /// @param from   payer (the agent's wallet)
    /// @param to     recipient
    /// @param amount USDC settled (18 decimals, native on Arc)
    /// @param refId  invoice / payout id (reconciliation memo)
    /// @param fxRate rate the agent used, scaled by 1e8 (0 if not applicable)
    /// @param route  "direct_usdc" / "onchain_swap" (bytes32-encoded)
    event Settled(
        address indexed from,
        address indexed to,
        uint256 amount,
        bytes32 indexed refId,
        int64 fxRate,
        bytes32 route
    );

    /// @notice Settle `msg.value` USDC to `to`, recording FX context on-chain.
    function settle(address to, bytes32 refId, int64 fxRate, bytes32 route)
        external
        payable
    {
        require(to != address(0), "bad recipient");
        require(msg.value > 0, "no value");
        (bool ok, ) = to.call{value: msg.value}("");
        require(ok, "transfer failed");
        emit Settled(msg.sender, to, msg.value, refId, fxRate, route);
    }

    /// @notice Reject bare transfers — settlements must carry context via settle().
    receive() external payable {
        revert("use settle()");
    }
}
