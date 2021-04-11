from .sockets import ConnectionManager
import datetime
import time
import maya
from nucypher.crypto.powers import DecryptingPower, SigningPower

import redis
from umbral.keys import UmbralPrivateKey
import uvicorn
from eth_typing.evm import ChecksumAddress
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi_socketio import SocketManager
from nucypher.characters.lawful import Alice, Bob, Enrico, Ursula
from web3.main import Web3

from .config import settings
from .signer import PrivateSocketIOSigner

app = FastAPI(
    docs_url="/api/docs", redoc_url="/api/redocs", openapi_url="/api/openapi.json"
)

# SocketManager(app=app, mount_location="/api/ws/")

# import ipdb; ipdb.set_trace()

rdb = redis.Redis()
manager = ConnectionManager()


@app.get("/api")
async def read_root():
    # import ipdb

    # ipdb.set_trace()
    return {settings.app_name: "Hello World"}


@app.get("/api/v1/bob")
async def get_bob_list():
    list_of_bobs = [x.decode("utf-8") for x in rdb.smembers("db:bobs")]
    return {
        "bobs": list_of_bobs,
    }


@app.get("/api/v1/bob/{name}")
async def get_bob_list(name: str):
    bob = rdb.hgetall("db:bobs:" + name)
    return bob


@app.post("/api/v1/bob")
async def register_bob(
    name: str,
    checksum_address: str,
):
    bob_name = name

    bob = Bob(
        checksum_address=checksum_address,
        domain=settings.nucypher_network,
        provider_uri=settings.provider_uri,
    )

    pub_enc_key = bob.public_keys(DecryptingPower)
    pub_sig_key = bob.public_keys(SigningPower)

    # Store it in the NuDrop db
    data = {
        "name": bob_name,
        "enc_key": "0x" + pub_enc_key.hex(),
        "sig_key": "0x" + pub_sig_key.hex(),
    }

    rdb.hmset("db:bobs:" + bob_name, data)
    rdb.sadd("db:bobs", bob_name)

    return data


@app.post("/api/v1/policy/create")
async def create_policy(
    alice_address: str,
    socket_id: str,
    bob_enc_key: str,
    bob_sig_key: str,
    expiry_days: int,
    code_name: str,
):
    address = Web3.toChecksumAddress(alice_address)
    signer = PrivateSocketIOSigner(
        sid=socket_id,
        sign_message_cb=sign_message_cb,
        sign_transaction_cb=sign_transaction_cb,
    )

    alice = Alice(
        checksum_address=address,
        signer=signer,
        domain=settings.nucypher_network,
        provider_uri=settings.provider_uri,
    )

    remote_bob = Bob.from_public_keys(
        encrypting_key=bytes.fromhex(bob_enc_key),
        verifying_key=bytes.fromhex(bob_sig_key),
    )

    label = bytes("nudrop/" + code_name, "utf-8")

    policy_public_key = alice.get_policy_encrypting_key_from_label(label)

    policy_end_datetime = maya.now() + datetime.timedelta(days=expiry_days)
    m, n = 2, 3

    policy = alice.grant(remote_bob, label, m=m, n=n, expiration=policy_end_datetime)

    policy.treasure_map_publisher.block_until_complete()

    alice_verifying_key = bytes(alice.stamp)

    alice.disenchant()
    del alice

    return {
        "verifying_key": alice_verifying_key.hex(),
        "policy_public_key": policy_public_key.hex(),
        "label": label.decode("utf-8"),
    }


def sign_transaction_cb(sid, message):
    ev = "sign_transaction"
    app.sio.emit(ev, message, room=sid)

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
    app.sio.emit(ev, message, room=sid)

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
                await manager.send_personal_data({
                    "kind":"prompt_login"
                }, websocket)
            elif data["kind"] == "signtx_resp":
                p = rdb.publish("sign_tx:" + data["sid"], data["resp"])
            elif data["kind"] == "signmsg_resp":
                pass
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     print('Accepting client connection...')
#     await websocket.accept()
#     while True:
#         try:
#             # Wait for any message from the client
#             data = await websocket.receive_json()
#             # Send message to the client
#             if data == "on_load":
#                 await websocket.send_json({
#                     "kind": "message",
#                     "message": "prompt_login"
#                 })
#             elif data == "signtx_resp":
#                 await websocket.send_json({
#                     "kind": "message",
#                     "message": ""
#                 })
#             elif data == "signmsg_resp":
#                 pass

# # @app.sio.on("on_load")
# # async def handle_message(sid, *args, **kwargs):
# #     print("here!!")
# #     await app.sio.emit("prompt_login", {"socket_id": sid})


# # @app.sio.on("signtx_resp")
# # def handle_message(sid, *args, **kwargs):
# #     print("RECV", kwargs)
# #     p = rdb.publish("sign_tx:" + kwargs["sid"], kwargs["resp"])


# @app.sio.on("signmsg_resp")
# def handle_message(sid, *args, **kwargs):
#     print("RECV", kwargs)
#     p = rdb.publish("sign_msg:" + kwargs["sid"], kwargs["resp"])


# resp = {'value': random.uniform(0, 1)}
# await websocket.send_json(resp)
#     except Exception as e:
#         print('error:', e)
#         break
# print('Bye..')


async def main():
    uvicorn.run(
        "nudrop.app:app", host="0.0.0.0", port=8000, reload=True, debug=True, workers=3
    )
