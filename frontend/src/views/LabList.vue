<template>
  <el-card style="max-width: 100%">
    <template #header>
      <div class="card-header">
        <span style="font-size: large;">实验室列表</span>
      </div>
    </template>
    <div class="filter-toolbar">
      <el-input v-model="params.keywords" class="keyword-filter" :suffix-icon="Search" placeholder="支持名称/位置模糊搜索"
        clearable maxlength="50" @keyup.enter="handleSearch" @clear="handleSearch">
        <template #prepend>关键字</template>
      </el-input>
      <el-select v-model="params.status" class="status-filter" clearable placeholder="选择实验室状态" @clear="handleSearch">
        <el-option label="开放" :value="1" />
        <el-option label="关闭" :value="0" />
      </el-select>
      <div class="filter-actions">
        <el-button type="primary" :icon="Search" @click="handleSearch" :disabled="!isQuery">查询</el-button>
        <el-button type="danger" :icon="RefreshLeft" @click="handleReset">重置</el-button>
      </div>
    </div>
  </el-card>
  <div class="lab-grid">
    <el-row :gutter="16">
      <el-col v-for="row in tableData" :key="row.id" :xs="24" :sm="12" :md="8" :lg="6" :xl="3">
        <el-card class="lab-card" shadow="hover">
          <div class="lab-cover">
            <el-image v-if="row.img" :src="row.img" :preview-src-list="[row.img]" :alt="`${row.name}封面图`" fit="cover"
              hide-on-click-modal close-on-press-escape preview-teleported class="cover-image" />
            <div v-else class="cover-placeholder">暂无封面图</div>
            <el-tag class="status-tag" :type="row.status === 1 ? 'success' : 'info'">
              {{ row.status === 1 ? '开放中' : '暂未开放' }}
            </el-tag>
          </div>

          <div class="lab-content">
            <h3 class="lab-name" :title="row.name">{{ row.name || '未命名实验室' }}</h3>
            <div class="lab-info">
              <div class="info-row">
                <el-icon>
                  <Location />
                </el-icon>
                <span>{{ row.location || '位置未填写' }}</span>
              </div>
              <div class="info-row">
                <el-icon>
                  <User />
                </el-icon>
                <span>容纳人数：{{ row.capacity ?? '—' }} 人</span>
              </div>
              <div class="info-row">
                <el-icon>
                  <Clock />
                </el-icon>
                <span>{{ formatOpenSchedule(row) }}</span>
              </div>
            </div>

            <div class="lab-actions">
              <el-button type="primary" plain @click="handleView(row)">
                <el-icon>
                  <View />
                </el-icon>
                查看实验室
              </el-button>
              <el-button type="primary" @click="handleBook(row)" :disabled="row.status !== 1">
                <el-icon>
                  <Calendar />
                </el-icon>
                预约
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-empty v-if="tableData.length === 0" description="暂无实验室数据" />
    <el-pagination v-model:current-page="params.page" v-model:page-size="params.pageSize" :pager-count="5" background
      layout="->, total, prev, pager, next, sizes" :page-sizes="[10, 20, 50, 100]" :total="total"
      @size-change="handleSizeChange" @current-change="handleCurrentChange" />
  </div>
  <ReservationDialog v-model:visibe="reserveVisible" :lab-id="currentLab?.id" :lab-name="currentLab?.name"
    @update-visibe="colseVisibe" />
</template>


<script setup>
import { getLabPageList } from '@/api/lab';
import { cleanParams } from '@/utils/params';
import { Search, RefreshLeft, Location, User, Clock, View, Calendar } from '@element-plus/icons-vue';
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import ReservationDialog from '@/components/ReservationDialog.vue';

const router = useRouter();
// 查询参数
const isQuery = computed(() => !(!params.keywords.trim() && !(params.status == 1 || params.status == 0)))
const params = reactive({
  page: 1,
  pageSize: 10,
  status: '',
  keywords: ''
})
const handleSearch = () => {
  if (isQuery.value) {
    params.page = 1
    loadData()
  }
}
const handleReset = () => {
  params.status = '',
    params.keywords = ''
  params.page = 1
  loadData()
}

const weekdayLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const formatOpenSchedule = (row) => {
  const days = Array.isArray(row.open_days)
    ? row.open_days.map(day => weekdayLabels[day]).filter(Boolean).join('、')
    : ''
  const hours = row.open_time && row.close_time
    ? `${row.open_time.slice(0, 5)}-${row.close_time.slice(0, 5)}`
    : '时间未设置'
  return `${days || '开放日未设置'} ${hours}`
}

const handleSizeChange = (val) => {
  params.pageSize = val
  params.page = 1
  loadData()
}

const handleCurrentChange = (val) => {
  params.page = val
  loadData()
}

const handleView = (row) => {
  router.push({ name: 'LabEquipment', params: { id: row.id } })
}

// 预约弹窗
const reserveVisible = ref(false)
const currentLab = ref(null)
const handleBook = (row) => {
  reserveVisible.value = true
  currentLab.value = row
}

const colseVisibe = () => {
  reserveVisible.value = false
}

// 数据加载
const tableData = ref([])
const total = ref(0)

const loadData = async () => {
  try {
    const res = await getLabPageList(cleanParams({
      'page': params.page,
      'page_size': params.pageSize,
      'status': params.status,
      'keywords': params.keywords?.trim()
    }))
    if (res.code === 200) {
      tableData.value = res.data?.data ?? []
      total.value = res.data?.total ?? 0
    }
  } finally { }
}

onMounted(loadData)

</script>

<style scoped>
.lab-grid {
  margin-top: 16px;
}

.lab-card {
  margin-bottom: 16px;
  overflow: hidden;
}

.lab-cover {
  position: relative;
  aspect-ratio: 16 / 9;
  overflow: hidden;
  background: #f3f5f8;
}

.cover-image {
  display: block;
  width: 100%;
  height: 100%;
}

.cover-placeholder {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  color: #909399;
  font-size: 14px;
}

.status-tag {
  position: absolute;
  top: 10px;
  right: 10px;
}

.lab-content {
  padding-top: 14px;
}

.lab-name {
  overflow: hidden;
  margin: 0 0 12px;
  color: #303133;
  font-size: 17px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lab-info {
  display: grid;
  gap: 10px;
  min-height: 112px;
  color: #606266;
  font-size: 13px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  min-width: 0;
  padding-bottom: 0;
}

.info-row .el-icon {
  flex: 0 0 auto;
  margin-top: 2px;
  color: #909399;
}

.info-row span {
  overflow-wrap: anywhere;
}

.lab-actions {
  display: flex;
  gap: 5px;
  margin-top: 16px;
}

.lab-actions .el-button {
  flex: 1;
  min-width: 0;
  margin-left: 0;
}

.lab-actions .el-button :deep(.el-icon) {
  margin-right: 1px;
}

.filter-toolbar {
  display: grid;
  grid-template-columns: 320px 220px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
}

.keyword-filter,
.status-filter {
  width: 100%;
  min-width: 0;
}

.filter-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 900px) {
  .filter-toolbar {
    grid-template-columns: minmax(0, 1fr) minmax(160px, 1fr);
  }

  .filter-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .filter-toolbar {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  .keyword-filter,
  .filter-actions {
    grid-column: 1 / -1;
  }
}

@media (max-width: 480px) {
  .filter-toolbar {
    grid-template-columns: minmax(0, 1fr);
  }

  .status-filter {
    grid-column: 1;
  }

  .filter-actions {
    justify-content: stretch;
  }

  .filter-actions :deep(.el-button) {
    flex: 1;
    margin-left: 0;
  }
}
</style>
