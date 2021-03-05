#!/usr/bin/env python3
import datetime
import maya
import os
import sys
from pathlib import Path

from web3.main import Web3

from nucypher.characters.lawful import Alice, Bob, Ursula
from nucypher.characters.lawful import Enrico as Enrico
from nucypher.config.constants import TEMPORARY_DOMAIN
from nucypher.utilities.ethereum import connect_web3_provider
from nucypher.crypto.powers import SigningPower, DecryptingPower
from nucypher.blockchain.eth.signers import Signer
from nucypher.utilities.logging import GlobalLoggerSettings


######################
# Boring setup stuff #
######################

# Twisted Logger
GlobalLoggerSettings.set_log_level(log_level_name='debug')
GlobalLoggerSettings.start_console_logging()

TESTNET = 'lynx'
PROVIDER_URI = "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
SEEDNODE_URI = "https://lynx.nucypher.network:9151"
# SIGNER_URI = 'clef://home/rhnvrm/.clef/clef.ipc'
SIGNER_URI = 'keystore:///home/rhnvrm/.ethereum/keystore/UTC--2021-03-08T16-08-28.795969228Z--c968123712e0fde083b12e408da2db9b5c6d0772'
wallet = Signer.from_signer_uri(SIGNER_URI)


ALICE_ADDRESS = "0xC968123712E0fDE083b12e408da2Db9b5c6d0772"
ALICE_PASSWORD = "nudroptesting"

##############################################
# Ursula, the Untrusted Re-Encryption Proxy  #
##############################################
ursula = Ursula.from_seed_and_stake_info(seed_uri=SEEDNODE_URI)

# Here are our Policy details.
policy_end_datetime = maya.now() + datetime.timedelta(days=1)
m, n = 2, 3


###########################
# NuDrop our dApp         #
# Acts as the sidechannel #
###########################

nudrop_db_bobs = {}
nudrop_db_alices = {}

# An abstracted filestore (such as IPFS)
nudrop_filestore = {}

#################################
# Bob (such as Wikileaks, WaPo) #
#################################

# First there was Bob.
bob = Bob(domain=TESTNET, provider_uri=PROVIDER_URI)

# Bob generates and gives his public keys to NuDrop.
verifying_key = bob.public_keys(SigningPower)
encrypting_key = bob.public_keys(DecryptingPower)

# Store it in the NuDrop db
nudrop_db_bobs["bob1"] = {
    "verifying_key": verifying_key,
    "encrypting_key": encrypting_key,
    "known_alices": []
}

######################################
# Alice, the Authority of the Policy #
# This can be a foundation like      #
# Freedom of Press foundation or     #
# even an actual journalist          #
######################################

# Connect to the ethereum provider.
connect_web3_provider(provider_uri=PROVIDER_URI)

wallet = Signer.from_signer_uri(SIGNER_URI)
password = ALICE_PASSWORD
wallet.unlock_account(account=ALICE_ADDRESS, password=password)

alice = Alice(checksum_address=ALICE_ADDRESS, signer=wallet, domain=TESTNET, provider_uri=PROVIDER_URI)

alice_verifying_key = bytes(alice.stamp)

# Alice can get the public key even before creating the policy.
# From this moment on, any Data Source that knows the public key
# can encrypt data originally intended for Alice, but that can be shared with
# any Bob that Alice grants access.

# Alice writes a label, maybe with a codename
label = b"my/secret/label/snowy_codename"

# This key is stored with Alice and can be shared with Enrico
policy_public_key = alice.get_policy_encrypting_key_from_label(label)

# Alice grant access to Bob. She already knows Bob's public keys from a side-channel.
# The sidechannel here is NuDrop. Alice selects an available bob, bob1 from NuDrop.

selected_bob = nudrop_db_bobs["bob1"]

remote_bob = Bob.from_public_keys(encrypting_key=selected_bob["encrypting_key"],
                                  verifying_key=selected_bob["verifying_key"])

expiration = maya.now() + datetime.timedelta(hours=1)
rate = Web3.toWei(50, 'gwei')
m, n = 2, 3
policy = alice.grant(remote_bob, label, m=m, n=n, rate=rate, expiration=policy_end_datetime)

assert policy.public_key == policy_public_key
policy.treasure_map_publisher.block_until_complete()

# Alice puts her public key on NuDrop for Bob to find later...
# Using NuDrop,
alice_verifying_key = bytes(alice.stamp)

nudrop_db_bobs["bob1"]["known_alices"].append(alice_verifying_key)
nudrop_db_alices[alice_verifying_key] = {
    "policy_public_key": policy_public_key,
    "label": label,
    "files": [],
}

# ...and then disappears from the internet.
#
# Note that local characters (alice and bob), as opposed to objects representing
# remote characters constructed from public data (remote_alice and remote_bob)
# run a learning loop in a background thread and need to be stopped explicitly.
alice.disenchant()
del alice

#########################
# Enrico, the Encryptor #
# This is the actual    #
# field journalist or   #
# whistleblower         #
#########################

# Enrico now can enter the Alice verifying key that was shared with him by Alice.
alice_data_for_enrico = nudrop_db_alices[alice_verifying_key]

enrico = Enrico(policy_encrypting_key=alice_data_for_enrico["policy_public_key"])
plaintext = b"Extremely sensitive information."
ciphertext, _signature = enrico.encrypt_message(plaintext)

# Enrico now adds it to NuDrop
# Let's create a new file in the data store abstraction
fname = "dummy_super_random_file_name"
nudrop_filestore[fname] = ciphertext

# Add it to the list of files registered for this Alice verifying key.
nudrop_db_alices[alice_verifying_key]["files"].append(fname)

del enrico



#####################
# some time passes. #
# ...               #
#                   #
# ...               #
# And now for Bob.  #
#####################

#####################
# Bob               #
#     who is meant  #
#     to receive    #
#     the data      #
# Such as wikileaks #
#####################

# Bob1 looks up the Alice who have granted policies for Bob for NuDrop
bob1_data = nudrop_db_bobs["bob1"]

selected_alice_verifying_key = nudrop_db_bobs["bob1"]["known_alices"][0]
selected_alice_data = nudrop_db_alices[selected_alice_verifying_key]

bob.join_policy(selected_alice_data["label"], selected_alice_verifying_key)

# Now Bob can retrieve the original message.
# Bob fetches one of the encrypted file.
selected_file_name = selected_alice_data["files"][0]
fetched_ciphertext = nudrop_filestore[selected_file_name]


delivered_cleartexts = bob.retrieve(fetched_ciphertext,
                                    policy_encrypting_key=policy_public_key,
                                    alice_verifying_key=alice_verifying_key,
                                    label=label)

# We show that indeed this is the passage originally encrypted by Enrico.
print("Retrieved: {}".format(delivered_cleartexts[0]))
assert plaintext == delivered_cleartexts[0]

bob.disenchant()
