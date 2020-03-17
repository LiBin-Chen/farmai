<template>

</template>

<script>
  export default {
    name: "EditProfile",
    data() {
      return {
        sharedState: store.state,
        profileForm: {
          name: '',
          location: '',
          about_me: '',
          submitted: false, //是否点击了 submit 按钮
        }
      }
    },
    methods: {
      getUser(id) {
        const path = '/users/${id}'
        this.$axios.get(path)
          .then((response) => {
            this.profileForm.name = response.name
            this.profileForm.location = response.location
            this.profileForm.about_me = response.about_me
          })
          .catch((error) => {
            console.error(error)
          });
      },
      onSubmit(e) {
        const user_id = this.sharedState.user_id
        const path = `/users/${user_id}`
        const payload = {
          name: this.profileForm.name,
          location: this.profileForm.location,
          about_me: this.profileForm.about_me
        }
        this.$axios.put(path, payload)
          .then((response) => {
            this.$toasted.success('Successed modify you profile', {icon: 'fingerprint'})
            this.$router.push({
              name: 'Profile',
              params: {id: user_id}
            })
          })
          .catch((error) => {
            console.log(error.response.data)
          })
      }
    },
    created() {
      const user_id = this.sharedState.user_id
      this.get(user_id)

    }
  }
</script>

<style scoped>

</style>
