from typing import List

from eth_utils.address import is_address, to_checksum_address
from eth_utils.applicators import apply_formatters_to_dict
from flask import Flask, render_template
from flask_cors import CORS
import flask_socketio
from flask_socketio import SocketIO, emit
from hexbytes.main import HexBytes
from nucypher.blockchain.eth.constants import NULL_ADDRESS
from nucypher.blockchain.eth.decorators import validate_checksum_address
from nucypher.blockchain.eth.signers import Signer
from nucypher.utilities.logging import GlobalLoggerSettings
from web3.main import Web3
import flask
from uuid import uuid4
from flask import request, current_app

app = Flask(__name__, template_folder=".")
cors = CORS(app)
socketio = SocketIO(app, logger=True, engineio_logger=True, cors_allowed_origins='*', ping_timeout=60000)

class NuDropException(Exception):
    pass

def sign_callback(sign_type, message_dict):
    print(sign_type, message_dict)
    return None

class MetaMask(Signer):
    SIGN_DATA_FOR_VALIDATOR = 'data/validator'
    SIGN_DATA_FOR_CLIQUE = 'application/clique'
    SIGN_DATA_FOR_ECRECOVER = 'text/plain'
    DEFAULT_CONTENT_TYPE = SIGN_DATA_FOR_ECRECOVER

    def __init__(self, testnet: bool = False, sign_callback=None):
        super().__init__()
        self.sign_callback = sign_callback
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

        # Workaround for contract creation TXs
        if transaction_dict['to'] == b'':
            transaction_dict['to'] = None
        elif transaction_dict['to']:
            formatters['to'] = to_checksum_address
        formatted_transaction = apply_formatters_to_dict(formatters, transaction_dict)
        txHash = self.sign_callback('transaction', formatted_transaction)
        print(txHash)
        return txHash

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
                raise ValueError('When using the intended validator type, a validator address is required.')
            data = {'address': validator_address, 'message': message}
        elif content_type == self.SIGN_DATA_FOR_ECRECOVER:
            data = {'address': account, 'message': message}
        else:
            raise NotImplementedError
        signature = self.sign_callback('message', data)
        print(signature)
        return HexBytes(signature)

@socketio.on('on_load')
def handle_message(data):
    emit("prompt_login")

@app.route("/", methods=["GET"])
def home():
    print("hi")
    signer = MetaMask(testnet=True, sign_callback=sign_callback)
    return render_template("index.html")

if __name__ == '__main__':
    GlobalLoggerSettings.start_console_logging()
    GlobalLoggerSettings.set_log_level('debug')

    socketio.run(app,
                 host='127.0.0.1',
                 port='5000',
                 )
