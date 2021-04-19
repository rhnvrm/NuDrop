<template>
  <div class="section">
    <h1 class="title">My Wallet</h1>
    <b-field label="Private Key">
      <b-input v-model="privateKey" placeholder="My Private Key"></b-input>
    </b-field>

    <b-field label="Nucypher Passphrase">
      <b-input 
        v-model="nuPassphrase" 
        placeholder="passphrase"
        v-on:blur="generateNucypherKeyring"></b-input>
    </b-field>

    <b-field label="Public Key">
      <b-input readonly v-model="checksumAddress" placeholder="My Private Key"></b-input>
    </b-field>

    <b-field label="Umbral Sig Key">
      <b-input readonly v-model="pub_sig_key" placeholder="My Private Key"></b-input>
    </b-field>

    <b-field label="Umbral Enc Key">
      <b-input readonly v-model="pub_enc_key" placeholder="My Private Key"></b-input>
    </b-field>
  </div>
</template>

<script>
import axios from "axios";
import querystring from "querystring";
import Web3 from "web3";
import PrivateKeyProvider from "truffle-privatekey-provider";

export default {
  data: function () {
    return {
        web3: "not available",
        checksumAddress: "not available",
        pub_enc_key: "not available",
        pub_sig_key: "not available",
        nuPassphrase: "",
    };
  },
  mounted() {
          var provider = new PrivateKeyProvider(
      this.$store.state.private_key,
      "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
    );

    var web3 = new Web3(provider);
    this.web3 = web3;
    this.checksumAddress = this.web3.eth.accounts.wallet._accounts.currentProvider.address 
  },
  methods: {
    generateNucypherKeyring: function () {
      const payload = {
          checksum_address: this.checksumAddress,
          password: this.nuPassphrase, 
      };

      axios
        .post("/api/v1/me", querystring.stringify(payload))
        .then((response) => {
          console.log(response)
          this.pub_enc_key = response.data.pub_enc_key
          this.pub_sig_key = response.data.pub_sig_key
        });
    },
  },
  computed: {
    privateKey: {
      get() {
        return this.$store.state.private_key;
      },
      set(value) {
        this.$store.commit("set_private_key", value);
      },
    },
  },
};
</script>
