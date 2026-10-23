<template>
  <div class="register-container">
    <div class="register-box">
      <h1 style="font-size: 24px; margin-bottom: 30px">欢迎注册实验室预约系统</h1>

      <el-form :model="form" label-width="auto" style="max-width: 600px" ref="ruleFormRef" :rules="rules">
        <el-form-item prop="username">
          <el-input size="large" v-model="form.username" placeholder="请输入账号" :prefix-icon="User" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input type="password" size="large" v-model="form.password" placeholder="请输入密码" :prefix-icon="Lock"
            show-password />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input type="password" size="large" v-model="form.confirmPassword" placeholder="请确认密码" :prefix-icon="Lock"
            show-password />
        </el-form-item>
        <div>
          <el-button size="large" type="primary" style="width: 100%" @click="register" :loading="loadingValue">注
            册</el-button>
          <div style="text-align: right; margin-top: 20px">
            已有账号？请 <router-link style="color: var(--el-color-primary)" to="/login">登录</router-link>
          </div>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { registerApi } from '@/api/auth'
import router from '@/router'
import { ElMessage } from 'element-plus'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})
const ruleFormRef = ref()
const loadingValue = ref(false)

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('Please input the password again'))
  } else if (value !== form.password) {
    callback(new Error("Two inputs don't match!"))
  } else {
    callback()
  }
}

const rules = reactive({
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 3, max: 12, message: '账号长度 3-12 位', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 12, message: '密码长度 6-12 位', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 12, message: '密码长度 6-12 位', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ],
})

const register = async () => {
  try {
    await ruleFormRef.value.validate()
  } catch {
    return;
  }
  loadingValue.value = true;
  try {
    const res = await registerApi(form)
    if (res.code === 200) {
      ElMessage.success("注册成功")
      await router.push("/login")
    }
  } finally {
    loadingValue.value = false;
  }
}

</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-box {
  width: 380px;
  border-radius: 8px;
  box-shadow: 0 8px 12px rgba(0, 0, 0, 0.1);
  padding: 30px;
  text-align: center;
  background-color: white;
}
</style>
