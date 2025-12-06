<template>
  <div class="add-student-page">
    <div class="header">
      <BackButton />
      <h1>新增学员</h1>
    </div>
    
    <div class="content">
      <form @submit.prevent="handleSubmit" class="student-form">
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
              placeholder="请输入学习项目"
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
        
        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="goBack" :disabled="loading">
            取消
          </button>
          <button type="submit" class="btn-save" :disabled="loading">
            {{ loading ? '保存中...' : '新增学员' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStudentStore } from '@/stores/student'
import { toast } from '@/utils/toast'
import BackButton from '@/components/common/BackButton.vue'

const router = useRouter()
const studentStore = useStudentStore()

const loading = ref(false)

const form = reactive({
  name: '',
  learning_item: '',
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

const selectLearningItem = (item) => {
  form.learning_item = item
}

const goBack = () => {
  router.back()
}

const handleSubmit = async () => {
  // 验证表单
  if (!form.name || !form.learning_item) {
    toast.warning('请填写所有必填字段')
    return
  }

  loading.value = true

  // 构建要发送的数据
  const studentData = {
    name: form.name,
    learning_item: form.learning_item,
    note: form.note || undefined
  }

  try {
    await studentStore.createStudent(studentData)

    toast.success('学员创建成功')
    router.push('/students')
  } catch (error) {
    toast.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.add-student-page {
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
  cursor: not-allowed;
}

.learning-item-suggestions {
  margin-top: 8px;
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