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
          <h3><span class="title-icon">💰</span> 套餐信息</h3>
          
          <div class="form-group">
            <label>套餐类型 *</label>
            <input
              type="text"
              v-model="form.package_type"
              required
              placeholder="请输入套餐类型"
            />
            <div class="package-type-suggestions">
              <div class="suggestion-chips">
                <span
                  v-for="type in packageTypeSuggestions"
                  :key="type"
                  class="suggestion-chip"
                  @click="selectPackageType(type)"
                >
                  {{ type }}
                </span>
              </div>
            </div>
          </div>
          
          <div class="form-group">
            <label>总共（次）</label>
            <input
              type="number"
              v-model="form.total_lessons"
              required
              min="1"
              placeholder="请输入总共次数"
            />
          </div>

          <div class="form-group">
            <label>剩余（次）</label>
            <input
              type="number"
              v-model="form.remaining_lessons"
              placeholder="请输入剩余次数"
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
import BackButton from '@/components/common/BackButton.vue'

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

// 套餐类型建议列表
const packageTypeSuggestions = [
  '1 v 1',
  '1 v 2',
  '1 v 3',
  '1 v 5'
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
    router.back() // 如果获取学员信息失败，返回上一个页面
  }
}


const selectLearningItem = (item) => {
  form.learning_item = item
}

const selectPackageType = (type) => {
  // 移除显示用的空格，实际存储为紧凑格式
  form.package_type = type.replace(/\s+v\s+/g, 'v')
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

.profit-display {
  padding: 20px;
  background: #f8f9fa;
  border: 2px solid #f5222d;
  border-radius: 16px;
  font-size: 24px;
  font-weight: 800;
  color: #f5222d;
  text-align: center;
  margin-top: 10px;
  margin-bottom: 2px;
  letter-spacing: 1px;
}

.form-actions {
  display: flex;
  gap: 15px;
  margin: 0 0 20px 0;
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

.learning-item-suggestions,
.package-type-suggestions,
.venue-share-suggestions {
  margin-top: 12px;
}

.suggestion-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-chip {
  padding: 8px 12px;
  background: #fff;
  border: 1px solid #1989fa;
  border-radius: 8px;
  font-size: 14px;
  color: #1989fa;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  font-weight: 500;
}

.suggestion-chip:hover {
  background: #1989fa;
  color: #fff;
  transform: translateY(-1px);
}
</style>