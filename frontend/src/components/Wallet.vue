<template>
  <div class="section">
    <h1 class="title">My Wallet</h1>
    
    <div v-if="privateKey == 'not available'">
    <b-message 
      v-if="privateKey === 'not available'" 
      type="is-danger">
      You have not set up your private key in the NuCypher Wallet. Please enter
      your private key below.
    </b-message>
    <b-field label="Private Key">
      <b-input 
        v-model="privateKey" 
        placeholder="My Private Key" 
        >
      </b-input>
    </b-field>
    </div>
    <div v-if="privateKey !== 'not available'">
      <b-field label="Private Key">
        <b-input 
          type="password" 
          v-model="privateKey" 
          placeholder="My Private Key" 
          password-reveal>
        </b-input>
      </b-field>

      <b-field label="Public Key">
        <b-input readonly v-model="checksumAddress" placeholder="My Private Key"></b-input>
      </b-field>

      <b-field label="Nucypher Passphrase">
        <b-input 
          type="password" 
          v-model="nuPassphrase" 
          placeholder="enter your passphrase to reveal umbral keys"
          v-on:blur="generateNucypherKeyring"></b-input>
      </b-field>

      <div v-if="pub_sig_key !== 'not available'">
        <b-field label="Umbral Sig Key">
          <b-input readonly v-model="pub_sig_key" placeholder="My Private Key"></b-input>
        </b-field>

        <b-field label="Umbral Enc Key">
          <b-input readonly v-model="pub_enc_key" placeholder="My Private Key"></b-input>
        </b-field>

        <b-field grouped label="Your Pseudonym">
            <b-input v-model="pseudonym" placeholder="" expanded></b-input>
            <p class="control">
                <b-button @click="generateNewName" v-if="pseudonym===''" label="Generate" type="is-primary" />
            </p>
        </b-field>

        <div v-if="pseudonym!==''">
          <b-message type="is-info" has-icon>
            You can share your key publicly so that others can share docs with you.

            People trying to share files can find your umbral keys for <b>7 days</b>.
          </b-message>
          <div class="buttons">
            <b-button @click="shareUmbralKeys" type="is-primary" expanded
              >Share Umbral Keys</b-button
            >
          </div>
        </div> 
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import querystring from "querystring";
import Web3 from "web3";
import PrivateKeyProvider from "truffle-privatekey-provider";
import generator from "name-creator";

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
          this.pub_enc_key = response.data.pub_enc_key
          this.pub_sig_key = response.data.pub_sig_key
        }).catch((err) => {
          this.$buefy.toast.open({
              duration: 5000,
              message: err,
              position: 'is-bottom',
              type: 'is-danger'
          }) 
        })
    },
    shareUmbralKeys: function () {
      const payload = {
          checksum_address: this.checksumAddress,
          password: this.nuPassphrase, 
          name: this.pseudonym,
      };

      axios
        .post("/api/v1/me/share/public", querystring.stringify(payload))
        .then((response) => {
          if (response.status == 200) {
            this.$buefy.toast.open({
                duration: 5000,
                message: "Share was successful",
                position: 'is-bottom',
                type: 'is-success'
            }) 
          }
        }).catch((err) => {
          this.$buefy.toast.open({
              duration: 5000,
              message: err,
              position: 'is-bottom',
              type: 'is-danger'
          }) 
        })
    },
    generateNewName: function() {
      this.pseudonym = generator.generate({ words: 4, number: true }).dashed; 
    }
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
    pseudonym: {
      get() {
        return this.$store.state.pseudonym;
      },
      set(value) {
        this.$store.commit("set_pseudonym", value);
      },
    },
  },
};
</script>
