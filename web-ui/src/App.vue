<template>
  <div>
   <headerComponent></headerComponent>
   <template v-if="$store.state.checking_session"></template>
   <template v-else>
     <loginForm v-if="$store.state.logged_in === false"></loginForm>
     <homeComponent v-else-if="$store.state.logged_in === true"></homeComponent>
   </template>
  </div>
</template>

<script>

import HeaderComponent from './components/misc/header.vue';
import LoginForm from './components/pages/login.vue';
import HomeComponent from './components/pages/home.vue';
import axios from 'axios';

import { mapGetters } from 'vuex';

export default {
 
  computed: {
    checking_session() {
      return store.state.checking_session;
    },
    logged_in() {
      return store.state.logged_in;
    }
  },

  data() {
    return {}
  },

  created() {

    axios.interceptors.request.use(function(config) {

      var token = sessionStorage.getItem('token');

      config['headers']['Authorization'] = token;
      return config;
    });

    axios.post('/httpapi/v1/commands/session')
      .then(function() {
        this.$store.commit('session_checked');
        this.$store.commit('login');
      }.bind(this))
      .catch(function() {
        this.$store.commit('session_checked');
        this.$store.commit('logout');
      }.bind(this));
  },

  components: {
    'headerComponent': HeaderComponent,
    'loginForm': LoginForm,
    'homeComponent': HomeComponent
  }
};

</script>

<style lang="scss">

body, html {
  padding: 0px;
  margin: 0px;
}
</style>
