<template>
  <el-card style="max-width: 100%">
  <template #header>
    <div class="card-header">
      <span style="font-size: large;">智能实验室AI助手</span>
    </div>
  </template>
  <div class="ai-chat">
    <div ref="listRef" class="list">
      <div v-for="(msg, index) in messages" :key="index" class="msg" :class="msg.role">
        <div v-if="msg.role === 'assistant'" v-html="formatAssistantMessage(msg.content)" />
        <template v-else>{{ msg.content }}</template>
      </div>
    </div>

    <div class="footer">
      <el-input v-model="input" type="textarea" placeholder="输入问题，Enter 发送，Shift + Enter 换行" @keydown.enter="send" />
      <el-button type="primary" :disabled="!input.trim()" :loading="loading" @click="send">
        发送
      </el-button>
    </div>
  </div>
  </el-card>
</template>

<script setup>
import { chatApi, getChatApi } from '@/api/ai'
import { ref, nextTick, onMounted } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'

const messages = ref([])
const input = ref('')
const listRef = ref(null)
const loading = ref(false)

const formatAssistantMessage = (content) =>
  DOMPurify.sanitize(marked.parse(content, { async: false, breaks: true }))

const scrollToBottom = async () => {
  await nextTick() // 等 DOM 更新完成之后，再执行传入的回调
  listRef.value.scrollTop = listRef.value.scrollHeight
}

// 加载当天历史数据
const loadChat = async () => {
  try {
    const res = await getChatApi()
    if (res.code === 200) {
      res.data.messages.forEach(element => {
        messages.value.push({ role: element.role, content: element.content })
      });
    }
  } catch (e){
    // console.log(e)
    messages.value.push({ role: 'assistant', content: '你好，我是智能实验室AI助手，有什么可以帮你？' })
  }
  scrollToBottom()
}

onMounted(loadChat)

const send = async (e) => {
  if (e.shiftKey) return
  e.preventDefault()
  loading.value = true
  const text = input.value.trim()
  if (!text) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  scrollToBottom()
  try { 
    const res = await chatApi({ messages: messages.value })
    if (res.code === 200) {
      messages.value.push(res.data)
    }
  } finally {
    loading.value = false
  }
  scrollToBottom()
}
</script>

<style scoped>
.ai-chat {
  display: flex;
  flex-direction: column;
  height: 100vh;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f7f8fa;
}

.msg {
  max-width: 80%;
  margin-bottom: 12px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  width: fit-content;
}

.msg.assistant {
  background: #f3ecec;
  color: #303133;
  line-height: 16px;
}

.msg.user {
  background: #409eff;
  color: #fff;
  margin-left: auto;
}

.footer {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #ebeef5;
  background: #fff;
}
</style>