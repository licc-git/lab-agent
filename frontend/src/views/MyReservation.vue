<template>
  <el-card style="max-width: 100%">
    <template #header>
      <div class="card-header">
        <span style="font-size: large;">实验室管理</span>
      </div>
    </template>
    <div class="input-group">
      <el-input v-model="params.keywords" :suffix-icon="Search" placeholder="支持实验室/设备模糊搜索" clearable
        @keyup.enter="handleSearch" @clear="handleSearch"><template #prepend>关键词</template></el-input>
      <el-button type="primary" :disabled="isQuery" :icon="Search" @click="handleSearch">查询</el-button>
      <el-button :icon="RefreshLeft" style="margin-left: 8px;" @click="handleReset">重置</el-button>
    </div>
  </el-card>
  <el-card style="max-width: 100%; margin-top: 1rem; padding: 0.25rem 1rem;">
    <el-table :data="tableData" stripe max-height="800" v-loading="loading" style="width: 100%"
      :header-cell-style="{ background: '#263445', color: '#cfd7e1', fontWeight: 'bold' }">
      <el-table-column prop="id" label="ID" width="100" />
      <el-table-column prop="reserve_type" label="预约类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.reserve_type === '实验室' ? 'success' : 'warning'">
            {{ row.reserve_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="lab_name" label="实验室" width="100" />
      <el-table-column prop="equipment_name" label="设备" width="100" />
      <el-table-column prop="reserve_date" label="日期" width="100" />
      <el-table-column show-overflow-tooltip label="预约时段" width="180">
        <template #default="{ row }">{{ row.start_time }}-{{ row.end_time }}</template>
      </el-table-column>
      <el-table-column prop="remark" show-overflow-tooltip label="说明" width="180" />
      <el-table-column fixed="right" prop="status" label="预约状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 0 ? 'danger' : row.status === 1 ? 'success' : row.status === 2 ? 'warning' : 'info'">
            {{ row.status === 0 ? '待审核' : row.status === 1 ? '已通过' : row.status === 2 ? '已拒绝' : row.status === 3 ? '已取消' : '已过期' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column fixed="right" label="审核预约" align="right">
        <template #default="{ row }">
          <el-button v-if="row.status === 0" type="primary" size="small" plain bg @click="handleCancel(row)">取消</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div style="margin-top: 1.5rem; display: flex; justify-content: flex-end;">
      <el-pagination background layout="total, ->, prev, pager, next, ->, sizes" :total="total" :pager-count="5"
        :page-sizes="[10, 20, 50, 100]" v-model:page-size="params.pageSize" v-model:current-page="params.page"
        @current-change="handleCurrentChange" @size-change="handleSizeChange" />
    </div>
  </el-card>
</template>


<script setup>

import { cancelReservationApi, getReservationListApi } from '@/api/reservation';
import { reactive, ref, onMounted, computed } from 'vue';
import { Search, RefreshLeft } from '@element-plus/icons-vue';
import { cleanParams } from '@/utils/params';
import { ElMessage, ElMessageBox } from 'element-plus';


// 查询参数
const params = reactive({
  page: 1,
  pageSize: 10,
  keywords: null,
})

// 分页查询
const handleSizeChange = () => {
  params.page = 1
  loadData()
}
const handleCurrentChange = () => {
  loadData()
}
// 重置
const handleReset = () => {
  params.keywords = null
  params.page = 1
  loadData()
}

// 搜索查询
const isQuery = computed(() => !params.keywords?.trim())
const handleSearch = () => {
  params.page = 1
  loadData()
}
// 审核预约
const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm(`确定取消你的预约？`, '预约取消', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      closeOnClickModal: false,
      type: 'warning',
    })
  } catch {
    return
  }

  try {
    const res = await cancelReservationApi(row.id)
    if (res.code === 200) {
      ElMessage.success("取消成功")
      loadData()
    }
  } finally { }
}

// 加载数据
const tableData = ref([])
const loading = ref(false)
const total = ref(0)

const loadData = async () => {
  loading.value = true
  try {
    const res = await getReservationListApi(cleanParams({
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
.input-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 500px;
}
</style>