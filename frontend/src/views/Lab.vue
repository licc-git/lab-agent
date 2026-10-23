<template>
  <el-card style="max-width: 100%">
    <template #header>
      <div class="card-header">
        <span style="font-size: large;">实验室管理</span>
      </div>
    </template>
    <div class="input-group">
      <el-input v-model="params.keywords" :suffix-icon="Search" placeholder="支持名称/位置模糊搜索" clearable
        @keyup.enter="handleSearch" @clear="handleSearch"><template #prepend>关键词</template></el-input>
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
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="img" label="封面图" width="120">
        <template #default="{ row }">
          <el-image v-if="row.img" :src="row.img" fit="cover" style="width: 80px; height: 45px; border-radius: 4px;"
            :preview-src-list="[row.img]" preview-teleported hide-on-click-modal>
          </el-image>
          <span v-else>—</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" width="160" />
      <el-table-column prop="location" label="位置" width="150">
        <template #default="{ row }">{{ row.location || '—' }}</template>
      </el-table-column>
      <el-table-column sortable prop="capacity" label="容纳人数" width="100" />
      <el-table-column label="开放安排" min-width="220">
        <template #default="{ row }">
          <div>{{ formatOpenDays(row.open_days) }}</div>
          <div class="muted-text">{{ formatOpenHours(row) }}</div>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="简介" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">{{ row.description || '—' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'">
            {{ row.status === 1 ? '开放' : '关闭' }}
          </el-tag>
        </template>
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
  <el-dialog v-model="dialogVisible" :title="isAdd ? '新增实验室' : '编辑实验室'" width="500" destroy-on-close
    :close-on-click-modal="false">
    <el-form :model="ruleForm" ref="ruleFormRef" :rules="rules" label-width="auto" style="min-width: 300px;"
      label-position="left" status-icon>
      <el-form-item label="名 称" prop="name">
        <el-input v-model="ruleForm.name" placeholder="请输入实验室名称" maxlength="20" show-word-limit />
      </el-form-item>
      <el-form-item label="位 置" prop="location">
        <el-input v-model="ruleForm.location" placeholder="如：实验楼 A305" maxlength="50" />
      </el-form-item>
      <el-form-item label="容纳人数" prop="capacity">
        <el-input-number v-model="ruleForm.capacity" :min="0" :max="99" />
      </el-form-item>
      <el-form-item label="开放日" prop="open_days">
        <el-checkbox-group v-model="ruleForm.open_days" class="open-days-group">
          <el-checkbox v-for="day in weekdayOptions" :key="day.value" :value="day.value">
            {{ day.label }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      <el-form-item label="每日开放" prop="open_time">
        <div class="daily-hours">
          <el-time-picker v-model="ruleForm.open_time" format="HH:mm" value-format="HH:mm"
            placeholder="开始时间" />
          <span>至</span>
          <el-time-picker v-model="ruleForm.close_time" format="HH:mm" value-format="HH:mm"
            placeholder="结束时间" />
        </div>
      </el-form-item>
      <el-form-item label="简 介" prop="description">
        <el-input v-model="ruleForm.description" type="textarea" :rows="3" placeholder="实验室简介（选填）" maxlength="512"
          show-word-limit />
      </el-form-item>
      <el-form-item label="状 态" prop="status">
        <el-select v-model="ruleForm.status" placeholder="请选择状态">
          <el-option label="开 放" :value="1" />
          <el-option label="关 闭" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item label="封面图" prop="img">
        <el-upload ref="uploadRef" v-model:file-list="fileList" list-type="picture-card" accept="image/*" :limit="1"
          :http-request="handleUpload" :before-upload="checkImage" :on-remove="handleImgRemove"
          :on-exceed="handleExceed">
          <el-icon>
            <IconPicture />
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
import { createLabApi, deleteLabListApi, deleteLabApi, getLabPageList, updateLabApi } from '@/api/lab';
import { uploadFileApi } from '@/api/files';
import { reactive, ref, onMounted, computed, markRaw } from 'vue';
import { Search, Delete, Plus, RefreshLeft, Picture as IconPicture } from '@element-plus/icons-vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { cleanParams } from '@/utils/params';

const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: null,
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
const isQuery = computed(() => !params.keywords?.trim())
const handleSearch = () => {
  params.page = 1
  loadData()
}
// 重置
const handleReset = () => {
  params.keywords = null
  params.page = 1
  loadData()
}

const weekdayOptions = [
  { value: 0, label: '周一' },
  { value: 1, label: '周二' },
  { value: 2, label: '周三' },
  { value: 3, label: '周四' },
  { value: 4, label: '周五' },
  { value: 5, label: '周六' },
  { value: 6, label: '周日' }
]

const formatOpenDays = (days) => {
  if (!Array.isArray(days) || days.length === 0) return '未设置开放日'
  return weekdayOptions.filter(day => days.includes(day.value)).map(day => day.label).join('、')
}

const formatOpenHours = (row) => {
  if (!row.open_time || !row.close_time) return '每日时间未设置'
  return `每日 ${row.open_time.slice(0, 5)} - ${row.close_time.slice(0, 5)}`
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定删除实验室 ${row?.name} ？`,
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
    const res = await deleteLabApi(row.id)
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
      `确定删除选中的 ${count} 个实验室 ？`,
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
    const res = await deleteLabListApi({ ids })
    if (res.code === 200) {
      ElMessage.success(res.message || `成功删除 ${count} 个实验室`)
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
  name: '',
  location: null,
  capacity: 0,
  open_time: '08:00',
  close_time: '22:00',
  open_days: [0, 1, 2, 3, 4],
  description: null,
  img: null,
  status: 1
})
const ruleFormRef = ref()
// 封面图上传
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
// 开放日和每日时段需要成组配置，结束时间应晚于开始时间。
const validateSchedule = (rule, value, callback) => {
  if (ruleForm.open_days.length === 0) {
    callback(new Error('请至少选择一个开放日'))
  } else if (!ruleForm.open_time || !ruleForm.close_time) {
    callback(new Error('请设置每日开放的开始和结束时间'))
  } else if (ruleForm.close_time <= ruleForm.open_time) {
    callback(new Error('每日结束时间必须晚于开始时间'))
  } else {
    callback()
  }
}
const rules = {
  name: [
    { required: true, message: '请输入实验室名称', trigger: 'blur' },
    { min: 1, max: 20, message: '名称长度不能大于20', trigger: 'blur' }
  ],
  location: [
    { min: 5, max: 50, message: '位置长度不能小于5或大于50', trigger: 'blur' }
  ],
  open_days: [{ validator: validateSchedule, trigger: 'change' }],
  open_time: [{ validator: validateSchedule, trigger: 'change' }],
  close_time: [{ validator: validateSchedule, trigger: 'change' }],
  description: [
    { max: 512, message: '简介长度不能大于512', trigger: 'blur' }
  ],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}
const resetForm = () => {
  Object.assign(ruleForm, {
    id: null,
    name: '',
    location: null,
    capacity: 0,
    open_time: '08:00',
    close_time: '22:00',
    open_days: [0, 1, 2, 3, 4],
    description: null,
    img: null,
    status: 1
  })
  fileList.value = []
}
const handleEdit = (row) => {
  isAdd.value = false
  resetForm()
  Object.assign(ruleForm, {
    id: row.id,
    name: row.name,
    location: row.location,
    capacity: row.capacity ?? 0,
    open_time: row.open_time ? row.open_time.slice(0, 5) : null,
    close_time: row.close_time ? row.close_time.slice(0, 5) : null,
    open_days: row.open_days ?? [0, 1, 2, 3, 4],
    description: row.description,
    img: row.img,
    status: row.status
  })
  // 回显已有封面
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

  // 空字符串会被后端校验拒绝（如 location min_length=5）：选填字段空值统一转 null
  const payload = { ...ruleForm }
  for (const k of ['location', 'description']) {
    if (!payload[k]) payload[k] = null
  }

  try {
    submitLoading.value = true
    const res = isAdd.value ? await createLabApi(payload) : await updateLabApi(ruleForm.id, payload)
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
    const res = await getLabPageList(cleanParams({
      'page': params.page,
      'page_size': params.pageSize,
      'keywords': params.keywords?.trim()
    }))
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
.open-days-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0 8px;
}

.open-days-group :deep(.el-checkbox) {
  margin-right: 8px;
}

.daily-hours {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
}

.daily-hours :deep(.el-date-editor) {
  min-width: 0;
  flex: 1;
}

.muted-text {
  color: #909399;
  font-size: 12px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 400px;
}
</style>
