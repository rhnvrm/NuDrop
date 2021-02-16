#!/usr/bin/env python3
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


######################
# Boring setup stuff #
######################

# Twisted Logger
GlobalLoggerSettings.set_log_level(log_level_name='debug')
GlobalLoggerSettings.start_console_logging()

# Start federated ursula using:
# python ../nucypher/examples/run_demo_ursula_fleet.py`
# if your ursulas are NOT running on your current host,
# run like this: python finnegans-wake-demo.py 172.28.1.3:11500
# otherwise the default will be fine.

try:
    SEEDNODE_URI = sys.argv[1]
except IndexError:
    SEEDNODE_URI = "localhost:11500"

##############################################
# Ursula, the Untrusted Re-Encryption Proxy  #
##############################################
ursula = Ursula.from_seed_and_stake_info(seed_uri=SEEDNODE_URI, federated_only=True)

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
bob = Bob(federated_only=True, domain=TEMPORARY_DOMAIN, known_nodes=[ursula])

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

alice = Alice(federated_only=True, domain=TEMPORARY_DOMAIN, known_nodes=[ursula])


# Start node discovery and wait until 8 nodes are known in case
# the fleet isn't fully spun up yet, as sometimes happens on CI.
alice.start_learning_loop(now=True)
alice.block_until_number_of_known_nodes_is(8, timeout=30, learn_on_this_thread=True)

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
policy = alice.grant(remote_bob, label, m=m, n=n, expiration=policy_end_datetime)

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
