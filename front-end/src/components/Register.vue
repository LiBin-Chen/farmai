<template>
  <div class="container">
    <h1>Register</h1>
    <div class="row">
      <div class="col-md-4">
        <form @submit.prevent="onSubmit">
          <div class="form-group">
            <label for="username">Username</label>
            <input type="text" v-model="registerForm.username" class="form-control" v-bind:class="{'is-invalid': registerForm.usernameError}" id="username" placeholder="">
            <div v-show="registerForm.usernameError" class="invalid-feedback">{{ registerForm.usernameError }}</div>
          </div>
          <div class="form-group">
            <label for="email">Email address</label>
            <input type="email" v-model="registerForm.email" class="form-control" v-bind:class="{'is-invalid': registerForm.emailError}" id="email" aria-describedby="emailHelp" placeholder="">
            <small v-if="!registerForm.emailError" id="emailHelp" class="form-text text-muted">We'll never share your email with anyone else.</small>
            <div v-show="registerForm.emailError" class="invalid-feedback">{{ registerForm.emailError }}</div>
          </div>
          <div class="form-group">
            <label for="password">Password</label>
            <input type="password" v-model="registerForm.password" class="form-control" v-bind:class="{'is-invalid': registerForm.passwordError}" id="password" placeholder="">
            <div v-show="registerForm.passwordError" class="invalid-feedback">{{ registerForm.passwordError }}</div>
          </div>
          <button type="submit" class="btn btn-primary">Register</button>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
  import store from '../store.js'

  export default {
    name: "Register",
    data() {
      return {
        registerForm: {
          username: '',
          email: '',
          password: '',
          submitted: false, //是否点击了 submit 按钮
          errors: 0,  //表达是否在前端验证通过,0表示没有错误,验证通过
          usernameError: null,
          emailError: null,
          passwordError: null,
        }
      }
    },
    methods: {
      onSubmit(e) {
        this.registerForm.submitted = true;  //先更新状态
        this.registerForm.errors = 0;

        if (!this.registerForm.username) {
          this.registerForm.errors++;
          this.registerForm.usernameError = 'Username Require.';
        } else {
          this.registerForm.usernameError = null
        }

        if (!this.registerForm.email) {
          this.registerForm.errors++;
          this.registerForm.emailError = 'Email Require.';
        } else {
          this.registerForm.emailError = null
        }

        if (!this.registerForm.password) {
          this.registerForm.errors++;
          this.registerForm.passwordError = 'Password Require.';
        } else {
          this.registerForm.passwordError = null
        }

        if (this.registerForm.errors > 0) {
          //表示表单验证没有通过,不继续往下执行,即不会通过axios调用后端api
          return false
        }

        const path = '/users'
        const payload = {
          username: this.registerForm.username,
          email: this.registerForm.email,
          password: this.registerForm.password,
        }
        this.$axios.post(path, payload)
          .then((response) => {
            //handle success
            this.$toasted.success('Congratulations,you are now a registered user!', {icon: 'fingerprint'})
            this.$route.push('/login')
          })
          .catch((error) => {
            //handle error
            for (var field in error.response.data.message) {
              if (field == 'username') {
                this.registerForm.usernameError == error.response.data.message.username
              } else if (field == 'email') {
                this.registerForm.emailError == error.response.data.message.email
              } else if (field == 'password') {
                this.registerForm.passwordError == error.response.data.message.password
              }
            }
          });
      },
      validEmail: function (email) {
        var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(email);

      }
    }
  }
</script>

<style scoped>

</style>
