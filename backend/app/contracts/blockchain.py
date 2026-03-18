"""Polygon Amoy blockchain notarization for SYNAPSE Living Contracts."""
import hashlib
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# ABI for AgreementRegistry contract (only the functions we call)
AGREEMENT_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
            {"internalType": "bytes32", "name": "contractId",  "type": "bytes32"},
            {"internalType": "bytes32", "name": "previousHash","type": "bytes32"},
        ],
        "name": "record",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "contentHash", "type": "bytes32"}],
        "name": "verify",
        "outputs": [
            {"internalType": "bool",    "name": "exists",    "type": "bool"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "address", "name": "submitter", "type": "address"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


class PolygonNotarizer:
    """Notarize SYNAPSE Living Contracts on Polygon Amoy testnet."""

    def __init__(self):
        from web3 import Web3
        self.w3 = Web3(Web3.HTTPProvider(settings.POLYGON_AMOY_RPC_URL))
        if settings.DEPLOYER_PRIVATE_KEY:
            self.account = self.w3.eth.account.from_key(settings.DEPLOYER_PRIVATE_KEY)
        else:
            self.account = None

        if settings.AGREEMENT_REGISTRY_ADDRESS:
            self.contract = self.w3.eth.contract(
                address=settings.AGREEMENT_REGISTRY_ADDRESS,
                abi=AGREEMENT_REGISTRY_ABI,
            )
        else:
            self.contract = None

    def hash_contract(self, contract_data: dict) -> str:
        """SHA-256 hash of canonical JSON serialization."""
        canonical = json.dumps(contract_data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    async def notarize(
        self,
        contract_id: str,
        contract_data: dict,
        previous_hash: str = "",
    ) -> tuple[str, str, str]:
        """
        Notarize a contract on Polygon Amoy.
        Returns (content_hash, tx_hash, polygon_scan_url).
        """
        if not self.contract or not self.account:
            logger.warning("Blockchain not configured — returning mock hashes for development.")
            content_hash = self.hash_contract(contract_data)
            return content_hash, "0x" + "0" * 64, f"https://amoy.polygonscan.com/tx/0x{'0'*64}"

        content_hash = self.hash_contract(contract_data)
        hash_bytes = bytes.fromhex(content_hash)
        prev_bytes  = bytes.fromhex(previous_hash) if previous_hash else b"\x00" * 32

        # Encode contract_id as bytes32 (truncate UUID if needed)
        cid_bytes = contract_id.replace("-", "").encode()[:32].ljust(32, b"\x00")

        txn = self.contract.functions.record(
            hash_bytes, cid_bytes, prev_bytes
        ).build_transaction({
            "from":     self.account.address,
            "nonce":    self.w3.eth.get_transaction_count(self.account.address),
            "gas":      100_000,
            "gasPrice": self.w3.eth.gas_price,
        })

        signed  = self.account.sign_transaction(txn)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=30)

        tx_hash_hex = receipt.transactionHash.hex()
        scan_url = f"https://amoy.polygonscan.com/tx/{tx_hash_hex}"
        logger.info(f"Contract notarized: {scan_url}")
        return content_hash, tx_hash_hex, scan_url


polygon_notarizer = PolygonNotarizer()
