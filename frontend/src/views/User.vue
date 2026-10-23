<template>
  <el-card style="max-width: 100%">
    <template #header>
      <div class="card-header">
        <span style="font-size: large;">用户列表</span>
      </div>
    </template>
    <div class="input-group">
      <el-input v-model="params.username" :suffix-icon="Search" placeholder="支持模糊搜索" clearable
        @keyup.enter="handleSearch" @clear="handleSearch"><template #prepend>账号</template></el-input>
      <el-input v-model="params.name" :suffix-icon="Search" placeholder="支持模糊搜索" clearable @keyup.enter="handleSearch"
        @clear="handleSearch"><template #prepend>昵称</template></el-input>
      <el-button type="primary" :disabled="isQuery" :icon="Search" @click="handleSearch">查询</el-button>
      <el-button :disabled="isQuery" :icon="RefreshLeft" style="margin-left: 8px;" @click="handleReset">重置</el-button>
      <el-button type="warning" :icon="Plus" @click="handleAdd">新增</el-button>
      <el-button type="danger" :icon="Delete" :disabled="selectedRows.length === 0"
        @click="handleBatchDelete">删除</el-button>
    </div>
  </el-card>
  <el-card style="max-width: 100%; margin-top: 1rem; padding: 0.25rem 1rem;">
    <el-table :data="tableData" stripe max-height="800" v-loading="loading" style="width: 100%"
      @selection-change="handleSelectionChange"
      :header-cell-style="{ background: '#263445', color: '#cfd7e1', fontWeight: 'bold' }">
      <el-table-column type="selection" width="55" :selectable="row => row.role !== 'admin'" />
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="username" label="账号" width="150" />
      <el-table-column prop="name" label="昵称" width="100" />
      <el-table-column prop="avatar" label="头像" width="100">
        <template #default="{ row }">
          <el-avatar v-if="row.avatar" :src="row.avatar" style="width: 30px; height: 30px;" />
          <el-avatar v-else :icon="UserFilled" style="width: 30px; height: 30px;" />
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" width="180" />
      <el-table-column prop="email" label="邮箱" width="200" show-overflow-tooltip />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          {{ row?.role === 'admin' ? '管理员' : row?.role === 'student' ? '学生' : '未知' }}
        </template>
      </el-table-column>

      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'">
            {{ row.status === 1 ? '正常' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="primary" plain bg @click="handleEdit(row)" :disabled="row.role === 'admin'">编辑</el-button>
          <el-button type="danger" plain bg @click="handleDelete(row)" :disabled="row.role === 'admin'">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
      <el-pagination background layout="total, ->, prev, pager, next, ->, sizes" :total="total" :pager-count="5"
        :page-sizes="[10, 20, 50, 100]" v-model:page-size="params.pageSize" v-model:current-page="params.page"
        @current-change="handleCurrentChange" @size-change="handleSizeChange" />
    </div>
  </el-card>
  <el-dialog v-model="dialogVisible" :title="isAdd ? '新增用户' : '编辑用户'" width="500" destroy-on-close
    :close-on-click-modal="false">
    <el-form :model="ruleForm" ref="ruleFormRef" :rules="rules" label-width="auto" style="min-width: 300px;"
      label-position="left" v-loading="diaLoading" status-icon>
      <el-form-item label="账 号" prop="username">
        <el-input v-model="ruleForm.username" placeholder="请输入账号" />
      </el-form-item>
      <el-form-item v-if="isAdd" label="密 码" prop="password">
        <el-input v-model="ruleForm.password" placeholder="请输入密码" />
      </el-form-item>
      <el-form-item label="昵 称" prop="name">
        <el-input v-model="ruleForm.name" placeholder="请输入昵称" />
      </el-form-item>
      <el-form-item label="邮 箱" prop="email">
        <el-input v-model="ruleForm.email" placeholder="请输入邮箱" />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="ruleForm.phone" placeholder="请输入手机号" />
      </el-form-item>
      <el-form-item label="角 色" prop="role">
        <el-select v-model="ruleForm.role" placeholder="请选择角色">
          <el-option label="管理员" value="admin" />
          <el-option label="学 生" value="student" />
        </el-select>
      </el-form-item>
      <el-form-item label="状 态" prop="status">
        <el-select v-model="ruleForm.status" placeholder="请选择状态">
          <el-option label="正 常" :value='1' />
          <el-option label="禁 用" :value='0' />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">提交</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { createUserApi, deleteUsersApi, deleteUserApi, getUserPageListApi, updateUserApi } from '@/api/user';
import { reactive, ref, onMounted, computed, markRaw } from 'vue';
import { Search, UserFilled, Delete, Plus, RefreshLeft } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';


const params = reactive({
  page: 1,
  pageSize: 10,
  username: '',
  name: '',
})

const tableData = ref([])
const loading = ref(false)
const total = ref(0)

// 分页查询
const handleSizeChange = () => {
  params.page = 1
  loadData()
}
const handleCurrentChange = () => {
  loadData()
}

// 搜索查询
const isQuery = computed(() => !params.username?.trim() && !params.name?.trim())
const handleSearch = () => {
  params.page = 1
  loadData()
}
// 重置
const handleReset = () => {
  params.username = ''
  params.name = ''
  params.page = 1
  loadData()
}
// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除用户 ${row?.username} ？`,
      'Warning',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        closeOnClickModal: false,
        type: 'warning',
        icon: markRaw(Delete),
      }
    )
  } catch {
    return
  }

  try {
    const res = await deleteUserApi(row.id)
    if (res.code === 200) {
      ElMessage.success('删除成功')
      loadData()
    }
  } catch {
    ElMessage.error('删除失败，请稍后重试')
  }
}

// 批量删除
const selectedRows = ref([])
const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}
const handleBatchDelete = async () => {
  const count = selectedRows.value.length
  const ids = selectedRows.value.map(row => row.id)
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${count} 个用户 ？`,
      'Warning',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        closeOnClickModal: false,
        type: 'warning',
        icon: markRaw(Delete),
      }
    )
  } catch {
    return
  }

  try {
    const res = await deleteUsersApi(ids)
    if (res.code === 200) {
      ElMessage.success(`成功删除 ${res.data?.deleted ?? count} 个用户`)
      loadData()
    }
  } catch {
    ElMessage.error('删除失败，请稍后重试')
  }
}

// 编辑与新增
const diaLoading = ref(false)
const dialogVisible = ref(false)
const submitLoading = ref(false)
const isAdd = ref(false)
const ruleForm = reactive({
  username: '',
  name: null,
  role: 'student',
  email: null,
  phone: null,
  avatar: null,
  status: 1
})
const ruleFormRef = ref()
const rules = {
  username: [
    { required: true, message: '请输入账号', trigger: 'blur' },
    { min: 6, max: 12, message: '账号字符长度不能小于6或大于12', trigger: 'blur' }
  ],
  name: [
    { min: 2, max: 6, message: '昵称字符长度不能小于2或大于6', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  password: [
    { min: 6, max: 12, message: '密码字符长度不能小于6或大于12', trigger: 'blur' }
  ],
  email: [
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}
const resetForm = () => {
  Object.assign(ruleForm, {
    id: null,
    username: '',
    password: '',
    name: null,
    role: 'student',
    email: null,
    phone: null,
    avatar: null,
    status: 1
  })
}
const handleEdit = async (row) => {
  isAdd.value = false
  resetForm()
  Object.assign(ruleForm, {
    id: row.id,
    username: row.username,
    name: row.name,
    role: row.role,
    email: row.email,
    phone: row.phone,
    avatar: row.avatar,
    status: row.status
  })
  dialogVisible.value = true
}
const handleAdd = () => {
  isAdd.value = true
  resetForm()
  dialogVisible.value = true
}
const handleSubmit = async () => {
  try {
    await ruleFormRef.value.validate()
  } catch { return }

  const payload = { ...ruleForm }
  for (const k of ['name', 'email', 'phone', 'avatar']) {
    if (!payload[k]) payload[k] = null
  }
  if (!payload.password) delete payload.password

  try {
    submitLoading.value = true
    const res = isAdd.value ? await createUserApi(payload) : await updateUserApi(ruleForm.id, payload)
    if (res.code === 200) {
      dialogVisible.value = false
      ElMessage.success(isAdd.value ? '新增成功' : '修改成功')
      loadData()
    }
  } finally {
    submitLoading.value = false
  }
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await getUserPageListApi({
      'page': params.page,
      'page_size': params.pageSize,
      'username': params.username?.trim() || null,
      'name': params.name?.trim() || null
    })
    if (res.code === 200) {
      tableData.value = res.data?.data ?? []
      total.value = res.data?.total ?? 0
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

</script>

<style scoped>
.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;

  min-width: 400px;
}
</style>