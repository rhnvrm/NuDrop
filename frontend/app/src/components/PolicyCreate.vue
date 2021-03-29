<template>
  <div class="section">
    Policy Create
    <div>User address: {{ user_address }}</div>
  </div>
</template>

<script>
import WalletConnectProvider from "@walletconnect/web3-provider";

// import Web3 from "web3";
export default {
  mounted() {
    //  Create WalletConnect Provider
    const provider = new WalletConnectProvider({
    infuraId: "79153147849f40cf9bc97d4ec3c6416b",
    });

    //  Enable session (triggers QR Code modal)
    provider.enable().then(alert);
  },
  data: function () {
    return {
      user_address: "not available",
    };
  },
};
</script>
