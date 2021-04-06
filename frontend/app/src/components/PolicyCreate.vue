<template>
  <div class="section">
    Policy Create
    <div>User address: {{ user_address }}</div>
    <div>Socket address: {{ socket_id }}</div>

    <button v-on:click="createPolicy">Create policy</button>
  </div>
</template>

<script>
// import WalletConnectProvider from "@walletconnect/web3-provider";

import Web3 from "web3";
// import { Transaction } from "@ethereumjs/tx";
// import Common from "@ethereumjs/common";
// import {toBuffer} from "ethereumjs-util";
import { io } from "socket.io-client";
import axios from "axios";
import PrivateKeyProvider from "truffle-privatekey-provider"
export default {
  async mounted() {

    var privateKey = "0ce60fcab58b5ea3134dc0c1be9a3bdfab7d603cef0cee9053dd3291f59133c6";
    var provider = new PrivateKeyProvider(privateKey, "https://goerli.infura.io/v3/79153147849f40cf9bc97d4ec3c6416b");

    var web3 = new Web3(provider);
    console.log("here");


    // var txParams = {
    //   gasPrice: web3.utils.toHex(1353462421),
    //   chainId: web3.utils.toHex(5),
    //   value: web3.utils.toHex(100000000000),
    //   from: this.user_address,
    //   gas: web3.utils.toHex(164076),
    //   to: "0xaC5e34d3FD41809873968c349d1194D23045b9D2",
    //   data:
    //     "0x81e742a155c0bba8d63a253166c5d1ecbf7c811d00000000000000000000000000000000000000000000000000000000c968123712e0fde083b12e408da2db9b5c6d077200000000000000000000000000000000000000000000000000000000606611d900000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000001000000000000000000000000542d4b7f72cddf9cf020602ca1c9d58482ec3254",
    // };

    const socket = io("ws://localhost:5000");

    socket.emit("on_load", {});

    socket.on("prompt_login", async (data) => {
      console.log()
      this.user_address = web3.eth.accounts.wallet._accounts.currentProvider.address;
      this.socket_id = data.socket_id;
    });

    socket.on("sign_transaction", async (data) => {
      console.log("INDATA", data);
      var txParams = {
        gasPrice: web3.utils.toHex(data.gasPrice),
        chainId: web3.utils.toHex(data.chainId),
        value: web3.utils.toHex(data.value),
        from: web3.utils.toHex(data.from),
        gas: web3.utils.toHex(data.gas),
        to: web3.utils.toHex(data.to),
        data: web3.utils.toHex(data.data),
      }
      // console.log("this.user", this.user_address)
      // let nonce = await web3.eth.getTransactionCount(this.user_address);

      // console.log("nonce", nonce);

      // if (txParams.chainId && Number(txParams.chainId) > 1) nonce += 1048576;

      // txParams.nonce = web3.utils.toHex(nonce);

      // console.log(txParams);

      // const common = new Common({ chain: "goerli" });
      // const tx = Transaction.fromTxData(txParams, { common });

      // var stx = web3.utils.toHex(tx.getMessageToSign());
      // console.log("stx",stx)

      // var sig = await web3.eth.personal.sign(stx, this.user_address, (err) => {
      //   console.log("err signing", err)
      // });
      // console.log("sig", sig);

      // const pkey = toBuffer("0x0ce60fcab58b5ea3134dc0c1be9a3bdfab7d603cef0cee9053dd3291f59133c6")
      // console.log("pkey", pkey)
      // var sig = tx.sign(pkey)
      // console.log("sig", sig.serialize().toString('hex'))

      var sig = await web3.eth.signTransaction(txParams)
      console.log(sig)
      // var signing_address = await web3.eth.personal.ecRecover(stx, sig)
      // console.log("sa", signing_address)
      socket.emit("signtx_resp", {
        sid: this.socket_id,
        resp: "0x" + sig.raw,
      });
    });
  },
  data: function () {
    return {
      user_address: "not available",
      socket_id: "not available",
    };
  },
  methods: {
    createPolicy: function () {
      axios
        .post("http://localhost:5000/api/prototype", {
          alice_address: this.user_address,
          socket_id: this.socket_id,
        })
        .then((response) => (this.prototype_data = response.data));
    },
  },
};
</script>
