<template>
  <div class="section">
    <div>User address: {{ user_address }}</div>
    <div>Socket address: {{ socket_id }}</div>

    <div>{{ api_response_data }}</div>

    <h1 class="title">Decrypt File</h1>
    <b-field label="Codename">
      <b-input v-model="codename" placeholder=""></b-input>
    </b-field>
    <b-field message="ipfs uri where the file will be stored">
      <p class="control">
        <span class="button is-static">ipfs://</span>
      </p>
      <b-input expanded></b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Policy Encrypting Key"
        type="text"
        icon="key"
        v-model="policy_key"
      >
      </b-input>
    </b-field>
    <b-field>
      <b-input
        placeholder="Sender Verifying Key"
        type="text"
        icon="key"
        v-model="alice_verifying_key"
      >
      </b-input>
    </b-field>

    <b-field label="Nucypher Passphrase">
      <b-input 
        v-model="nuPassphrase" 
        placeholder="passphrase"></b-input>
    </b-field>

    <b-field label="Ciphertext">
      <b-input v-model="ciphertext" type="textarea"></b-input>
    </b-field>

    <b-field label="Decrypted File">
      <Editor @editor-data="editorDataUpdate"></Editor>
    </b-field>

    <div class="buttons">
      <b-button @click="decryptData" type="is-primary" expanded
        >Decrypt</b-button
      >
    </div>
  </div>
</template>

<script>
import Editor from "./Editor.vue";
import axios from "axios";
import querystring from "querystring";
import Web3 from "web3";
import PrivateKeyProvider from "truffle-privatekey-provider";

export default {
  components: {
    Editor,
  },
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
    var wsprotocol = "";
    if (window.location.hostname === "localhost") {
      wsprotocol = "ws";
    } else {
      wsprotocol = "wss";
    }
    var ws = new WebSocket(
      wsprotocol + `://` + window.location.hostname + `/api/ws/${client_id}`
    );
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
  },
  data: function () {
    return {
      editorData: {
        json: "",
        data: "",
      },
      user_address: "not available",
      socket_id: "not available",
      enc_key: "",
      sig_key: "",
      policy_key: "",
      alice_verifying_key: "",
      codename: "",
      api_response_data: "",
      ciphertext: "",
      nuPassphrase: "",
    };
  },
  computed: {
    label: {
      get() {
        return "nudrop/" + this.codename;
      },
    },
  },

  methods: {
    editorDataUpdate: function (data) {
      this.editorData = data;
    },
    decryptData: function () {
      const payload = {
        policy_pub_key: this.policy_key,
        alice_verifying_key: this.alice_verifying_key,
        label: this.label,
        ciphertext: this.ciphertext,
        bob_address: this.user_address,
        bob_password: this.nuPassphrase,
        socket_id: this.socket_id
      };

      axios
        .post("/api/v1/bob/decrypt", querystring.stringify(payload))
        .then((response) => {
          console.log(response);
          this.api_response_data = response;
        });
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