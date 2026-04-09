<template>
  <div class="edit-student-page">
    <div class="header">
      <BackButton />
      <h1>编辑学员</h1>
    </div>
    
    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <form v-else @submit.prevent="handleSubmit" class="student-form">
        <div class="form-section">
          <h3><span class="title-icon">👤</span> 基本信息</h3>
          
          <div class="form-group">
            <label>姓名 *</label>
            <input
              type="text"
              v-model="form.name"
              required
              placeholder="请输入学员姓名"
            />
          </div>

  
          <div class="form-group">
            <label>性别</label>
            <select v-model="form.gender">
              <option value="">请选择性别</option>
              <option value="男">男</option>
              <option value="女">女</option>
            </select>
          </div>

          <div class="form-group">
            <label>年龄</label>
            <input
              type="number"
              v-model.number="form.age"
              placeholder="请输入年龄"
              min="0"
              max="150"
            />
          </div>

          <div class="form-group">
            <label>身份证号码</label>
            <input
              type="text"
              v-model="form.id_card"
              placeholder="请输入身份证号码"
            />
          </div>

          <div class="form-group">
            <label>联系电话</label>
            <input
              type="tel"
              v-model="form.phone"
              placeholder="请输入联系电话"
            />
          </div>

          <div class="form-group">
            <label>紧急联系人</label>
            <input
              type="text"
              v-model="form.emergency_contact"
              placeholder="请输入紧急联系人"
            />
          </div>
        </div>
        
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="goBack">
            取消
          </button>
          <button type="submit" class="btn-save" :disabled="loading">
            {{ loading ? '保存中...' : '保存' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { toast } from '@/utils/toast'
import BackButton from '@/components/common/BackButton.vue'

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()

const loading = ref(false)
const initialLoading = ref(true)

const form = reactive({
  name: '',
  gender: '',
  age: null,
  id_card: '',
  phone: '',
  emergency_contact: ''
})

onMounted(async () => {
  const studentId = route.params.id
  await fetchStudentData(studentId)
  initialLoading.value = false
})

const fetchStudentData = async (studentId) => {
  try {
    await studentStore.fetchStudentById(studentId)
    const student = studentStore.currentStudent
    
    if (student) {
      form.name = student.name || ''
      form.gender = student.gender || ''
      form.age = student.age || null
      form.id_card = student.id_card || ''
      form.phone = student.phone || ''
      form.emergency_contact = student.emergency_contact || ''
    }
  } catch (error) {
    toast.error('获取学员信息失败')
    router.back() // 如果获取学员信息失败，返回上一个页面
  }
}


const goBack = () => {
  router.back()
}

const handleSubmit = async () => {
  // 验证表单
  if (!form.name) {
    toast.warning('请填写姓名')
    return
  }

  loading.value = true

  try {
    await studentStore.updateStudent(route.params.id, {
      name: form.name,
      gender: form.gender || undefined,
      age: form.age || undefined,
      id_card: form.id_card || undefined,
      phone: form.phone || undefined,
      emergency_contact: form.emergency_contact || undefined
    })

    toast.success('学员信息更新成功')
    router.push(`/student/${route.params.id}`)
  } catch (error) {
    toast.error(error.message || '更新失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.edit-student-page {
  min-height: 100vh;
  background: #f5f5f5;
  position: relative;
  font-size: 20px;
}

.header {
  background: #fff;
  color: #1a1a1a;
  padding: 16px 20px;
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e0e0e0;
}

.back-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 16px;
  cursor: pointer;
  margin-right: 15px;
  padding: 8px 12px;
  border-radius: 6px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.back-btn:hover {
  background: #f0f0f0;
  color: #1a1a1a;
}

.header h1 {
  font-size: 20px;
  margin: 0;
  font-weight: 600;
}

.content {
  padding: 20px 0;
  margin: 0;
  min-height: calc(100vh - 60px);
  box-sizing: border-box;
}

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

.student-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  margin: 0;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.form-section h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  margin: -20px -20px 20px -20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e8e8e8;
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 16px;
  color: #1a1a1a;
  font-weight: 600;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 16px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  font-size: 16px;
  font-family: inherit;
  box-sizing: border-box;
  background: #fff;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #1989fa;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin: 0 20px 20px 20px;
}

.btn-cancel,
.btn-save {
  flex: 1;
  padding: 16px 20px;
  border: none;
  border-radius: 12px;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-cancel {
  background: #fff;
  color: #1989fa;
  border: 2px solid #1989fa;
}

.btn-cancel:hover {
  background: #f0f9ff;
}

.btn-save {
  background: #1989fa;
  color: #fff;
  border: 2px solid #1989fa;
}

.btn-save:hover {
  background: #096dd9;
  border-color: #096dd9;
}

.btn-save:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.readonly-input {
  background: #f8f9fa;
  color: #999;
  cursor: not-allowed;
  border: 2px dashed #d0d0d0;
  font-style: italic;
  text-align: center;
  font-weight: 500;
}

.readonly-input:focus {
  outline: none;
  border: 2px dashed #d0d0d0;
}

</style>