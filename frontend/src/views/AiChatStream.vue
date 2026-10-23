<template>
  <section class="chat-page">
    <header class="chat-header">
      <div>
        <h1>智能实验室 AI 助手</h1>
        <p>可查询实验室、设备、预约信息，也可以咨询实验室规则。</p>
      </div>
      <el-tag type="success" effect="plain">实时流式对话</el-tag>
    </header>

    <div ref="listRef" class="chat-list" aria-live="polite">
      <div v-if="messages.length === 0" class="welcome">
        <div class="welcome-icon"><el-icon><ChatDotRound /></el-icon></div>
        <h2>你好，我是智能实验室助手</h2>
        <p>你可以问我实验室开放时间、设备信息或预约相关问题。</p>
      </div>

      <article
        v-for="(message, index) in messages"
        :key="index"
        class="message-row"
        :class="message.role"
      >
        <div class="avatar" :class="message.role">
          <el-icon><User v-if="message.role === 'user'" /><ChatDotRound v-else /></el-icon>
        </div>
        <div class="message-content">
          <div class="message-name">{{ message.role === 'user' ? '我' : '实验室助手' }}</div>
          <div v-if="message.role === 'user'" class="message-bubble user-bubble">
            {{ message.content }}
          </div>
          <div v-else class="message-bubble assistant-bubble">
            <div v-if="message.tools?.length" class="tool-list">
              <div v-for="(tool, toolIndex) in message.tools" :key="toolIndex" class="tool-item">
                <el-icon class="tool-icon"><Tools /></el-icon>
                <div class="tool-copy">
                  <span>{{ tool.label || tool.name }}</span>
                  <small v-if="tool.preview">{{ tool.preview }}</small>
                  <small v-else-if="tool.error" class="tool-error">{{ tool.error }}</small>
                  <small v-else>{{ tool.done ? '执行完成' : '正在执行…' }}</small>
                </div>
                <el-icon v-if="!tool.done" class="tool-loading is-loading"><Loading /></el-icon>
                <el-icon v-else-if="tool.error" class="tool-error-icon"><WarningFilled /></el-icon>
                <el-icon v-else class="tool-done"><CircleCheck /></el-icon>
              </div>
            </div>
            <div
              v-if="message.content"
              class="markdown-content"
              v-html="formatAssistantMessage(message.content)"
            />
            <div v-else-if="message.pending && !message.tools?.length" class="typing-indicator">
              <i></i><i></i><i></i>
            </div>
            <div v-if="message.error" class="stream-error">
              <el-icon><WarningFilled /></el-icon>
              {{ message.error }}
            </div>
            <div v-if="message.stopped" class="stopped-note">生成已停止</div>
          </div>
        </div>
      </article>
    </div>

    <footer class="composer">
      <div class="composer-box">
        <el-input
          v-model="input"
          class="composer-input"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 5 }"
          maxlength="1280"
          resize="none"
          placeholder="输入你想了解的问题…（Enter 发送，Shift + Enter 换行）"
          :disabled="loading"
          @keydown.enter="handleEnter"
        />
        <el-button
          v-if="loading"
          class="send-button stop-button"
          circle
          aria-label="停止生成"
          @click="stopGeneration"
        >
          <el-icon><VideoPause /></el-icon>
        </el-button>
        <el-button
          v-else
          class="send-button"
          type="primary"
          circle
          :disabled="!input.trim()"
          aria-label="发送消息"
          @click="sendMessage"
        >
          <el-icon><Promotion /></el-icon>
        </el-button>
      </div>
      <div class="composer-hint">AI 生成内容仅供参考，请以系统中的实际数据为准。</div>
    </footer>
  </section>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import {
  ChatDotRound,
  CircleCheck,
  Loading,
  Promotion,
  Tools,
  User,
  VideoPause,
  WarningFilled,
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getChatApi } from '@/api/ai'
import { getToken } from '@/utils/auth'

const messages = ref([])
const input = ref('')
const listRef = ref(null)
const loading = ref(false)
const controller = ref(null)
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || ''

const formatAssistantMessage = computed(() => (content) =>
  DOMPurify.sanitize(marked.parse(content || '', { async: false, breaks: true })),
)

const scrollToBottom = async () => {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

const loadChat = async () => {
  try {
    const response = await getChatApi()
    if (response.code === 200 && Array.isArray(response.data?.messages)) {
      messages.value = response.data.messages.map(({ role, content }) => ({ role, content }))
    }
  } catch {
    messages.value = []
  }
  await scrollToBottom()
}

const applyEvent = async (data, assistantMessage, enqueueText) => {
  if (data === '[DONE]') {
    assistantMessage.pending = false
    return true
  }

  let event
  try {
    event = JSON.parse(data)
  } catch {
    assistantMessage.error = '收到无法识别的流式数据。'
    assistantMessage.pending = false
    return false
  }

  if (event.type === 'token') {
    enqueueText(event.content || '')
  } else if (event.type === 'tool_start') {
    assistantMessage.tools.push({
      name: event.name,
      label: event.label,
      input: event.input,
      done: false,
    })
  } else if (event.type === 'tool_end') {
    const tool = [...assistantMessage.tools]
      .reverse()
      .find((item) => item.name === event.name && !item.done)
    if (tool) {
      tool.done = true
      tool.preview = event.preview
      tool.error = event.error
    }
  } else if (event.type === 'error') {
    assistantMessage.error = event.content || '生成失败，请稍后重试。'
    assistantMessage.pending = false
  }
  return false
}

const readEventStream = async (response, assistantMessage) => {
  if (!response.body) throw new Error('浏览器无法读取流式响应。')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  const pendingCharacters = []
  let buffer = ''
  let completed = false
  let typing = false
  let typingTask = Promise.resolve()

  const drainCharacters = async () => {
    while (pendingCharacters.length && !controller.value?.signal.aborted) {
      assistantMessage.content += pendingCharacters.shift()
      await nextTick()
      await new Promise((resolve) => requestAnimationFrame(resolve))
      if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
      await new Promise((resolve) => setTimeout(resolve, 24))
    }
    typing = false
  }

  const enqueueText = (text) => {
    pendingCharacters.push(...Array.from(text))
    if (!typing) {
      typing = true
      typingTask = drainCharacters()
    }
  }

  const consumeBlock = async (block) => {
    const data = block
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).replace(/^ /, ''))
      .join('\n')
    if (data) completed = (await applyEvent(data, assistantMessage, enqueueText)) || completed
  }

  try {
    while (!completed) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done })

      let separator
      while ((separator = buffer.match(/\r?\n\r?\n/))) {
        const index = separator.index
        await consumeBlock(buffer.slice(0, index))
        buffer = buffer.slice(index + separator[0].length)
        if (completed) break
      }
      if (done) {
        if (buffer.trim()) await consumeBlock(buffer)
        break
      }
    }
  } finally {
    reader.releaseLock()
  }
  if (!completed) throw new Error('流式连接意外结束，请重试。')
  await typingTask
  assistantMessage.pending = false
}

const sendMessage = async () => {
  const text = input.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  const assistantMessage = reactive({
    role: 'assistant',
    content: '',
    tools: [],
    pending: true,
    error: '',
    stopped: false,
  })
  messages.value.push(assistantMessage)
  input.value = ''
  loading.value = true
  controller.value = new AbortController()
  await scrollToBottom()

  try {
    const response = await fetch(`${apiBaseUrl}/api/ai/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
      },
      body: JSON.stringify({
        messages: messages.value
          .filter((message) => message !== assistantMessage)
          .filter((message) => message.role === 'user' || message.role === 'assistant')
          .map(({ role, content }) => ({ role, content })),
      }),
      signal: controller.value.signal,
    })

    if (!response.ok) {
      let detail = `请求失败（${response.status}）`
      try {
        const body = await response.json()
        detail = body.message || body.detail || detail
      } catch {
        // Keep the HTTP status as the visible error when the body is not JSON.
      }
      throw new Error(detail)
    }

    await readEventStream(response, assistantMessage)
    if (assistantMessage.pending) assistantMessage.pending = false
  } catch (error) {
    assistantMessage.pending = false
    if (error.name === 'AbortError') {
      assistantMessage.stopped = true
    } else {
      assistantMessage.error = error.message || '连接失败，请检查网络后重试。'
      ElMessage.error(assistantMessage.error)
    }
  } finally {
    loading.value = false
    controller.value = null
    await scrollToBottom()
  }
}

const handleEnter = (event) => {
  if (event.shiftKey || event.isComposing) return
  event.preventDefault()
  sendMessage()
}

const stopGeneration = () => controller.value?.abort()

onMounted(loadChat)
onBeforeUnmount(stopGeneration)
</script>

<style scoped>
.chat-page {
  display: flex;
  flex-direction: column;
  width: min(100%, 1040px);
  height: calc(100vh - 112px);
  min-height: 420px;
  margin: 0 auto;
  overflow: hidden;
  background: #fff;
  border: 1px solid #e8edf3;
  border-radius: 18px;
  box-shadow: 0 8px 32px rgb(34 63 95 / 6%);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 26px;
  border-bottom: 1px solid #edf0f4;
}

.chat-header h1 {
  color: #1f2d3d;
  font-size: 19px;
  font-weight: 650;
}

.chat-header p {
  margin-top: 6px;
  color: #8a94a3;
  font-size: 13px;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 28px clamp(16px, 5vw, 60px);
  scroll-behavior: smooth;
}

.welcome {
  display: flex;
  min-height: 100%;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8a94a3;
  text-align: center;
}

.welcome-icon {
  display: grid;
  width: 58px;
  height: 58px;
  margin-bottom: 16px;
  color: #fff;
  font-size: 27px;
  background: linear-gradient(145deg, #5095ff, #67c6e8);
  border-radius: 18px;
  place-items: center;
}

.welcome h2 {
  margin-bottom: 9px;
  color: #344054;
  font-size: 18px;
}

.welcome p {
  font-size: 13px;
}

.message-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 24px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  color: #4785ee;
  font-size: 18px;
  background: #eaf2ff;
  border-radius: 12px;
  place-items: center;
}

.avatar.user {
  color: #fff;
  background: #5b8ff9;
}

.message-content {
  max-width: min(82%, 720px);
  min-width: 0;
}

.message-row.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-name {
  margin: 1px 0 7px;
  color: #98a2b3;
  font-size: 12px;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 4px 16px 16px;
  font-size: 14px;
  line-height: 1.75;
  overflow-wrap: anywhere;
}

.user-bubble {
  color: #fff;
  white-space: pre-wrap;
  background: #528cf2;
  border-radius: 16px 4px 16px 16px;
}

.assistant-bubble {
  color: #344054;
  background: #f5f7fa;
}

.markdown-content :deep(p + p),
.markdown-content :deep(ul),
.markdown-content :deep(ol),
.markdown-content :deep(pre) {
  margin-top: 10px;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 22px;
}

.markdown-content :deep(ul) {
  list-style: disc;
}

.markdown-content :deep(ol) {
  list-style: decimal;
}

.markdown-content :deep(pre) {
  padding: 12px;
  overflow-x: auto;
  background: #e9edf3;
  border-radius: 8px;
}

.markdown-content :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.tool-list {
  display: grid;
  gap: 8px;
  margin-bottom: 10px;
}

.tool-item {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  min-width: 220px;
  padding: 9px 11px;
  color: #536477;
  background: #fff;
  border: 1px solid #e7ecf2;
  border-radius: 10px;
  font-size: 12px;
}

.tool-icon {
  margin-top: 2px;
  color: #528cf2;
}

.tool-copy {
  display: grid;
  flex: 1;
  gap: 3px;
  min-width: 0;
}

.tool-copy small {
  overflow: hidden;
  color: #98a2b3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tool-copy .tool-error,
.tool-error-icon {
  color: #e45656;
}

.tool-loading {
  color: #528cf2;
}

.tool-done {
  color: #67c23a;
}

.stream-error {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 8px;
  color: #d94b4b;
  font-size: 12px;
}

.stopped-note {
  margin-top: 6px;
  color: #98a2b3;
  font-size: 12px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  height: 20px;
}

.typing-indicator i {
  width: 6px;
  height: 6px;
  background: #a8b5c7;
  border-radius: 50%;
  animation: typing 1.1s infinite ease-in-out;
}

.typing-indicator i:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-indicator i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-4px); opacity: 1; }
}

.composer {
  padding: 14px clamp(16px, 5vw, 60px) 12px;
  border-top: 1px solid #edf0f4;
}

.composer-box {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 10px 12px 10px 16px;
  border: 1px solid #dfe5ed;
  border-radius: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.composer-box:focus-within {
  border-color: #8db4fa;
  box-shadow: 0 0 0 3px rgb(82 140 242 / 10%);
}

.composer-input {
  flex: 1;
}

.composer-input :deep(.el-textarea__inner) {
  padding: 5px 0;
  color: #344054;
  box-shadow: none;
}

.send-button {
  flex: 0 0 auto;
}

.stop-button {
  color: #e45656;
  background: #fff1f0;
  border: 0;
}

.composer-hint {
  margin-top: 8px;
  color: #a0a8b5;
  font-size: 11px;
  text-align: center;
}

@media (max-width: 600px) {
  .chat-page {
    height: calc(100dvh - 112px);
    min-height: 360px;
    border-radius: 12px;
  }

  .chat-header {
    padding: 15px 16px;
  }

  .chat-header h1 {
    font-size: 16px;
  }

  .chat-header p {
    max-width: 245px;
    line-height: 1.5;
  }

  .chat-header :deep(.el-tag) {
    flex: 0 0 auto;
    font-size: 10px;
  }

  .chat-list {
    padding: 20px 14px;
  }

  .message-row {
    gap: 8px;
    margin-bottom: 18px;
  }

  .avatar {
    width: 30px;
    height: 30px;
    flex-basis: 30px;
  }

  .message-content {
    max-width: calc(100% - 40px);
  }

  .message-bubble {
    padding: 10px 12px;
    font-size: 13px;
  }

  .composer {
    padding: 12px 12px 10px;
  }
}
</style>
