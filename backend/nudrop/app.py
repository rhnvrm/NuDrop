import asyncio
import datetime
import time

import maya
from nucypher.crypto.kits import UmbralMessageKit
import redis
import uvicorn
from asgiref.sync import async_to_sync
from eth_typing.evm import ChecksumAddress
from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi_socketio import SocketManager
from nucypher.blockchain.eth.interfaces import BlockchainInterfaceFactory
from nucypher.characters.lawful import Alice, Bob, Enrico, Ursula
from nucypher.config.constants import TEMPORARY_DOMAIN
from nucypher.config.keyring import ExistingKeyringError, NucypherKeyring
from nucypher.crypto.powers import DecryptingPower, SigningPower
from nucypher.policy.collections import SignedTreasureMap
from nucypher.utilities.logging import GlobalLoggerSettings
from umbral.keys import UmbralPrivateKey, UmbralPublicKey
from web3.main import Web3

from .config import settings
from .signer import WebsocketSigner
from .sockets import ConnectionManager

# Twisted Logger
GlobalLoggerSettings.set_log_level(log_level_name="debug")
GlobalLoggerSettings.start_console_logging()

BlockchainInterfaceFactory.initialize_interface(provider_uri=settings.provider_uri)

app = FastAPI(
    docs_url="/api/docs", redoc_url="/api/redocs", openapi_url="/api/openapi.json"
)

rdb = redis.Redis()

manager = ConnectionManager()


@app.get("/api")
async def read_root():
    return {settings.app_name: "Hello World"}


def get_keyring(checksum_address, password):
    try:
        keyring = NucypherKeyring.generate(
            checksum_address=checksum_address, password=password
        )
        keyring.unlock(password)
        return keyring
    except ExistingKeyringError:
        keyring = NucypherKeyring(account=checksum_address)
        keyring.unlock(password)

        return keyring

@app.post("/api/v1/me")
def about_me(
    checksum_address: str = Form(...),
    password: str = Form(...),
):
    keyring = get_keyring(Web3.toChecksumAddress(checksum_address), password)

    data = {
        "pub_enc_key": keyring.encrypting_public_key.hex(),
        "pub_sig_key": keyring.signing_public_key.hex(),
    }

    keyring.lock()

    return data

@app.post("/api/v1/me/share/public")
def share_public(
    checksum_address: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
):
    keyring = get_keyring(Web3.toChecksumAddress(checksum_address), password)

    data = {
        "pub_enc_key": keyring.encrypting_public_key.hex(),
        "pub_sig_key": keyring.signing_public_key.hex(),
    }

    keyring.lock()

    rdb.hmset("bob:"+name, data)
    rdb.expire("bob:"+name, 604800)
    return True


@app.get("/api/v1/public/bobs")
def get_public_bobs():
    bobs = rdb.keys("bob:*")
    return {
        "bobs": [ x[4:] for x in bobs ]
    }

@app.get("/api/v1/public/bobs/{bob_id}")
def get_public_bob(bob_id: str):
    bob = rdb.hgetall("bob:"+bob_id)
    return {
        "data": bob,
    }
@app.post("/api/v1/enrico/encrypt")
def encrypt_file(
    policy_pub_key: str = Form(...),
    plaintext: str = Form(...),
):
    key = UmbralPublicKey.from_hex(policy_pub_key)
    enrico = Enrico(policy_encrypting_key=key)
    plaintext = plaintext.encode("utf-8")
    ciphertext, _signature = enrico.encrypt_message(plaintext)
    return {
        "ciphertext": ciphertext.to_bytes().hex(),
    }


@app.post("/api/v1/bob/decrypt")
def decrypt_data(
    bob_address: str = Form(...),
    bob_password: str = Form(...),
    policy_pub_key: str = Form(...),
    alice_verifying_key: str = Form(...),
    label: str = Form(...),
    ciphertext: str = Form(...),
    tmap_bytes: str = Form(...),
):
    signer = WebsocketSigner(
        sid=0,
        sign_message_cb=sign_message_cb,
        sign_transaction_cb=sign_transaction_cb,
    )

    keyring = get_keyring(Web3.toChecksumAddress(bob_address), bob_password)

    bob = Bob(
        keyring=keyring,
        signer=signer,
        domain=settings.nucypher_network,
        provider_uri=settings.provider_uri,
    )

    signed_tmap = SignedTreasureMap.from_bytes(bytes.fromhex(tmap_bytes))

    delivered_cleartexts = bob.retrieve(
        UmbralMessageKit.from_bytes(bytes.fromhex(ciphertext)),
        policy_encrypting_key=UmbralPublicKey.from_hex(policy_pub_key),
        alice_verifying_key=UmbralPublicKey.from_hex(alice_verifying_key),
        label=label,
        treasure_map=signed_tmap,
    )

    return {"cleartext": delivered_cleartexts}


@app.post("/api/v1/policy/create")
def create_policy(
    alice_address: str = Form(...),
    alice_password: str = Form(...),
    socket_id: str = Form(...),
    bob_enc_key: str = Form(...),
    bob_sig_key: str = Form(...),
    expiry_days: int = Form(...),
    code_name: str = Form(...),
):
    address = Web3.toChecksumAddress(alice_address)
    signer = WebsocketSigner(
        sid=socket_id,
        sign_message_cb=sign_message_cb,
        sign_transaction_cb=sign_transaction_cb,
    )

    keyring = get_keyring(address, alice_password)

    alice = Alice(
        keyring=keyring,
        signer=signer,
        domain=settings.nucypher_network,
        provider_uri=settings.provider_uri,
    )

    alice.start_learning_loop(now=True)

    remote_bob = Bob.from_public_keys(
        encrypting_key=UmbralPublicKey.from_hex(bob_enc_key),
        verifying_key=UmbralPublicKey.from_hex(bob_sig_key),
    )

    label = bytes("nudrop/" + code_name, "utf-8")

    policy_public_key = alice.get_policy_encrypting_key_from_label(label)

    policy_end_datetime = maya.now() + datetime.timedelta(days=expiry_days)
    m, n = 2, 3
    rate = Web3.toWei(50, "gwei")

    seed_uri = "https://lynx.nucypher.network:9151"
    ursula = Ursula.from_seed_and_stake_info(seed_uri=seed_uri)
    policy = alice.grant(
        remote_bob,
        label,
        rate=rate,
        m=m,
        n=n,
        expiration=policy_end_datetime,
        handpicked_ursulas=[ursula],
    )

    policy.treasure_map_publisher.block_until_complete()

    alice_verifying_key = bytes(alice.stamp)

    alice.disenchant()
    del alice
    return {
        "verifying_key": alice_verifying_key.hex(),
        "policy_public_key": policy_public_key.hex(),
        "label": label.decode("utf-8"),
        "tmap_bytes": bytes(policy.treasure_map).hex(),
    }


def sign_transaction_cb(sid, message):
    ev = "sign_transaction"
    ws = manager.active_connections[sid]
    manager.add_task({"task": {"kind": ev, "data": message}, "ws": ws})

    p = rdb.pubsub(ignore_subscribe_messages=True)
    p.subscribe("sign_tx:" + sid)

    message, data = None, None
    timeout = 200
    stop_time = time.time() + timeout

    # https://stackoverflow.com/questions/7875008/how-to-implement-rediss-pubsub-timeout-feature
    while time.time() < stop_time:
        message = p.get_message(timeout=stop_time - time.time())
        if message:
            break

    return message["data"]


def sign_message_cb(sid, message):
    ev = "sign_message"
    ws = manager.active_connections[sid]
    manager.add_task({"task": {"kind": ev, "data": message}, "ws": ws})

    p = rdb.pubsub(ignore_subscribe_messages=True)
    p.subscribe("sign_msg:" + sid)

    message, data = None, None
    timeout = 200
    stop_time = time.time() + timeout

    # https://stackoverflow.com/questions/7875008/how-to-implement-rediss-pubsub-timeout-feature
    while time.time() < stop_time:
        message = p.get_message(timeout=stop_time - time.time())
        if message:
            break

    return message["data"]


@app.websocket("/api/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["kind"] == "on_load":
                manager.register(data["sid"], websocket)
                await manager.send_personal_data({"kind": "prompt_login"}, websocket)
            elif data["kind"] == "signtx_resp":
                p = rdb.publish("sign_tx:" + str(data["sid"]), data["resp"])
            elif data["kind"] == "signmsg_resp":
                p = rdb.publish("sign_msg:" + str(data["sid"]), data["resp"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(manager.clear_tasks())


async def main():
    import os

    reload = True
    debug = True
    workers = 3

    if os.getenv("PRODUCTION"):
        reload = False
        debug = False
        workers = 30

    uvicorn.run(
        "nudrop.app:app",
        host="0.0.0.0",
        port=8000,
        reload=reload,
        debug=debug,
        workers=workers,
    )
