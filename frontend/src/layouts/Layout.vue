<template>
  <div class="common-layout">
    <el-container style="height: 100vh;">
      <el-header style="border-bottom: 1px solid #ddd; display: flex; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 3px;">
          <img src="@/assets/imgs/logo.png" alt="" style="width: 36px;">
          <span style="font-size: 24px;">智能实验室预约系统</span>
        </div>
        <div style="display: flex; align-items: center;">
          <el-dropdown placement="bottom-end" @command="handleCommand">
            <div style="display: flex; align-items: center; gap: 5px; cursor: pointer;">
              <img :src="userInfo?.avatar" alt="" style="width: 24px; border-radius: 50%;">
              <span>{{ userInfo?.name || userInfo?.username }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile"><el-text class="mx-1"
                    type="primary">个人中心</el-text></el-dropdown-item>
                <el-dropdown-item command="password"><el-text class="mx-1"
                    type="primary">修改密码</el-text></el-dropdown-item>
                <el-dropdown-item divided command="logout"><el-text class="mx-1"
                    type="danger">退出登录</el-text></el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-container>
        <el-aside class="manager-aside" width="200px">
          <el-menu class="manager-menu" router :default-active="route.path" style="height: 100%;">
            <el-menu-item index="/manager/home"><el-icon>
                <Setting />
              </el-icon><span>系统首页</span></el-menu-item>
              <el-menu-item index="/manager/ai-chat"><el-icon>
                <ChatLineRound />
              </el-icon><span>AI助手</span></el-menu-item>
            <el-menu-item index="/manager/lab" v-if="userInfo?.role === 'admin'" ><el-icon>
                <House />
              </el-icon><span>实验室管理</span></el-menu-item>
              <el-menu-item index="/manager/lab_list" v-if="userInfo?.role === 'student'"><el-icon>
                <House />
              </el-icon><span>实验室列表</span></el-menu-item>
            <el-menu-item index="/manager/equ" v-if="userInfo?.role === 'admin'"><el-icon>
                <Filter />
              </el-icon><span>设备管理</span></el-menu-item>
              <el-menu-item index="/manager/audit-reservation" v-if="userInfo?.role === 'admin'"><el-icon>
                <Tickets />
              </el-icon><span>预约审核</span></el-menu-item>
              <el-menu-item index="/manager/my-reservation" v-if="userInfo?.role === 'student'"><el-icon>
                <Tickets />
              </el-icon><span>我的预约</span></el-menu-item>
            <el-menu-item index="/manager/user" v-if="userInfo?.role === 'admin'"><el-icon>
                <User />
              </el-icon><span>用户管理</span></el-menu-item>
          </el-menu>
        </el-aside>
        <el-container>
          <el-main><router-view /></el-main>
        </el-container>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { useUser } from '@/utils/user'
import router from '@/router'
import { useRoute } from 'vue-router'
import { User, Filter, House, Setting, Tickets, ChatLineRound } from '@element-plus/icons-vue'


const route = useRoute()
const { userInfo } = useUser()
const { logout } = useUser()

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/manager/profile')
  } else if (command === 'password') {
    router.push('/manager/password')
  } else if (command === 'logout') {
    logout()
    router.push('/login')
  }
}
</script>

<style scoped>
@media (max-width: 600px) {
  .manager-aside {
    width: 64px !important;
    flex: 0 0 64px !important;
  }

  .manager-menu {
    width: 64px;
  }

  .manager-menu :deep(.el-menu-item) {
    justify-content: center;
    padding: 0 !important;
  }

  .manager-menu :deep(.el-menu-item > span) {
    display: none;
  }

  .manager-menu :deep(.el-menu-item .el-icon) {
    margin: 0;
  }
}
</style>