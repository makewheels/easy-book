<template>
  <div class="edit-student-page">
    <div class="header">
      <button class="back-btn" @click="goBack">
        ← 返回
      </button>
      <h1>编辑学员</h1>
    </div>
    
    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>
      
      <form v-else @submit.prevent="handleSubmit" class="student-form">
        <div class="form-section">
          <h3>基本信息</h3>
          
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
            <label>学习项目 *</label>
            <input
              type="text"
              v-model="form.learning_item"
              required
              placeholder="请输入学习项目（如：自由泳、蛙泳、仰泳、蝶泳、踩水、考证等）"
            />
            <div class="learning-item-suggestions">
              <div class="suggestion-chips">
                <span
                  v-for="item in learningItemSuggestions"
                  :key="item"
                  class="suggestion-chip"
                  @click="selectLearningItem(item)"
                >
                  {{ item }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>备注</label>
            <textarea 
              v-model="form.note"
              placeholder="请输入备注信息（可选）"
              rows="3"
            ></textarea>
          </div>
        </div>
        
        <div class="form-section">
          <h3>套餐信息</h3>
          
          <div class="form-group">
            <label>套餐类型 *</label>
            <select v-model="form.package_type" required>
              <option value="">请选择套餐类型</option>
              <option value="1v1">1v1</option>
              <option value="1v多">1v多</option>
            </select>
          </div>
          
          <div class="form-group">
            <label>总共 *</label>
            <input
              type="number"
              v-model="form.total_lessons"
              required
              min="1"
              placeholder="请输入总共次数"
            />
          </div>

          <div class="form-group">
            <label>剩余</label>
            <input
              type="number"
              v-model="form.remaining_lessons"
              readonly
              disabled
              class="readonly-input"
              placeholder="剩余次数（由系统自动管理）"
            />
          </div>
          
          <div class="form-group">
            <label>售价（元）*</label>
            <input 
              type="number" 
              v-model="form.price" 
              required
              min="1"
              placeholder="请输入售价"
            />
          </div>
          
          <div class="form-group">
            <label>上交俱乐部（元）*</label>
            <input
              type="number"
              v-model="form.venue_share"
              required
              min="0"
              placeholder="请输入上交俱乐部"
            />
            <div class="venue-share-suggestions">
              <div class="suggestion-chips">
                <span
                  v-for="amount in venueShareSuggestions"
                  :key="amount"
                  class="suggestion-chip"
                  @click="selectVenueShare(amount)"
                >
                  {{ amount }} 元
                </span>
              </div>
            </div>
          </div>
          
          <div class="form-group" v-if="form.price && form.venue_share">
            <label>利润</label>
            <div class="profit-display">
              {{ form.price - form.venue_share }} 元
            </div>
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

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()

const loading = ref(false)
const initialLoading = ref(true)

const form = reactive({
  name: '',
  learning_item: '',
  package_type: '',
  total_lessons: '',
  remaining_lessons: '',
  price: '',
  venue_share: '',
  note: ''
})

// 学习项目建议列表
const learningItemSuggestions = [
  '蛙泳',
  '自由泳',
  '仰泳',
  '蝶泳',
  '踩水',
  '考证',
  '技术改进',
  '防溺水'
]

// 上交俱乐部金额建议列表
const venueShareSuggestions = [
  600
]

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
      form.learning_item = student.learning_item || ''
      form.package_type = student.package_type || ''
      form.total_lessons = student.total_lessons || ''
      form.remaining_lessons = student.remaining_lessons || ''
      form.price = student.price || ''
      form.venue_share = student.venue_share || ''
      form.note = student.note || ''
    }
  } catch (error) {
    toast.error('获取学员信息失败')
    router.push('/students')
  }
}

const goBack = () => {
  router.push(`/student/${route.params.id}`)
}

const selectLearningItem = (item) => {
  form.learning_item = item
}

const selectVenueShare = (amount) => {
  form.venue_share = amount
}

const handleSubmit = async () => {
  // 验证表单
  if (!form.name || !form.learning_item || !form.package_type || 
      !form.total_lessons || !form.remaining_lessons || !form.price || !form.venue_share) {
    toast.warning('请填写所有必填字段')
    return
  }
  
  if (form.total_lessons <= 0 || form.remaining_lessons < 0 || form.price <= 0 || form.venue_share < 0) {
    toast.warning('请输入有效的数值')
    return
  }
  
  if (parseInt(form.remaining_lessons) > parseInt(form.total_lessons)) {
    toast.warning('剩余课程数不能大于总课程数')
    return
  }
  
  loading.value = true
  
  try {
    await studentStore.updateStudent(route.params.id, {
      name: form.name,
      learning_item: form.learning_item,
      package_type: form.package_type,
      total_lessons: parseInt(form.total_lessons),
      remaining_lessons: parseInt(form.remaining_lessons),
      price: parseInt(form.price),
      venue_share: parseInt(form.venue_share),
      note: form.note || undefined
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
  overflow-y: auto;
}

.header {
  background: #1989fa;
  color: #fff;
  padding: 15px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  height: 60px;
  box-sizing: border-box;
}

.back-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  margin-right: 15px;
}

.header h1 {
  font-size: 22px;
  margin: 0;
}

.content {
  padding: 15px;
  padding-top: 75px;
  min-height: calc(100vh - 60px);
  box-sizing: border-box;
}

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
}

.student-form {
  max-width: 400px;
  margin: 0 auto;
}

.form-section {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-section h3 {
  margin: 0 0 15px 0;
  color: #1989fa;
  font-size: 18px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #1989fa;
}

.profit-display {
  padding: 10px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  color: #1989fa;
  text-align: center;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
  margin-bottom: 30px;
}

.btn-cancel,
.btn-save {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}

.btn-cancel {
  background: #f5f5f5;
  color: #666;
}

.btn-save {
  background: #1989fa;
  color: #fff;
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.readonly-input {
  background-color: #f5f5f5;
  color: #666;
  cursor: not-allowed;
  border-color: #ddd;
}

.readonly-input:focus {
  outline: none;
  border-color: #ddd;
}

.learning-item-suggestions {
  margin-top: 8px;
}

.venue-share-suggestions {
  margin-top: 8px;
}

.suggestion-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.suggestion-chip {
  padding: 4px 8px;
  background: #f0f9ff;
  border: 1px solid #b3d8ff;
  border-radius: 4px;
  font-size: 12px;
  color: #1989fa;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.suggestion-chip:hover {
  background: #1989fa;
  color: #fff;
  border-color: #1989fa;
  transform: scale(1.05);
}
</style>