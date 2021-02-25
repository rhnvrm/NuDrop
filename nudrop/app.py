#!/usr/bin/env python3
from flask import Flask, render_template, request
import datetime
import maya
import os
import sys
from pathlib import Path

from nucypher.characters.lawful import Alice, Bob, Ursula
from nucypher.characters.lawful import Enrico as Enrico
from nucypher.config.constants import TEMPORARY_DOMAIN
from nucypher.crypto.powers import SigningPower, DecryptingPower
from nucypher.utilities.logging import GlobalLoggerSettings
from umbral.keys import UmbralPublicKey, UmbralPrivateKey

# Twisted Logger
GlobalLoggerSettings.set_log_level(log_level_name="debug")
GlobalLoggerSettings.start_console_logging()

# NuDrop Data
# TODO: setup actual db
nudrop_db_bobs = {}
nudrop_db_alices = {}
nudrop_filestore = {}

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
            "known_alices": [],
        }

        nudrop_db_bobs[bob_name] = data

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
        }

        return render_template("register_alice.html", data=data)
    else:
        return render_template("register_alice.html")


@app.route("/policy", methods=["POST", "GET"])
def manage_policy():
    if request.method == "POST":
        # TODO: work on making a form and get data from form
        alice = Alice(
            federated_only=True, domain=TEMPORARY_DOMAIN, known_nodes=[ursula]
        )
        alice.start_learning_loop(now=True)
        alice.block_until_number_of_known_nodes_is(
            8, timeout=30, learn_on_this_thread=True
        )

        label = b"my/secret/label/snowy_codename"

        policy_public_key = alice.get_policy_encrypting_key_from_label(label)

        selected_bob = nudrop_db_bobs["bob1"]

        remote_bob = Bob.from_public_keys(
            encrypting_key=selected_bob["enc_key"],
            verifying_key=selected_bob["sig_key"],
        )
        policy = alice.grant(
            remote_bob, label, m=m, n=n, expiration=policy_end_datetime
        )

        policy.treasure_map_publisher.block_until_complete()

        alice_verifying_key = bytes(alice.stamp)

        nudrop_db_bobs["bob1"]["known_alices"].append(alice_verifying_key)
        nudrop_db_alices[alice_verifying_key] = {
            "policy_public_key": policy_public_key,
            "label": label,
            "files": [],
        }

        alice.disenchant()
        del alice
    else:
        pass
