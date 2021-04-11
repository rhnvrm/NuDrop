

import time
from typing import List

from eth_utils.address import to_checksum_address
from eth_utils.applicators import apply_formatters_to_dict
from hexbytes.main import HexBytes
from nucypher.blockchain.eth.constants import NULL_ADDRESS
from nucypher.blockchain.eth.decorators import validate_checksum_address
from nucypher.blockchain.eth.signers import Signer
from web3.main import Web3

class PrivateSocketIOSigner(Signer):
    SIGN_DATA_FOR_VALIDATOR = 'data/validator'
    SIGN_DATA_FOR_CLIQUE = 'application/clique'
    SIGN_DATA_FOR_ECRECOVER = 'text/plain'
    DEFAULT_CONTENT_TYPE = SIGN_DATA_FOR_ECRECOVER

    def __init__(self, testnet: bool = False, sid=None, sign_message_cb=None, sign_transaction_cb=None):
        super().__init__()
        self.sid = sid
        self.sign_message_cb = sign_message_cb
        self.sign_transaction_cb = sign_transaction_cb
        self.testnet = testnet

    @classmethod
    def uri_scheme(cls) -> str:
        return NotImplemented

    @property
    def accounts(self) -> List[str]:
        return NotImplemented

    @validate_checksum_address
    def is_device(self, account: str):
        return NotImplemented

    @validate_checksum_address
    def unlock_account(self, account: str, password: str, duration: int = None) -> bool:
        return NotImplemented

    @validate_checksum_address
    def lock_account(self, account: str) -> bool:
        return NotImplemented

    @validate_checksum_address
    def sign_transaction(self, transaction_dict: dict) -> str:
        formatters = {
            'nonce': Web3.toHex,
            'gasPrice': Web3.toHex,
            'gas': Web3.toHex,
            'value': Web3.toHex,
            'chainId': Web3.toHex,
            'from': to_checksum_address
        }

        if transaction_dict['to'] == b'':
            transaction_dict['to'] = None
        elif transaction_dict['to']:
            formatters['to'] = to_checksum_address
        formatted_transaction = apply_formatters_to_dict(
            formatters, transaction_dict)

        txData = self.sign_transaction_cb(self.sid, formatted_transaction)

        return txData.decode()

    @validate_checksum_address
    def sign_message(self, account: str, message: bytes, content_type: str = None, validator_address: str = None, **kwargs) -> HexBytes:
        if isinstance(message, bytes):
            message = Web3.toHex(message)

        if not content_type:
            content_type = self.DEFAULT_CONTENT_TYPE
        elif content_type not in self.SIGN_DATA_CONTENT_TYPES:
            raise ValueError(f'{content_type} is not a valid content type. '
                             f'Valid types are {self.SIGN_DATA_CONTENT_TYPES}')
        if content_type == self.SIGN_DATA_FOR_VALIDATOR:
            if not validator_address or validator_address == NULL_ADDRESS:
                raise ValueError(
                    'When using the intended validator type, a validator address is required.')
            data = {'address': validator_address, 'message': message}
        elif content_type == self.SIGN_DATA_FOR_ECRECOVER:
            data = {'address': account, 'message': message}
        else:
            raise NotImplementedError

        signature = self.sign_message_cb(self.sid, data)

        return HexBytes(signature.decode())

