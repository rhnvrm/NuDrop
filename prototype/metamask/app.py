import binascii
import datetime
import json
import time
from typing import List
from uuid import uuid4

import flask
import flask_socketio
import maya
import redis
import rlp
from eth_account._utils.transactions import Transaction, assert_valid_fields
from eth_utils.address import is_address, to_checksum_address
from eth_utils.applicators import apply_formatters_to_dict
from eth_utils.conversions import to_int
from flask import Flask, current_app, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from hexbytes.main import HexBytes
from nucypher.blockchain.eth.constants import NULL_ADDRESS
from nucypher.blockchain.eth.decorators import validate_checksum_address
from nucypher.blockchain.eth.interfaces import BlockchainInterfaceFactory
from nucypher.blockchain.eth.signers import Signer
from nucypher.characters.lawful import Alice, Bob, Enrico, Ursula
from nucypher.utilities.ethereum import connect_web3_provider
from nucypher.utilities.logging import GlobalLoggerSettings
from web3.main import Web3

GlobalLoggerSettings.start_console_logging()
GlobalLoggerSettings.set_log_level('debug')


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='%%',
        variable_end_string='%%',
        comment_start_string='<#',
        comment_end_string='#>',
    ))


app = CustomFlask(__name__, template_folder=".")
cors = CORS(app)
socketio = SocketIO(app, logger=True, engineio_logger=True,
                    cors_allowed_origins='*', ping_timeout=60000)
rdb = redis.Redis()


def sign_transaction_cb(sid, message):
    print("YOLO TX", message)
    ev = "sign_transaction"
    socketio.emit(ev, message, room=sid)

    p = rdb.pubsub(ignore_subscribe_messages=True)
    p.subscribe("sign_tx:"+sid)

    print("WAITING FOR MESSAGE")
    message, data = None, None
    timeout = 200
    stop_time = time.time() + timeout

    # https://stackoverflow.com/questions/7875008/how-to-implement-rediss-pubsub-timeout-feature
    while time.time() < stop_time:
        message = p.get_message(timeout=stop_time - time.time())
        if message:
            break

    print("YOLO MESSAGE", message)
    txhash = message["data"]
    return txhash


def sign_message_cb(sid, message):
    print("YOLO MSG", message)
    ev = "sign_message"
    socketio.emit(ev, message, room=sid)

    p = rdb.pubsub(ignore_subscribe_messages=True)
    p.subscribe("sign_msg:"+sid)

    print("WAITING FOR MESSAGE")
    message, data = None, None
    timeout = 200
    stop_time = time.time() + timeout

    # https://stackoverflow.com/questions/7875008/how-to-implement-rediss-pubsub-timeout-feature
    while time.time() < stop_time:
        message = p.get_message(timeout=stop_time - time.time())
        if message:
            break

    print("YOLO MESSAGE", message)
    sig = message["data"]
    return sig


class MetaMask(Signer):
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

        # Workaround for contract creation TXs
        if transaction_dict['to'] == b'':
            transaction_dict['to'] = None
        elif transaction_dict['to']:
            formatters['to'] = to_checksum_address
        formatted_transaction = apply_formatters_to_dict(
            formatters, transaction_dict)
        print("formatted_tx", formatted_transaction)
        txData = self.sign_transaction_cb(self.sid, formatted_transaction)
        print("MYTXHASH", txData)

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
        print("MYSIGN", signature)
        return HexBytes(signature.decode())


TESTNET = 'lynx'
SEEDNODE_URI = "https://lynx.nucypher.network:9151"
PROVIDER_URI = "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
# PROVIDER_URI = "https://eth-goerli.alchemyapi.io/v2/N_84Pr8pjQPI7QK0zFxJFJQ6-Vlue6gQ"

BlockchainInterfaceFactory.initialize_interface(provider_uri=PROVIDER_URI)


# def newU():
#     return Ursula.from_seed_and_stake_info(seed_uri=SEEDNODE_URI)


# ursulas = [newU()]


@socketio.on('on_load')
def handle_message(data):
    emit("prompt_login", {
        "socket_id": request.sid
    })


@socketio.on('signtx_resp')
def handle_message(data):
    print("RECV", data)
    p = rdb.publish("sign_tx:"+data["sid"], data["resp"])

@socketio.on('signmsg_resp')
def handle_message(data):
    print("RECV", data)
    p = rdb.publish("sign_msg:"+data["sid"], data["resp"])


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/api/prototype", methods=["POST"])
def prototype():
    data = request.get_json()
    address = Web3.toChecksumAddress(data["alice_address"])
    signer = MetaMask(sid=data["socket_id"], sign_message_cb=sign_message_cb,
                      sign_transaction_cb=sign_transaction_cb)

    alice = Alice(checksum_address=address,
                  signer=signer, domain=TESTNET, provider_uri=PROVIDER_URI)
    bob = Bob(checksum_address=address,
              signer=signer, domain=TESTNET, provider_uri=PROVIDER_URI)
    alice_verifying_key = bytes(alice.stamp)
    label = b"my/secret/label/nudrop/test"
    expiration = maya.now() + datetime.timedelta(days=1)
    rate = Web3.toWei(50, 'gwei')
    m, n = 1, 1
    policy = alice.grant(bob, label, m=m, n=n, rate=rate,
                         expiration=expiration)
    policy.treasure_map_publisher.block_until_complete()
    enrico = Enrico(policy_encrypting_key=policy.public_key)
    plaintext = b"Extremely sensitive information."
    ciphertext, _signature = enrico.encrypt_message(plaintext)
    bob.join_policy(label, bytes(alice.stamp))
    delivered_cleartexts = bob.retrieve(ciphertext,
                                        policy_encrypting_key=policy.public_key,
                                        alice_verifying_key=alice_verifying_key,
                                        label=label,
                                        treasure_map=policy.treasure_map)
    print(delivered_cleartexts)
    return {"status": "success", "data": delivered_cleartexts[0].decode()}


if __name__ == '__main__':
    socketio.run(app,
                 host='127.0.0.1',
                 port='5000',
                 )
