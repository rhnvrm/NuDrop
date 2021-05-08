<template>
  <div class="section">
    <!-- Policy Create
    <div>User address: {{ user_address }}</div>
    <div>Socket address: {{ socket_id }}</div>

    <div>{{ api_response_data }}</div> -->

    <h1 class="title">Create Policy</h1>
    <b-field label="Code Name">
      <b-input v-model="codename" placeholder="Codename for label"></b-input>
    </b-field>
    <b-field label="Days">
      <b-numberinput min="1" v-model="expiry_days"></b-numberinput>
    </b-field>
    <b-field label="Find a Receiver">
      <b-autocomplete
          :data="bobs"
          placeholder="noble-mansion-cold-symptom"
          icon="magnify"
          clearable
          @select="option => setBob(option)">
          <template #empty>No results found</template>
      </b-autocomplete>
    </b-field>
    <b-field label="Receiver Encrypting Public Key">
      <b-input v-model="rec_enc_key" placeholder="023..."></b-input>
    </b-field>
    <b-field label="Receiver Signing Public Key">
      <b-input v-model="rec_sig_key" placeholder="037..."></b-input>
    </b-field>
    <b-field label="Nucypher Passphrase">
      <b-input 
        v-model="nuPassphrase" 
        placeholder="passphrase"></b-input>
    </b-field>
    <b-button v-on:click="createPolicy" type="is-primary" expanded
      >Create policy</b-button
    >
  </div>
</template>

<script>
import Web3 from "web3";
import PrivateKeyProvider from "truffle-privatekey-provider";
import axios from "axios";
import querystring from "querystring";
export default {
  async mounted() {
    if (this.$store.state.private_key == "not available") {
      this.$router.push("/me/wallet");
    }

    var provider = new PrivateKeyProvider(
      this.$store.state.private_key,
      "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
    );

    var web3 = new Web3(provider);
    this.web3 = web3;

    var client_id = Date.now();
    // TODO: make this uri configurable
    var wsprotocol = "" 
    if (window.location.hostname === 'localhost') {
      wsprotocol = "ws"
    } else {
      wsprotocol = "wss"
    }
    var ws = new WebSocket(wsprotocol+`://`+window.location.hostname+`/api/ws/${client_id}`);
    ws.onmessage = (event) => {
      const ev = JSON.parse(event.data);
      var data = ev.data;
      switch (ev.kind) {
        case "prompt_login":
          this.user_address =
            web3.eth.accounts.wallet._accounts.currentProvider.address;
          this.socket_id = client_id;
          break;
        case "sign_transaction":
          this.signTx(ws, data);
          break;

        case "sign_message":
          this.signMsg(ws, data);
          break;
      }
    };

    ws.onopen = () =>
      ws.send(
        JSON.stringify({
          kind: "on_load",
          sid: client_id,
        })
      );

    this.fetchBobs() 
  },
  data: function () {
    return {
      user_address: "not available",
      socket_id: "not available",
      api_response_data: "pending",
      expiry_days: 1,
      codename: "",
      web3: null,
      rec_enc_key:"",
      rec_sig_key:"",
      nuPassphrase: "",
      bobs: [],
    };
  },
  methods: {
    createPolicy: function () {
      axios
        .post(
          "/api/v1/policy/create",
          querystring.stringify({
            alice_address: this.user_address,
            alice_password: this.nuPassphrase,
            socket_id: this.socket_id,
            code_name: this.codename,
            expiry_days: this.expiry_days,
            bob_enc_key: this.rec_enc_key,
            bob_sig_key: this.rec_sig_key,
          })
        )
        .then((response) => {
          this.download(response.data)
        }).catch((err) => {
          this.$buefy.toast.open({
            duration: 5000,
            message: err,
            position: 'is-bottom',
            type: 'is-danger'
          }) 
        });
    },
    fetchBobs: function() {
      axios
        .get("/api/v1/public/bobs")
        .then((response) => {
          this.bobs = response.data.bobs
        }).catch((err) => {
          this.$buefy.toast.open({
              duration: 5000,
              message: err,
              position: 'is-bottom',
              type: 'is-danger'
          }) 
        })
    },
    setBob: function(bob) {
      axios
        .get("/api/v1/public/bobs/"+bob)
        .then((response) => {
          this.rec_sig_key = response.data.data.pub_sig_key
          this.rec_enc_key = response.data.data.pub_enc_key
        }).catch((err) => {
          this.$buefy.toast.open({
              duration: 5000,
              message: err,
              position: 'is-bottom',
              type: 'is-danger'
          }) 
        })
    },
    download: function(data) {
      var filename = "policy.json"
      var text = JSON.stringify(data)
      var element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();

      document.body.removeChild(element);
    },
    signMsg: async function (ws, data) {
      var msg = {
        address: this.web3.utils.toHex(data.address),
        message: this.web3.utils.toHex(data.message),
      };

      /* eslint-disable no-unused-vars */
      const { result, _ } = await this.$buefy.dialog.confirm({
        message: JSON.stringify(data, null, 2),
        closeOnConfirm: true,
        cancelText: "Disagree",
        confirmText: "Sign",
        onConfirm: () => this.$buefy.toast.open("Signing..."),
      });
      /* eslint-enable no-unused-vars */

      if (result) {
        this.web3.eth.sign(msg.message, msg.address).then((sig) => {
          ws.send(
            JSON.stringify({
              kind: "signmsg_resp",
              sid: this.socket_id,
              resp: sig,
            })
          );
        });
      }
    },
    signTx: async function (ws, data) {
      var txParams = {
        gasPrice: this.web3.utils.toHex(data.gasPrice),
        chainId: this.web3.utils.toHex(data.chainId),
        value: this.web3.utils.toHex(data.value),
        from: this.web3.utils.toHex(data.from),
        gas: this.web3.utils.toHex(data.gas),
        to: this.web3.utils.toHex(data.to),
        data: this.web3.utils.toHex(data.data),
      };

      /* eslint-disable no-unused-vars */
      const { result, _ } = await this.$buefy.dialog.confirm({
        message: JSON.stringify(data, null, 2),
        closeOnConfirm: true,
        cancelText: "Disagree",
        confirmText: "Sign",
        onConfirm: () => this.$buefy.toast.open("Signing..."),
      });
      /* eslint-enable no-unused-vars */

      if (result) {
        this.web3.eth.signTransaction(txParams).then((sig) => {
          ws.send(
            JSON.stringify({
              kind: "signtx_resp",
              sid: this.socket_id,
              resp: sig.raw,
            })
          );
        });
      }
    },
  },
};
</script>
