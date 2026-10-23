<template>
  <el-dialog :model-value="visibe" :title="selectTitle()" :close-on-click-modal="false" width="500" align-center @open="onOpen" @close="onClosed">
    <el-form :model="form" ref="ruleFormRef" :rules="rules" v-loading="loading" label-width="80px"
      style="max-width: 600px">
      <el-form-item label="日期" prop="date">
        <el-date-picker v-model="form.date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD"
          :disabled-date="disabledDate" style="width: 100%" placeholder="请选择预约日期" />
      </el-form-item>
      <el-form-item label="开始时间" prop="startTime">
        <el-time-select v-model="form.startTime" start="08:30" step="00:15" end="19:00"
          :max-time="form.endTime" style="width: 100%" placeholder="请选择预约开始时间" />
      </el-form-item>
      <el-form-item label="结束时间" prop="endTime">
        <el-time-select v-model="form.endTime" start="08:30" step="00:15" end="19:00"
          :min-time="form.startTime"
          style="width: 100%" placeholder="请选择预约结束时间" />
      </el-form-item>
      <el-form-item label="说明" prop="remark">
        <el-input v-model="form.remark" style="width: 100%" type="textarea"></el-input>
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="onClosed">取消</el-button>
        <el-button type="primary" @click="onSubmit">预约</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { createReservationApi } from '@/api/reservation'
import { cleanParams } from '@/utils/params'
import { ElMessage } from 'element-plus'
import { ref, reactive } from 'vue'

const props = defineProps({
  visibe: Boolean,
  labId: Number,
  labName: String,
  equipmentId: Number,
  equipmentName: String
})

const emit = defineEmits(['updateVisibe'])

const form = reactive({
  date: null,
  startTime: null,
  endTime: null,
  remark: null,
})



const ruleFormRef = ref()
const rules = reactive({
  date: [{ required: true, message: '请选择预约日期', trigger: 'change' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  remark: [{ max: 64, message: 'Length should lt 64', trigger: 'blur' }]
})

const loading = ref(false)

const onSubmit = async () => {
  try {
    await ruleFormRef.value.validate()
  } catch {
    return
  }
  try {
    loading.value = true
    const res = await createReservationApi(cleanParams({
      lab_id: props.labId,
      equipment_id: props.equipmentId,
      reserve_date: form.date,
      start_time: form.startTime,
      end_time: form.endTime,
      remark: form.remark
    }))
    if (res.code === 200) {
      ElMessage.success('预约已提交，请等待审核')
      emit('updateVisibe')
    }
  } finally {
    loading.value = false
  }
}

const onOpen = () => {
  form.date = null
  form.startTime = null
  form.endTime = null
  form.remark = null
  ruleFormRef.value?.clearValidate()
}
// closed：完全关闭后 —— 清理
const onClosed = () => {
  ruleFormRef.value?.resetFields()
  emit('updateVisibe')
}

const disabledDate = (t) => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return t.getTime() < today.getTime()
}

const selectTitle = () => {
  const labTitle = props.labName ?? '实验室'
  const equipTitle = props.equipmentName ?? '设备'
  return props.equipmentName ? equipTitle + '预约' : labTitle + '预约'
}

</script>
