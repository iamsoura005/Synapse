// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title AgreementRegistry
/// @notice Immutable on-chain registry for SYNAPSE Living Contract hashes.
///         Each contract version is a new entry linked via previousHash.
contract AgreementRegistry {

    struct Agreement {
        bytes32 contentHash;
        address submitter;
        uint256 timestamp;
        uint256 version;
        bytes32 previousHash;   // 0x0 if first version
    }

    // contentHash -> Agreement
    mapping(bytes32 => Agreement) public agreements;

    // contractId (bytes32) -> ordered array of content hashes (version chain)
    mapping(bytes32 => bytes32[]) public versionChain;

    event AgreementRecorded(
        bytes32 indexed contentHash,
        address indexed submitter,
        uint256 timestamp,
        uint256 version
    );

    /// @notice Record a new contract version on-chain.
    /// @param contentHash  SHA-256 of the canonical JSON contract
    /// @param contractId   Stable ID across versions (UUID as bytes32)
    /// @param previousHash Hash of the previous version (0x0 if first)
    function record(
        bytes32 contentHash,
        bytes32 contractId,
        bytes32 previousHash
    ) external returns (bool) {
        require(agreements[contentHash].timestamp == 0, "Already recorded");

        uint256 version = versionChain[contractId].length + 1;

        agreements[contentHash] = Agreement({
            contentHash: contentHash,
            submitter: msg.sender,
            timestamp: block.timestamp,
            version: version,
            previousHash: previousHash
        });

        versionChain[contractId].push(contentHash);

        emit AgreementRecorded(contentHash, msg.sender, block.timestamp, version);
        return true;
    }

    /// @notice Verify that a hash was recorded.
    /// @return exists     True if recorded
    /// @return timestamp  Block timestamp of recording
    /// @return submitter  Address that submitted the hash
    function verify(bytes32 contentHash)
        external
        view
        returns (bool exists, uint256 timestamp, address submitter)
    {
        Agreement memory a = agreements[contentHash];
        return (a.timestamp > 0, a.timestamp, a.submitter);
    }

    /// @notice Get the full version chain for a contract ID.
    function getVersionChain(bytes32 contractId)
        external
        view
        returns (bytes32[] memory)
    {
        return versionChain[contractId];
    }
}
