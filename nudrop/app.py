#!/usr/bin/env python3
from flask import Flask, render_template, request, flash, redirect
import datetime
import maya
import os
import sys
from pathlib import Path
import redis

from nucypher.characters.lawful import Alice, Bob, Ursula
from nucypher.config.characters import AliceConfiguration
from nucypher.characters.lawful import Enrico as Enrico
from nucypher.config.constants import TEMPORARY_DOMAIN
from nucypher.crypto.powers import SigningPower, DecryptingPower
from nucypher.crypto.keypairs import DecryptingKeypair, SigningKeypair
from nucypher.utilities.logging import GlobalLoggerSettings
from umbral.keys import UmbralPublicKey, UmbralPrivateKey

# Twisted Logger
GlobalLoggerSettings.set_log_level(log_level_name="debug")
GlobalLoggerSettings.start_console_logging()

# NuDrop Data
# TODO: setup actual db
# nudrop_db_bobs = {}
# nudrop_db_alices = {}
# nudrop_filestore = {}

rdb = redis.Redis()

# Ursula
SEEDNODE_URI = "localhost:11500"
ursula = Ursula.from_seed_and_stake_info(seed_uri=SEEDNODE_URI, federated_only=True)

# Flask
app = Flask(__name__, template_folder="tmpl")


@app.route("/register/bob", methods=["POST", "GET"])
def register_bob():
    if request.method == "POST":
        bob_name = request.form["name"]

        priv_enc_key = UmbralPrivateKey.gen_key()
        priv_sig_key = UmbralPrivateKey.gen_key()

        # Bob generates and gives his public keys to NuDrop.
        pub_enc_key = priv_enc_key.get_pubkey()
        pub_sig_key = priv_sig_key.get_pubkey()

        # Store it in the NuDrop db
        data = {
            "name": bob_name,
            "enc_key": pub_enc_key.hex(),
            "sig_key": pub_sig_key.hex(),
        }

        # nudrop_db_bobs[bob_name] = data
        rdb.hmset("db:bobs:" + bob_name, data)
        rdb.sadd("db:bobs", bob_name)

        tmpl_data = {
            "priv": {
                "enc_key": priv_enc_key.to_bytes().hex(),
                "sig_key": priv_sig_key.to_bytes().hex(),
            },
            "pub": data,
        }
        return render_template("register_bob.html", tmpl_data=tmpl_data)
    else:
        return render_template("register_bob.html")


@app.route("/register/alice", methods=["POST", "GET"])
def register_alice():
    if request.method == "POST":
        alice = Alice(
            federated_only=True, domain=TEMPORARY_DOMAIN, known_nodes=[ursula]
        )

        verifying_key = alice.public_keys(SigningPower)
        encrypting_key = alice.public_keys(DecryptingPower)

        data = {
            "verifying_key": verifying_key.hex(),
            "encrypting_key": encrypting_key.hex(),
            "checksum_address": alice.checksum_address,
        }

        return render_template("register_alice.html", data=data)
    else:
        return render_template("register_alice.html")


@app.route("/policy", methods=["POST", "GET"])
def manage_policy():
    if request.method == "POST":
        bob_name = request.form["bob"]
        code_name = request.form["codename"]
        checksum_address = request.form["checksum_address"]
        # passphrase = request.form["passphrase"]
        passphrase = "passwordpasswordpasswordpasswordpassword"

        bob_key = "db:bobs:" + bob_name
        selected_bob = rdb.hgetall(bob_key)

        # ipdb.set_trace()
        remote_bob = Bob.from_public_keys(
            encrypting_key=bytes.fromhex(selected_bob[b"enc_key"].decode("utf-8")),
            verifying_key=bytes.fromhex(selected_bob[b"sig_key"].decode("utf-8")),
        )

        policy_end_datetime = maya.now() + datetime.timedelta(days=1)
        m, n = 2, 3

        config_root = os.path.join("/", "tmp", "nucypher-alice-config")

        alice_config = AliceConfiguration(
            config_root=config_root,
            federated_only=True,
            domain=TEMPORARY_DOMAIN,
            known_nodes=[ursula],
            checksum_address=checksum_address,
        )

        alice_config.initialize(password=passphrase)
        alice_config.keyring.unlock(password=passphrase)
        alice = alice_config()
        alice.start_learning_loop(now=True)
        alice.block_until_number_of_known_nodes_is(
            8, timeout=30, learn_on_this_thread=True
        )

        label = bytes("nudrop/" + code_name, "utf-8")

        policy_public_key = alice.get_policy_encrypting_key_from_label(label)

        policy = alice.grant(
            remote_bob, label, m=m, n=n, expiration=policy_end_datetime
        )

        policy.treasure_map_publisher.block_until_complete()

        alice_verifying_key = bytes(alice.stamp)

        rdb.sadd("db:bob:" + bob_name, alice_verifying_key)
        # nudrop_db_bobs["bob1"]["known_alices"].append(alice_verifying_key)
        data = {
            "verifying_key": alice_verifying_key.hex(),
            "policy_public_key": policy_public_key.hex(),
            "label": label.decode("utf-8"),
        }

        rdb.hmset("db:alices:" + alice_verifying_key.hex(), data)

        alice.disenchant()
        del alice

        return render_template("policy.html", policy_data=data)
    else:
        list_of_bobs = [x.decode("utf-8") for x in rdb.smembers("db:bobs")]
        data = {
            "bobs": list_of_bobs,
        }
        return render_template("policy.html", data=data)


@app.route("/encrypt", methods=["POST", "GET"])
def encrypt():
    if request.method == "POST":
        alice_verifying_key = request.form["alice_verifying_key"]
        plaintext = request.form["plaintext_data"]

        alice_data_for_enrico = rdb.hgetall("db:alices:" + alice_verifying_key)

        policy_encrypting_key = bytes.fromhex(
            alice_data_for_enrico[b"policy_public_key"].decode("utf-8")
        )
        print(policy_encrypting_key)
        enrico = Enrico(
            policy_encrypting_key=UmbralPublicKey.from_bytes(policy_encrypting_key)
        )

        ciphertext, _signature = enrico.encrypt_message(bytes(plaintext, "utf-8"))
        # TODO: nudrop_db_alices[alice_verifying_key]["files"].append(fname)

        del enrico
        data = {"ciphertext": ciphertext.ciphertext.hex()}
        return render_template("encrypt.html", data=data)
    else:
        return render_template("encrypt.html")


@app.route("/decrypt", methods=["POST", "GET"])
def decrypt():
    if request.method == "GET":
        return render_template("decrypt.html")

    bob_data = rdb.hgetall("db:bobs:" + "rohan")

    # bob = Bob.from_public_keys(
    #     encrypting_key=UmbralPublicKey.from_bytes(
    #         bytes.fromhex(bob_data[b"enc_key"].decode("utf-8"))
    #     ),
    #     verifying_key=UmbralPublicKey.from_bytes(
    #         bytes.fromhex(bob_data[b"sig_key"].decode("utf-8"))
    #     ),
    # )
    # bob_enc_keypair = DecryptingKeypair(
    #     private_key=bob_data[b"enc_key"].decode("utf-8")
    # )
    # bob_sig_keypair = SigningKeypair(private_key=bob_data[b"sig_key"].decode("utf-8"))

    bob_enc_keypair = DecryptingKeypair(
        private_key=UmbralPrivateKey.from_bytes(
            bytes.fromhex(
                "870fbec26d9835214a6a5fd40864df41e7050952e268e31e91c180ac3d0164d9"
            )
        )
    )

    bob_sig_keypair = SigningKeypair(
        private_key=UmbralPrivateKey.from_bytes(
            bytes.fromhex(
                "44cdf8bda13c6b0b03bc53013d6401e68c366ee6d66efbe052e3793f5e6e96a3"
            )
        )
    )

    enc_power = DecryptingPower(keypair=bob_enc_keypair)
    sig_power = SigningPower(keypair=bob_sig_keypair)
    power_ups = [enc_power, sig_power]

    bob = Bob(
        domain=TEMPORARY_DOMAIN,
        federated_only=True,
        crypto_power_ups=power_ups,
        start_learning_now=True,
        abort_on_learning_error=True,
        known_nodes=[ursula],
        save_metadata=False,
    )

    bob.join_policy(
        bytes("nudrop/abc", "utf-8"),
        UmbralPublicKey.from_bytes(
            bytes.fromhex(
                "0298e9c3e104f9327f61186ca5d36c093f1988b2721a130b1c9ac367f9b4a54359"
            )
        ),
    )

    fetched_ciphertext = "e95c323dd12c2d64ddacdd3e77ad07f7b45b2add8ac7e99e328ca979993ffe036a0ae09a6bb85e9ffb18c0508cf1c6b4b967de0a7a79a2c130de058ffd6419852d0719734061c80eeb6e829a3e691e6d48d65e0a66d5b8edb0c5501ff928f5222c8a50ff3fda2404ce0db47b1d5d91"
    policy_public_key = (
        "027df7b52decec9425563cca5000261aa3bd1ae16aa7d8d47792985a235acde580"
    )
    alice_verifying_key = (
        "033078ad98dba310b4ef807ac5ba2d4f5e3481e8fd8954dce8baa028d5dde3bd4a"
    )
    label = "nudrop/codename"

    delivered_cleartexts = bob.retrieve(
        fetched_ciphertext,
        policy_encrypting_key=policy_public_key,
        alice_verifying_key=alice_verifying_key,
        label=label,
    )

    # We show that indeed this is the passage originally encrypted by Enrico.
    return "Retrieved: {}".format(delivered_cleartexts[0])

    bob.disenchant()


@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")
