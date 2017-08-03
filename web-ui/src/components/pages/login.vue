<template>
  <form action="/httpapi/v1/commands/authenticate" method="POST" v-on:submit="login">
    <label for="login-username">Username</label><input type="text" name="username=" id="login-username" v-model="username">
    <label for="login-password">Password</label><input type="password" name="password" id="login-password" v-model="password">
    <button type="submit">Login</button>
  </form>
</template>

<script>

import axios from 'axios';

export default {
  props: ['logged_in'],
  data() {
    return {
      username: '',
      password: ''
    }
  },
  methods: {
    login(event) {
      event.stopPropagation();
      event.preventDefault();

      var loginUrl = this.$el.getAttribute('action');

      console.log('trying to login');
      console.log('username: ', this.username);
      console.log('password: ', this.password);

      axios.post(loginUrl, {
        'username': this.username,
        'password': this.password
      })
      .then(function(response) {
        var token = response.data.token;
        sessionStorage.setItem('token', token);
        this.$store.commit('login');
      }.bind(this));

    }
  }
}

</script>
