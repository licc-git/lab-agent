<template>
  <el-card style="max-width: 480px; min-width: 300px; padding: 5px 15px;">
    <template #header>
      <div class="card-header">
        <span style="font-weight: 600; font-size: 1rem;">个人中心</span>
      </div>
    </template>
    <el-form :model="ruleForm" ref="ruleFormRef" :rules="rules" label-width="auto"
      style="min-width: 300px;" label-position="left"
      v-loading="loading" status-icon>
      <el-form-item label="头像">
        <el-upload class="avatar-uploader" :show-file-list="false" :http-request="handleFileUpload"
          :before-upload="beforeAvatarUpload">
          <img v-if="imageUrl" :src="imageUrl" class="avatar" />
          <el-icon v-else class="avatar-uploader-icon">
            <Plus />
          </el-icon>
        </el-upload>
      </el-form-item>
      <el-form-item label="账 号">
        <el-input v-model="ruleForm.username" disabled />
      </el-form-item>
      <el-form-item label="昵 称" prop="name">
        <el-input v-model="ruleForm.name" />
      </el-form-item>
      <el-form-item label="邮 箱" prop="email">
        <el-input v-model="ruleForm.email" />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="ruleForm.phone" />
      </el-form-item>
      <el-form-item label="角 色">
        <el-input v-model="roleLabel" disabled />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="submitting" :disabled="!isChanged" @click="submitForm">
          修改
        </el-button>
      </el-form-item>
    </el-form>


  </el-card>
</template>

<script setup>
import { updateUserInfoApi, getUserInfoApi, uploadAvatarApi } from '@/api/user';
import { ref, reactive, computed, onMounted } from 'vue';
import { useUser } from '@/utils/user';
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'


const ruleFormRef = ref()
const loading = ref(false)
const submitting = ref(false)
const { updateUser } = useUser()
const ruleForm = reactive({
  username: '',
  name: '',
  email: '',
  phone: '',
  role: '',
  avatar: '',
})

let original = {}

const loadUserInfo = async () => {
  loading.value = true
  try {
    const res = await getUserInfoApi()
    if (res.code === 200) {
      Object.assign(ruleForm, res.data)
      imageUrl.value = res.data.avatar || ''
      original = JSON.parse(JSON.stringify(res.data))
    }
  } finally {
    loading.value = false
  }
}

// 检查数据是否修改
const isChanged = computed(
  () => {
    const key = ['name', 'phone', 'email', 'avatar']
    return key.some(k => original[k] !== ruleForm[k]?.trim())
  }
)

// 角色选择
const roleLabel = computed(() => {
  return ruleForm.role === 'admin' ? '管理员' : ruleForm.role === 'student' ? '学生' : '未知角色'
})

// 表单验证规则
const rules = reactive({
  name: [
    { required: true, message: '请输入昵称', trigger: 'blur' },
    { min: 2, max: 6, message: '昵称字符长度不能小于3或大于6', trigger: 'blur' }
  ],
  email: [{ type: 'email', message: '邮箱格式错误', trigger: 'blur' }],
  phone: [{ pattern: /^1[3-9]\d{9}$/, message: '手机号格式错误', trigger: 'blur' }],
})

const submitForm = async () => {
  try {
    await ruleFormRef.value.validate()      // 校验不通过会 reject，直接跳到 catch
  } catch {
    return
  }
  submitting.value = true
  try {
    const res = await updateUserInfoApi(ruleForm)
    if (res.code === 200) {
      updateUser(res.data)
      ElMessage.success('更新成功')
      original = JSON.parse(JSON.stringify(ruleForm))   // 提交成功后刷新快照，防止"旧快照"误判
    }
  } finally {
    submitting.value = false
  }
}
// 头像
const imageUrl = ref('')
const handleFileUpload = async ({ file }) => {
  try {
    const res = await uploadAvatarApi(file)
    if (res.code === 200) {
      imageUrl.value = res.data.url
      ruleForm.avatar = res.data.url
      ElMessage.success('上传成功')
    }
  } catch (e) {
    console.log(e)
    ElMessage.error('上传失败')
  }
}

const beforeAvatarUpload = (rawFile) => {
  const imageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  if (!imageTypes.includes(rawFile.type)) {
    ElMessage.error('只能上传图片')
    return false
  } else if (rawFile.size / 1024 / 1024 > 2) {
    ElMessage.error('上传图片大小不能超过2M')
    return false
  }
  return true
}


onMounted(() => { loadUserInfo() })

</script>

<style scoped>
.avatar-uploader .avatar {
  width: 100px;
  height: 100px;
  display: block;
}
</style>

<style>
.avatar-uploader .el-upload {
  border: 1px dashed var(--el-border-color);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  transition: var(--el-transition-duration-fast);
}

.avatar-uploader .el-upload:hover {
  border-color: var(--el-color-primary);
}

.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  text-align: center;
}
</style>