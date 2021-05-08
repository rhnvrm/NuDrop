<template>
  <div class="section">
    <section class="hero is-medium is-primary">
      <div class="hero-body">
        <p class="title">Welcome to NuDrop</p>
        <p class="subtitle">
          Share data securely. Powered by <a href="https://nucypher.com">NuCypher</a>.
        </p>
      </div>
    </section>

    <div class="tile is-ancestor mt-2">
      <div class="tile is-parent">
        <div class="tile is-child box">
          <p class="content">
            NuDrop utilizes the cryptographic infra of <a href="https://nucypher.com">NuCypher</a> network and
            allow users to share and submit data anonymously by people such as
            whistleblowers and journalists to organizations such as media
            outlets. It provides a side-channel app on top of NuCypher which
            facilitates this communication.
          </p>
        </div>
      </div>
    </div>
    <div class="tile is-ancestor mt-2">
      <div class="tile is-parent">
        <div class="tile is-child box">
          <p class="title">Receive Encrypted Documents</p>
          <b-steps
            size="is-medium">
            <b-step-item label="Wallet" icon="account-key">
              Set up your <router-link to="/me/wallet">wallet</router-link> <br />
              Generate your pseudonym.
            </b-step-item>

            <b-step-item label="Share" icon="share-circle" clickable>
              Share your Umbral keys under your pseudonym. <br />
              The pseudonym is visibile for 7 days to policy creators. 
            </b-step-item>

            <b-step-item label="Receive" icon="download-lock" clickable>
              Receive the <pre>policy.json</pre> and <pre>encrypted.json</pre> files from the sender<br />
              (coming soon, directly share files via ipfs)
            </b-step-item>
          </b-steps>
        </div>
      </div>
      <div class="tile is-parent">
        <div class="tile is-child box">
          <p class="title">Send Encrypted Documents</p>
          <b-steps
            size="is-medium">
            <b-step-item label="Wallet" icon="account-key" >
              Set up your <router-link to="/me/wallet">wallet</router-link> <br />
              Your wallet stores your private key and it does not leave your browser. 
            </b-step-item>

            <b-step-item label="Policy" icon="account" clickable >
              Create a <router-link to="/policy/create">policy</router-link> <br />
              Optionally search for public receivers. <br />
              You can set up how many days it will be available. <br />
              Encrypt multiple files using a single policy. <br />
            </b-step-item>

            <b-step-item label="Share" icon="share-circle" clickable>
              Send the <pre>policy.json</pre> and <pre>encrypted.json</pre> files to the receiver<br />
              (coming soon, directly share files via ipfs)
            </b-step-item>
          </b-steps>
        </div>
      </div>
    </div>
  </div>
</template>