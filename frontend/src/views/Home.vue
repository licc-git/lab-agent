<template>
  <div class="home-page">
    <section class="welcome-panel">
      <div class="welcome-copy">
        <div class="welcome-eyebrow">SMART LAB · MANAGEMENT PLATFORM</div>
        <h1>{{ greeting }}，{{ displayName }}</h1>
        <p>欢迎使用智能实验室预约系统，快速查看实验室动态并处理日常事务。</p>
        <div class="welcome-meta">
          <el-icon><Calendar /></el-icon>
          <span>{{ todayText }}</span>
          <el-tag effect="plain" round>{{ isAdmin ? '管理员' : '学生' }}</el-tag>
        </div>
      </div>
      <div class="welcome-art" aria-hidden="true">
        <div class="art-orbit orbit-one"></div>
        <div class="art-orbit orbit-two"></div>
        <div class="art-core"><el-icon><Monitor /></el-icon></div>
        <div class="art-dot dot-one"></div>
        <div class="art-dot dot-two"></div>
      </div>
    </section>

    <el-alert
      v-if="loadError"
      class="load-error"
      :title="loadError"
      type="error"
      show-icon
      :closable="false"
    />

    <section class="stats-grid" aria-label="数据概览">
      <el-card v-for="stat in stats" :key="stat.label" class="stat-card" shadow="hover">
        <div class="stat-topline">
          <span class="stat-label">{{ stat.label }}</span>
          <span class="stat-icon" :class="`tone-${stat.tone}`">
            <el-icon><component :is="stat.icon" /></el-icon>
          </span>
        </div>
        <div class="stat-value">{{ loading ? '—' : stat.value }}</div>
        <div class="stat-caption">{{ stat.caption }}</div>
      </el-card>
    </section>

    <section class="content-grid">
      <el-card class="recent-card" shadow="never">
        <template #header>
          <div class="section-heading">
            <div>
              <h2>最近预约</h2>
              <p>{{ isAdmin ? '查看系统中最新提交的预约申请' : '跟进你的预约申请和审核进度' }}</p>
            </div>
            <el-button text type="primary" @click="goTo(isAdmin ? '/manager/audit-reservation' : '/manager/my-reservation')">
              查看全部 <el-icon class="button-arrow"><ArrowRight /></el-icon>
            </el-button>
          </div>
        </template>

        <el-table v-loading="loading" :data="recentReservations" class="reservation-table">
          <el-table-column prop="lab_name" label="实验室" min-width="130" show-overflow-tooltip />
          <el-table-column label="预约内容" min-width="130" show-overflow-tooltip>
            <template #default="{ row }">
              {{ row.equipment_name || '实验室使用' }}
            </template>
          </el-table-column>
          <el-table-column label="预约时间" min-width="150">
            <template #default="{ row }">
              <span class="reservation-date">{{ row.reserve_date }}</span>
              <span class="reservation-time">{{ formatTime(row.start_time) }}–{{ formatTime(row.end_time) }}</span>
            </template>
          </el-table-column>
          <el-table-column v-if="isAdmin" prop="user_name" label="申请人" min-width="90" show-overflow-tooltip />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="reservationStatusType(row.status)" effect="light" round>
                {{ reservationStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <template #empty>
            <el-empty description="还没有预约记录" :image-size="72" />
          </template>
        </el-table>
      </el-card>

      <el-card class="quick-card" shadow="never">
        <template #header>
          <div class="section-heading">
            <div>
              <h2>快捷入口</h2>
              <p>常用功能，一键直达</p>
            </div>
          </div>
        </template>
        <div class="quick-list">
          <button
            v-for="item in shortcuts"
            :key="item.label"
            class="quick-item"
            type="button"
            @click="goTo(item.path)"
          >
            <span class="quick-icon" :class="`tone-${item.tone}`">
              <el-icon><component :is="item.icon" /></el-icon>
            </span>
            <span class="quick-copy">
              <strong>{{ item.label }}</strong>
              <small>{{ item.description }}</small>
            </span>
            <el-icon class="quick-arrow"><ArrowRight /></el-icon>
          </button>
        </div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  Calendar,
  ChatDotRound,
  Clock,
  Collection,
  DataAnalysis,
  House,
  Monitor,
  Tickets,
  User,
} from '@element-plus/icons-vue'
import { getEquipmentPageList } from '@/api/equipment'
import { getLabPageList } from '@/api/lab'
import { getReservationListApi } from '@/api/reservation'
import { useUser } from '@/utils/user'

const router = useRouter()
const { userInfo } = useUser()
const isAdmin = computed(() => userInfo.value?.role === 'admin')
const displayName = computed(() => userInfo.value?.name || userInfo.value?.username || '用户')
const now = new Date()
const todayText = new Intl.DateTimeFormat('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long',
}).format(now)
const greeting = computed(() => {
  const hour = now.getHours()
  if (hour < 11) return '早上好'
  if (hour < 13) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
})

const loading = ref(false)
const loadError = ref('')
const recentReservations = ref([])
const overview = ref({
  reservationTotal: 0,
  pendingReservations: 0,
  approvedReservations: 0,
  labTotal: 0,
  openLabs: 0,
  equipmentTotal: 0,
})

const stats = computed(() => {
  if (isAdmin.value) {
    return [
      { label: '实验室总数', value: overview.value.labTotal, caption: '纳入系统管理', icon: House, tone: 'blue' },
      { label: '当前开放', value: overview.value.openLabs, caption: '可供预约使用', icon: Monitor, tone: 'green' },
      { label: '待审核预约', value: overview.value.pendingReservations, caption: '等待管理员处理', icon: Clock, tone: 'orange' },
      { label: '设备总数', value: overview.value.equipmentTotal, caption: '已登记实验设备', icon: Collection, tone: 'purple' },
    ]
  }

  return [
    { label: '我的预约', value: overview.value.reservationTotal, caption: '累计提交的预约申请', icon: Tickets, tone: 'blue' },
    { label: '待审核', value: overview.value.pendingReservations, caption: '等待审核结果', icon: Clock, tone: 'orange' },
    { label: '已通过', value: overview.value.approvedReservations, caption: '审核通过的预约', icon: DataAnalysis, tone: 'green' },
    { label: '开放实验室', value: overview.value.openLabs, caption: '当前可预约使用', icon: House, tone: 'purple' },
  ]
})

const shortcuts = computed(() => {
  if (isAdmin.value) {
    return [
      { label: '预约审核', description: '处理待审核的预约申请', path: '/manager/audit-reservation', icon: Tickets, tone: 'orange' },
      { label: '实验室管理', description: '维护实验室信息与开放状态', path: '/manager/lab', icon: House, tone: 'blue' },
      { label: '设备管理', description: '查看和维护实验室设备', path: '/manager/equ', icon: Monitor, tone: 'green' },
      { label: '用户管理', description: '管理系统用户与账号', path: '/manager/user', icon: User, tone: 'purple' },
    ]
  }

  return [
    { label: '实验室列表', description: '浏览实验室并发起预约', path: '/manager/lab_list', icon: House, tone: 'blue' },
    { label: '我的预约', description: '查看预约详情与审核进度', path: '/manager/my-reservation', icon: Tickets, tone: 'orange' },
    { label: 'AI 助手', description: '咨询实验室与设备相关问题', path: '/manager/ai-chat', icon: ChatDotRound, tone: 'green' },
  ]
})

const requireSuccess = (response) => {
  if (response?.code !== 200) {
    throw new Error(response?.message || '首页数据加载失败')
  }
  return response.data
}

const loadDashboard = async () => {
  loading.value = true
  loadError.value = ''
  try {
    if (isAdmin.value) {
      const [reservations, pending, labs, openLabs, equipment] = await Promise.all([
        getReservationListApi({ page: 1, page_size: 5 }),
        getReservationListApi({ page: 1, page_size: 1, status: 0 }),
        getLabPageList({ page: 1, page_size: 10 }),
        getLabPageList({ page: 1, page_size: 10, status: 1 }),
        getEquipmentPageList({ page: 1, page_size: 1 }),
      ])
      const reservationData = requireSuccess(reservations)
      overview.value = {
        ...overview.value,
        pendingReservations: requireSuccess(pending)?.total ?? 0,
        labTotal: requireSuccess(labs)?.total ?? 0,
        openLabs: requireSuccess(openLabs)?.total ?? 0,
        equipmentTotal: requireSuccess(equipment)?.total ?? 0,
      }
      recentReservations.value = reservationData?.data ?? []
      return
    }

    const [reservations, pending, approved, openLabs] = await Promise.all([
      getReservationListApi({ page: 1, page_size: 5 }),
      getReservationListApi({ page: 1, page_size: 1, status: 0 }),
      getReservationListApi({ page: 1, page_size: 1, status: 1 }),
      getLabPageList({ page: 1, page_size: 10, status: 1 }),
    ])
    const reservationData = requireSuccess(reservations)
    overview.value = {
      ...overview.value,
      reservationTotal: reservationData?.total ?? 0,
      pendingReservations: requireSuccess(pending)?.total ?? 0,
      approvedReservations: requireSuccess(approved)?.total ?? 0,
      openLabs: requireSuccess(openLabs)?.total ?? 0,
    }
    recentReservations.value = reservationData?.data ?? []
  } catch {
    loadError.value = '首页数据加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

const goTo = (path) => router.push(path)

const formatTime = (time) => (time ? time.slice(0, 5) : '--:--')

const reservationStatusLabel = (status) => ({
  0: '待审核',
  1: '已通过',
  2: '已拒绝',
  3: '已取消',
  4: '已过期',
}[status] || '未知状态')

const reservationStatusType = (status) => ({
  0: 'warning',
  1: 'success',
  2: 'danger',
  3: 'info',
  4: 'info',
}[status] || 'info')

onMounted(loadDashboard)
</script>

<style scoped>
.home-page {
  display: grid;
  gap: 20px;
  max-width: 1440px;
  margin: 0 auto;
}

.welcome-panel {
  position: relative;
  display: flex;
  min-height: 208px;
  align-items: center;
  overflow: hidden;
  padding: 32px 40px;
  border-radius: 16px;
  color: #fff;
  background: linear-gradient(112deg, #183c73 0%, #2464a5 58%, #3885bb 100%);
}

.welcome-copy {
  position: relative;
  z-index: 1;
  max-width: 680px;
}

.welcome-eyebrow {
  margin-bottom: 12px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 2px;
}

.welcome-copy h1 {
  margin: 0 0 10px;
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 600;
  letter-spacing: 1px;
}

.welcome-copy p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  line-height: 1.7;
}

.welcome-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
}

.welcome-meta :deep(.el-tag) {
  margin-left: 4px;
  border-color: rgba(255, 255, 255, 0.35);
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.welcome-art {
  position: absolute;
  top: 50%;
  right: 9%;
  width: 190px;
  height: 190px;
  transform: translateY(-50%);
}

.art-orbit {
  position: absolute;
  inset: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
}

.orbit-two {
  inset: 28px;
  border-style: dashed;
  transform: rotate(-28deg) scaleX(1.35);
}

.art-core {
  position: absolute;
  inset: 54px;
  display: grid;
  place-items: center;
  border: 1px solid rgba(255, 255, 255, 0.35);
  border-radius: 50%;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 0 40px rgba(255, 255, 255, 0.12);
  font-size: 42px;
}

.art-dot {
  position: absolute;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #9ee4ff;
  box-shadow: 0 0 14px rgba(158, 228, 255, 0.9);
}

.dot-one {
  top: 28px;
  right: 36px;
}

.dot-two {
  bottom: 34px;
  left: 20px;
  width: 6px;
  height: 6px;
}

.load-error {
  border-radius: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  border: 0;
  border-radius: 12px;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label {
  color: #606b7a;
  font-size: 14px;
}

.stat-icon,
.quick-icon {
  display: grid;
  flex: 0 0 auto;
  width: 42px;
  height: 42px;
  place-items: center;
  border-radius: 12px;
  font-size: 20px;
}

.tone-blue {
  color: #3478d4;
  background: #eaf2ff;
}

.tone-green {
  color: #20a477;
  background: #e7f7f0;
}

.tone-orange {
  color: #df8b20;
  background: #fff4e3;
}

.tone-purple {
  color: #8260c9;
  background: #f1edff;
}

.stat-value {
  margin-top: 15px;
  color: #253247;
  font-size: 30px;
  font-weight: 650;
  line-height: 1.2;
}

.stat-caption {
  margin-top: 8px;
  color: #9aa3af;
  font-size: 12px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(260px, 1fr);
  gap: 16px;
  align-items: stretch;
}

.recent-card,
.quick-card {
  min-width: 0;
  border: 0;
  border-radius: 12px;
}

.recent-card :deep(.el-card__header),
.quick-card :deep(.el-card__header) {
  padding: 20px 22px 16px;
  border-bottom: 1px solid #f0f2f5;
}

.recent-card :deep(.el-card__body) {
  padding: 0 22px 16px;
}

.quick-card :deep(.el-card__body) {
  padding: 4px 18px 12px;
}

.section-heading {
  display: flex;
  min-height: 42px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.section-heading h2 {
  color: #283548;
  font-size: 16px;
  font-weight: 650;
}

.section-heading p {
  margin-top: 6px;
  color: #9aa3af;
  font-size: 12px;
}

.button-arrow {
  margin-left: 4px;
}

.reservation-table {
  width: 100%;
}

.reservation-table :deep(.el-table__header th) {
  height: 44px;
  color: #748094;
  background: #fafbfd;
  font-weight: 500;
}

.reservation-date,
.reservation-time {
  display: block;
}

.reservation-date {
  color: #3d4858;
}

.reservation-time {
  margin-top: 4px;
  color: #9aa3af;
  font-size: 12px;
}

.quick-list {
  display: grid;
}

.quick-item {
  display: flex;
  width: 100%;
  align-items: center;
  gap: 12px;
  padding: 14px 4px;
  border: 0;
  border-bottom: 1px solid #f1f3f6;
  text-align: left;
  background: transparent;
  cursor: pointer;
  transition: background-color 0.18s ease;
}

.quick-item:last-child {
  border-bottom: 0;
}

.quick-item:hover {
  background: #f8faff;
}

.quick-icon {
  width: 40px;
  height: 40px;
  border-radius: 11px;
  font-size: 18px;
}

.quick-copy {
  display: grid;
  flex: 1;
  gap: 5px;
  min-width: 0;
}

.quick-copy strong {
  overflow: hidden;
  color: #3d4858;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-copy small {
  overflow: hidden;
  color: #9aa3af;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.quick-arrow {
  color: #b4bdc8;
  font-size: 14px;
}

@media (max-width: 1100px) {
  .content-grid {
    grid-template-columns: minmax(0, 1.4fr) minmax(240px, 1fr);
  }

  .welcome-art {
    right: 4%;
  }
}

@media (max-width: 850px) {
  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .home-page {
    gap: 14px;
  }

  .welcome-panel {
    min-height: 190px;
    padding: 24px;
  }

  .welcome-art {
    right: -88px;
    opacity: 0.45;
  }

  .welcome-copy p {
    max-width: 90%;
  }

  .stats-grid {
    gap: 10px;
  }

  .stat-card :deep(.el-card__body) {
    padding: 16px;
  }

  .stat-icon {
    width: 36px;
    height: 36px;
    font-size: 17px;
  }

  .stat-value {
    margin-top: 12px;
    font-size: 26px;
  }

  .recent-card :deep(.el-card__header),
  .quick-card :deep(.el-card__header) {
    padding-right: 16px;
    padding-left: 16px;
  }

  .recent-card :deep(.el-card__body) {
    padding-right: 12px;
    padding-left: 12px;
  }
}
</style>
