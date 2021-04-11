<template>
  <div class="section">
    Policy Create
    <div>User address: {{ user_address }}</div>
    <div>Socket address: {{ socket_id }}</div>

    <button v-on:click="createPolicy">Create policy</button>

    <div>{{ prototype_data }}</div>
  </div>
</template>

<script>
import Web3 from "web3";
// import { Manager } from "socket.io-client";
import axios from "axios";
import PrivateKeyProvider from "truffle-privatekey-provider";
export default {
  async mounted() {
    if (this.$store.state.private_key == "not available") {        
      this.$router.push('/me/wallet');
    }

    var provider = new PrivateKeyProvider(
      this.$store.state.private_key,
      "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b"
    );

    var web3 = new Web3(provider);

    var client_id = Date.now();
    var ws = new WebSocket(`ws://localhost/api/ws/${client_id}`);
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
          var txParams = {
            gasPrice: web3.utils.toHex(data.gasPrice),
            chainId: web3.utils.toHex(data.chainId),
            value: web3.utils.toHex(data.value),
            from: web3.utils.toHex(data.from),
            gas: web3.utils.toHex(data.gas),
            to: web3.utils.toHex(data.to),
            data: web3.utils.toHex(data.data),
          };

          web3.eth.signTransaction(txParams).then((sig) => {
            ws.send(
              JSON.stringify({
                kind: "signtx_resp",
                sid: this.socket_id,
                resp: sig.raw,
              })
            );
          });

          break;

        case "sign_message":
          var msg = {
            address: web3.utils.toHex(data.address),
            message: web3.utils.toHex(data.message),
          };

          web3.eth.sign(msg.message, msg.address).then((sig) => {
            ws.send(
              JSON.stringify({
                kind: "signmsg_resp",
                sid: this.socket_id,
                resp: sig,
              })
            );
          });

          break;
      }
    };

    ws.onopen = () =>
      ws.send(
        JSON.stringify({
          kind: "on_load",
        })
      );
  },
  data: function () {
    return {
      user_address: "not available",
      socket_id: "not available",
      prototype_data: "pending",
    };
  },
  methods: {
    createPolicy: function () {
      axios
        .post("http://localhost/api/v1/policy/create", {
          alice_address: this.user_address,
          socket_id: this.socket_id,
        })
        .then((response) => (this.prototype_data = response.data));
    },
  },
};
</script>
