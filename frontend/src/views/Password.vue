<template>
  <el-card style="max-width: 480px; min-width: 300px; padding: 5px 15px;">
    <template #header>
      <div class="card-header">
        <span style="font-weight: 600; font-size: 1rem;">密码管理</span>
      </div>
    </template>
    <el-form :model="ruleForm" label-width="auto" style="min-width: 300px;" ref="ruleFormRef" :rules="rules">
      <el-form-item label="原密码" prop="oldPassword">
        <el-input v-model="ruleForm.oldPassword" type="password" placeholder="请输入原密码" autocomplete="off" />
      </el-form-item>
      <el-form-item label="新密码" prop="newPassword">
        <el-input v-model="ruleForm.newPassword" type="password" placeholder="请输入新密码" autocomplete="off" />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirmPassword">
        <el-input v-model="ruleForm.confirmPassword" type="password" placeholder="请再次输入新密码" autocomplete="off" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确认修改</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { updatePasswordApi } from '@/api/user'
import { useUser } from '@/utils/user'
import router from '@/router'

const { logout } = useUser()
const ruleFormRef = ref()
const submitting = ref(false)
const ruleForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else if (value !== ruleForm.newPassword) {
    callback(new Error('两次密码输入不一致'))
  } else {
    callback()
  }
}

const rules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validatePass, trigger: 'blur' }]
}

const handleSubmit = async () => {
  const valid = await ruleFormRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const res = await updatePasswordApi({
      old_password: ruleForm.oldPassword,
      new_password: ruleForm.newPassword
    })
    if (res.code === 200) {
      ElMessage.success('密码修改成功，请重新登录')
      logout()
      await router.push('/login')
    }
  } finally {
    submitting.value = false
  }
}
</script>