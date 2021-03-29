<template>
    <b-navbar>
        <template #brand>
            <b-navbar-item tag="router-link" :to="{ path: '/' }">
                <img alt="NuDrop logo" src="../assets/logo.png">
            </b-navbar-item>
        </template>
        <template #start>
            <b-navbar-item tag="router-link" to="/">
                Home
            </b-navbar-item>
            <b-navbar-dropdown hoverable="true" label="Policy">
                <b-navbar-item  tag="router-link" to="/policy/create">
                    Create
                </b-navbar-item>
            </b-navbar-dropdown>
            <b-navbar-dropdown hoverable="true" label="Files">
                <b-navbar-item tag="router-link" to="/encrypt">
                    Encrypt
                </b-navbar-item>
                <b-navbar-item tag="router-link" to="/me/files">
                    My Files
                </b-navbar-item>
            </b-navbar-dropdown>
            <b-navbar-dropdown hoverable="true" label="Info">
                <b-navbar-item href="#">
                    About
                </b-navbar-item>
                <b-navbar-item href="#">
                    FAQ
                </b-navbar-item>
            </b-navbar-dropdown>
        </template>

        <template #end>
            <b-navbar-item tag="div">
                <div class="buttons">
                    <a class="button is-primary">
                        <strong>Sign up</strong>
                    </a>
                    <a class="button is-light">
                        Log in
                    </a>
                </div>
            </b-navbar-item>
        </template>
    </b-navbar>
</template>