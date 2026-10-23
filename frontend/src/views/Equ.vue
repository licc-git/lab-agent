<template>
  <el-card style="max-width: 100%">
    <template #header>
      <div class="card-header">
        <span style="font-size: large;">设备列表</span>
      </div>
    </template>
    <div class="input-group">
      <el-input v-model="params.keywords" :suffix-icon="Search" placeholder="支持名称/型号模糊搜索" clearable
        @keyup.enter="handleSearch" @clear="handleSearch"><template #prepend>关键词</template></el-input>
      <el-select v-model="params.labId" placeholder="所属实验室" clearable style="width: 180px;">
        <el-option v-for="lab in labOptions" :key="lab.id" :label="lab.name" :value="lab.id" />
      </el-select>
      <el-button type="primary" :disabled="isQuery" :icon="Search" @click="handleSearch">查询</el-button>
      <el-button :icon="RefreshLeft" style="margin-left: 8px;" @click="handleReset">重置</el-button>
      <el-button type="warning" :icon="Plus" @click="handleAdd">新增</el-button>
      <el-button type="danger" :icon="Delete" :disabled="selectedRows.length === 0"
        @click="handleBatchDelete">删除</el-button>
    </div>
  </el-card>
  <el-card style="max-width: 100%; margin-top: 1rem; padding: 0.25rem 1rem;">
    <el-table :data="tableData" stripe max-height="800" v-loading="loading" style="width: 100%"
      @selection-change="handleSelectionChange"
      :header-cell-style="{ background: '#263445', color: '#cfd7e1', fontWeight: 'bold' }">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="img" label="图片" width="120">
        <template #default="{ row }">
          <el-image v-if="row.img" :src="row.img" fit="cover" style="width: 80px; height: 45px; border-radius: 4px;"
            :preview-src-list="[row.img]" preview-teleported hide-on-click-modal>
          </el-image>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="设备名称" width="160" />
      <el-table-column prop="spec" label="型号规格" width="140">
        <template #default="{ row }">{{ row.spec || '—' }}</template>
      </el-table-column>
      <el-table-column prop="lab_name" label="所属实验室" width="150">
        <template #default="{ row }">{{ row.lab_name || '—' }}</template>
      </el-table-column>
      <el-table-column sortable prop="quantity" label="数量" width="90" />
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'warning'">
            {{ row.status === 1 ? '正常' : '维修' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="说明" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ row.description || '—' }}</template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button type="primary" plain bg @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" plain bg @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
      <el-pagination background layout="total, ->, prev, pager, next, ->, sizes" :total="total" :pager-count="5"
        :page-sizes="[10, 20, 50, 100]" v-model:page-size="params.pageSize" v-model:current-page="params.page"
        @current-change="handleCurrentChange" @size-change="handleSizeChange" />
    </div>
  </el-card>
  <el-dialog v-model="dialogVisible" :title="isAdd ? '新增设备' : '编辑设备'" width="500" destroy-on-close
    :close-on-click-modal="false">
    <el-form :model="ruleForm" ref="ruleFormRef" :rules="rules" label-width="auto" style="min-width: 300px;"
      label-position="left" status-icon>
      <el-form-item label="所属实验室" prop="lab_id">
        <el-select v-model="ruleForm.lab_id" placeholder="请选择实验室" style="width: 100%;">
          <el-option v-for="lab in labOptions" :key="lab.id" :label="lab.name" :value="lab.id" />
        </el-select>
      </el-form-item>
      <el-form-item label="设备名称" prop="name">
        <el-input v-model="ruleForm.name" placeholder="请输入设备名称" maxlength="64" show-word-limit />
      </el-form-item>
      <el-form-item label="型号规格" prop="spec">
        <el-input v-model="ruleForm.spec" placeholder="如：DS-1052E（选填）" maxlength="128" />
      </el-form-item>
      <el-form-item label="数 量" prop="quantity">
        <el-input-number v-model="ruleForm.quantity" :min="1" :max="999" />
      </el-form-item>
      <el-form-item label="状 态" prop="status">
        <el-select v-model="ruleForm.status" placeholder="请选择状态">
          <el-option label="正 常" :value="1" />
          <el-option label="维 修" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item label="说 明" prop="description">
        <el-input v-model="ruleForm.description" type="textarea" :rows="3" placeholder="设备说明（选填）" maxlength="512"
          show-word-limit />
      </el-form-item>
      <el-form-item label="图 片" prop="img">
        <el-upload ref="uploadRef" v-model:file-list="fileList" list-type="picture-card" accept="image/*" :limit="1"
          :http-request="handleUpload" :before-upload="checkImage" :on-remove="handleImgRemove"
          :on-exceed="handleExceed">
          <el-icon>
            <Plus />
          </el-icon>
        </el-upload>
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
import { createEquipmentApi, deleteEquipmentListApi, deleteEquipmentApi, getEquipmentPageList, updateEquipmentApi } from '@/api/equipment';
import { getLabOptionsApi } from '@/api/lab';
import { uploadFileApi } from '@/api/files';
import { reactive, ref, onMounted, computed, markRaw } from 'vue';
import { Search, Delete, Plus, RefreshLeft } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';

const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: null,
  labId: null
})

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
// 实验室下拉选项（新增/编辑、筛选共用）
const labOptions = ref([])
const loadLabOptions = async () => {
  const res = await getLabOptionsApi()
  if (res.code === 200) {
    labOptions.value = res.data ?? []
  }
}

// 分页查询
const handleSizeChange = () => {
  params.page = 1
  loadData()
}
const handleCurrentChange = () => {
  loadData()
}

// 搜索查询
const isQuery = computed(() => !params.keywords?.trim() && !params.labId)
const handleSearch = () => {
  params.page = 1
  loadData()
}
// 重置
const handleReset = () => {
  params.keywords = null
  params.labId = null
  params.page = 1
  loadData()
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除设备 ${row?.name} ？`,
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
    const res = await deleteEquipmentApi(row.id)
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
      `确定删除选中的 ${count} 个设备 ？`,
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
    const res = await deleteEquipmentListApi({ ids })
    if (res.code === 200) {
      ElMessage.success(res.message || `成功删除 ${count} 个设备`)
      loadData()
    }
  } catch {
    ElMessage.error('删除失败，请稍后重试')
  }
}

// 编辑与新增
const dialogVisible = ref(false)
const submitLoading = ref(false)
const isAdd = ref(false)
const ruleForm = reactive({
  lab_id: null,
  name: '',
  spec: null,
  quantity: 1,
  status: 1,
  description: null,
  img: null
})
const ruleFormRef = ref()
// 图片上传
const fileList = ref([])
const uploadRef = ref()
const checkImage = (file) => {
  if (!file.type.startsWith('image/')) {
    ElMessage.error('只能上传图片文件')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return false
  }
  return true
}
const handleUpload = async ({ file, onSuccess }) => {
  try {
    const res = await uploadFileApi(file)
    if (res.code === 200) {
      ruleForm.img = res.data.url
      onSuccess(res)
      ElMessage.success('上传成功')
    } else {
      fileList.value.pop()
    }
  } catch {
    fileList.value.pop()
  }
}
const handleImgRemove = () => {
  ruleForm.img = null
}
// 已有 1 张时再选图：替换旧图
const handleExceed = (files) => {
  const file = files[0]
  if (!checkImage(file)) return
  uploadRef.value.clearFiles()
  uploadRef.value.handleStart(file)
  uploadRef.value.submit()
}
const rules = {
  lab_id: [{ required: true, message: '请选择所属实验室', trigger: 'change' }],
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' },
    { min: 1, max: 64, message: '设备名称长度不能大于64', trigger: 'blur' }
  ],
  spec: [
    { max: 128, message: '型号规格长度不能大于128', trigger: 'blur' }
  ],
  quantity: [{ required: true, message: '请输入数量', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
  description: [
    { max: 512, message: '说明长度不能大于512', trigger: 'blur' }
  ],
}
const resetForm = () => {
  Object.assign(ruleForm, {
    id: null,
    lab_id: null,
    name: '',
    spec: null,
    quantity: 1,
    status: 1,
    description: null,
    img: null
  })
  fileList.value = []
}
const handleEdit = (row) => {
  isAdd.value = false
  resetForm()
  Object.assign(ruleForm, {
    id: row.id,
    lab_id: row.lab_id,
    name: row.name,
    spec: row.spec,
    quantity: row.quantity ?? 1,
    status: row.status,
    description: row.description,
    img: row.img
  })
  // 回显已有图片
  fileList.value = row.img ? [{ name: row.img.split('/').pop(), url: row.img }] : []
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

  // 空字符串统一转 null（后端可空字段）
  const payload = { ...ruleForm }
  for (const k of ['spec', 'description']) {
    if (!payload[k]) payload[k] = null
  }

  try {
    submitLoading.value = true
    const res = isAdd.value ? await createEquipmentApi(payload) : await updateEquipmentApi(ruleForm.id, payload)
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
    const res = await getEquipmentPageList({
      'page': params.page,
      'page_size': params.pageSize,
      'keywords': params.keywords?.trim() || null,
      'lab_id': params.labId || null
    })
    if (res.code === 200) {
      tableData.value = res.data?.data ?? []
      total.value = res.data?.total ?? 0
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
  loadLabOptions()
})

</script>

<style scoped>
.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 400px;
}
</style>
