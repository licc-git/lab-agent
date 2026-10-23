<template>
  <main class="lab-equipment-page">
    <el-card v-loading="labLoading" class="lab-summary" shadow="never">
      <div class="page-heading">
        <div>
          <h1>{{ lab.name || '实验室设备' }}</h1>
          <p>实验室信息与设备清单</p>
        </div>
        <div class="page-actions">
          <el-button type="primary" @click="handleBook">预约实验室</el-button>
          <el-button @click="router.push({ name: 'LabList' })">返回实验室列表</el-button>
        </div>
      </div>

      <div class="lab-details">
        <div class="detail-item">
          <span class="detail-label">位置</span>
          <span class="detail-value">{{ lab.location || '未知' }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">容纳人数</span>
          <span class="detail-value">{{ lab.capacity ?? '—' }} 人</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">开放日</span>
          <span class="detail-value">{{ formatOpenDays(lab.open_days) }}</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">每日开放时间</span>
          <span class="detail-value">{{ formatOpenHours(lab) }}</span>
        </div>
        <div class="detail-item description-item">
          <span class="detail-label">实验室介绍</span>
          <span class="detail-value">{{ lab.description || '暂无介绍' }}</span>
        </div>
      </div>
    </el-card>

    <el-card class="equipment-card" shadow="never">
      <div class="section-heading">
        <div>
          <h2>设备清单</h2>
          <p>共 {{ equipmentTotal }} 件设备</p>
        </div>
      </div>

      <el-table
        v-loading="equipmentLoading"
        :data="equipmentData"
        stripe
        class="equipment-table"
        empty-text="暂无设备数据"
      >
        <el-table-column prop="id" label="ID" width="76" />
        <el-table-column prop="img" label="图片" width="112">
          <template #default="{ row }">
            <el-image
              v-if="row.img"
              :src="row.img"
              :preview-src-list="[row.img]"
              fit="cover"
              preview-teleported
              hide-on-click-modal
              class="equipment-image"
            />
            <span v-else class="muted-text">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="设备名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="spec" label="型号规格" min-width="130">
          <template #default="{ row }">{{ row.spec || '—' }}</template>
        </el-table-column>
        <el-table-column sortable prop="quantity" label="数量" width="88" />
        <el-table-column prop="status" label="状态" width="92">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'warning'">
              {{ row.status === 1 ? '正常' : '维修' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="说明" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.description || '—' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" plain bg :disabled="row.status === 0" @click="handleBook(row)">预约</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="equipmentTotal > 0"
        v-model:current-page="params.page"
        v-model:page-size="params.pageSize"
        :total="equipmentTotal"
        :pager-count="5"
        :page-sizes="[10, 20, 50, 100]"
        background
        class="equipment-pagination"
        layout="total, sizes, prev, pager, next"
        @current-change="handleCurrentChange"
        @size-change="handleSizeChange"
      />
    </el-card>
  </main>
  <ReservationDialog 
  :visibe="reserveVisible"
  :lab-id="currentLab?.id"
  :lab-name="currentLab?.name"
  :equipment-id="currentEquip?.id"
  :equipment-name="currentEquip?.name"
  @update-visibe="reserveVisible = false"
  />
</template>

<script setup>
import { getEquipmentPageList } from '@/api/equipment'
import { getLabId } from '@/api/lab'
import { cleanParams } from '@/utils/params'
import { ElMessage } from 'element-plus'
import { reactive, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import ReservationDialog from '@/components/ReservationDialog.vue'

const route = useRoute()
const router = useRouter()

const params = reactive({
  page: 1,
  pageSize: 10,
  labId: null
})

const lab = ref({})
const labLoading = ref(false)
const equipmentData = ref([])
const equipmentTotal = ref(0)
const equipmentLoading = ref(false)

const weekdayLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
const formatOpenDays = (days) => {
  if (!Array.isArray(days) || days.length === 0) return '未设置'
  return days.map(day => weekdayLabels[day]).filter(Boolean).join('、') || '未设置'
}
const formatOpenHours = (lab) => {
  if (!lab.open_time || !lab.close_time) return '未设置'
  return `${lab.open_time.slice(0, 5)} 至 ${lab.close_time.slice(0, 5)}`
}

const loadLab = async (labId) => {
  labLoading.value = true
  lab.value = {}
  try {
    const res = await getLabId(labId)
    if (res.code === 200) {
      lab.value = res.data ?? {}
    }
  } finally {
    labLoading.value = false

  }
}

const loadEquipment = async () => {
  const labId = params.labId
  equipmentLoading.value = true
  equipmentData.value = []
  equipmentTotal.value = 0

  try {
    const res = await getEquipmentPageList(cleanParams({
      page: params.page,
      page_size: params.pageSize,
      lab_id: labId
    }))
    if (res.code === 200) {
      equipmentData.value = res.data?.data ?? []
      equipmentTotal.value = res.data?.total ?? 0
    }
  } finally {
    equipmentLoading.value = false
  }
}

const handleSizeChange = () => {
  params.page = 1
  void loadEquipment()
}

const handleCurrentChange = () => {
  void loadEquipment()
}

// 弹窗
const reserveVisible = ref(false)
const currentLab = ref(null)
const currentEquip = ref(null)
const handleBook = (row) => {
  reserveVisible.value = true
  currentLab.value = lab.value
  currentEquip.value = row ?? null
}


watch(
  () => route.params.id,
  (routeId) => {
    const labId = Number(routeId)
    params.page = 1

    if (!Number.isInteger(labId) || labId < 1) {
      labRequestId += 1
      equipmentRequestId += 1
      lab.value = {}
      equipmentData.value = []
      equipmentTotal.value = 0
      labLoading.value = false
      equipmentLoading.value = false
      ElMessage.error('实验室编号无效')
      return
    }

    params.labId = labId
    void Promise.allSettled([loadLab(labId), loadEquipment()])
  },
  { immediate: true }
)
</script>

<style scoped>
.lab-equipment-page {
  display: grid;
  gap: 16px;
}

.lab-summary,
.equipment-card {
  min-width: 0;
  border: 0;
}

.page-heading,
.section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-heading h1,
.section-heading h2 {
  margin: 0;
  color: #303133;
}

.page-heading h1 {
  font-size: 21px;
  line-height: 1.4;
}

.page-heading p,
.section-heading p {
  margin: 5px 0 0;
  color: #909399;
  font-size: 13px;
}

.page-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
}

.page-actions .el-button {
  margin-left: 0;
}

.lab-details {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px 24px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--el-border-color-lighter);
}

.detail-item {
  display: grid;
  gap: 6px;
  min-width: 0;
}

.detail-label {
  color: #909399;
  font-size: 13px;
}

.detail-value {
  overflow-wrap: anywhere;
  color: #303133;
  font-size: 14px;
  line-height: 1.6;
}

.description-item {
  grid-column: 1 / -1;
}

.section-heading {
  align-items: center;
  margin-bottom: 16px;
}

.section-heading h2 {
  font-size: 17px;
}

.equipment-image {
  display: block;
  width: 72px;
  height: 48px;
  border-radius: 4px;
  cursor: zoom-in;
}

.muted-text {
  color: #a8abb2;
}

.equipment-pagination {
  justify-content: flex-end;
  margin-top: 18px;
}

@media (max-width: 768px) {
  .lab-details {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 600px) {
  .page-heading {
    flex-direction: column;
  }

  .page-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .lab-details {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }

  .description-item {
    grid-column: auto;
  }

  .equipment-pagination {
    justify-content: center;
    flex-wrap: wrap;
    height: auto;
    row-gap: 10px;
  }
}
</style>
