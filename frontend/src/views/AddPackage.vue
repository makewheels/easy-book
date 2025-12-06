<template>
  <div class="add-package-page">
    <div class="header">
      <BackButton />
      <h1>{{ studentName }} - 新增套餐</h1>
    </div>

    <div class="content">
      <form @submit.prevent="handleSubmit" class="package-form">
        <div class="form-section">
          <h3>套餐类型</h3>

          <PackageTypeSelector v-model="packageTypeData" />
        </div>

  
        <div class="form-section">
          <h3>价格信息</h3>

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
              placeholder="请输入上交俱乐部金额"
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
          <button type="button" class="btn-cancel" @click="goBack" :disabled="loading">
            取消
          </button>
          <button type="submit" class="btn-save" :disabled="loading">
            {{ loading ? '保存中...' : '新增套餐' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { studentApi } from '@/api/student'
import { packageApi } from '@/api/package'
import { toast } from '@/utils/toast'
import BackButton from '@/components/common/BackButton.vue'
import PackageTypeSelector from '@/components/student/PackageTypeSelector.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const studentName = ref('')

const form = reactive({
  name: '',
  price: '',
  venue_share: '',
  is_active: true,
  sort_order: 0
})

const packageTypeData = ref({
  package_category: 'count_based',
  original_package_type: '',
  original_package_type_display: '',
  total_lessons: null,
  package_duration_type: '',
  package_duration_days: null,
  unlimited_access: false
})

// 上交俱乐部金额建议列表
const venueShareSuggestions = [
  600
]

// 监听套餐类型数据变化，将其合并到表单数据中
watch(packageTypeData, (newData) => {
  Object.assign(form, newData)
}, { deep: true })

// 页面加载时获取学生信息
onMounted(async () => {
  const studentId = route.params.studentId
  if (studentId) {
    try {
      const response = await studentApi.getStudentById(studentId)
      const student = response.data
      if (student) {
        studentName.value = student.name
      }
    } catch (error) {
      toast.error('获取学生信息失败')
      router.back()
    }
  }
})

const goBack = () => {
  router.back()
}

const selectVenueShare = (amount) => {
  form.venue_share = amount
}

const handleSubmit = async () => {
  // 验证表单
  if (!form.price || !form.venue_share) {
    toast.warning('请填写所有必填字段')
    return
  }

  if (form.price <= 0 || form.venue_share < 0) {
    toast.warning('请输入有效的价格')
    return
  }

  // 验证套餐类型数据
  if (packageTypeData.value.package_category === 'count_based') {
    if (!packageTypeData.value.total_lessons || packageTypeData.value.total_lessons <= 0) {
      toast.warning('记次套餐必须设置总课程数')
      return
    }
  } else {
    if (!packageTypeData.value.unlimited_access && !packageTypeData.value.package_duration_type) {
      toast.warning('时长套餐必须选择时长类型或设置永久有效')
      return
    }

    if (packageTypeData.value.package_duration_type === 'custom') {
      if (!packageTypeData.value.package_duration_days || packageTypeData.value.package_duration_days <= 0) {
        toast.warning('自定义时长套餐必须设置有效天数')
        return
      }
    }
  }

  loading.value = true

  try {
    // 生成套餐名称
    const packageTypeName = packageTypeData.value.original_package_type_display || '课程类型'
    const categoryTypeName = packageTypeData.value.package_category === 'count_based' ? '记次套餐' : '时长套餐'
    const generatedName = `${packageTypeName} ${categoryTypeName}`

    // 构建套餐数据
    const packageData = {
      name: generatedName,
      package_category: packageTypeData.value.package_category,
      package_type: packageTypeData.value.original_package_type,
      price: parseInt(form.price),
      venue_share: parseInt(form.venue_share),
      is_active: form.is_active,
      sort_order: parseInt(form.sort_order) || 0
    }

    // 根据套餐类型添加特定字段
    if (packageTypeData.value.package_category === 'count_based') {
      packageData.total_lessons = packageTypeData.value.total_lessons
    } else {
      packageData.package_duration_type = packageTypeData.value.package_duration_type
      packageData.package_duration_days = packageTypeData.value.package_duration_days
      packageData.unlimited_access = packageTypeData.value.unlimited_access

      // 如果不是永久有效且有时长类型，计算结束时间
      if (!packageTypeData.value.unlimited_access && packageTypeData.value.package_duration_type) {
        const endDate = calculateEndDate(
          packageTypeData.value.package_duration_type,
          packageTypeData.value.package_duration_days
        )
        packageData.package_end_date = endDate
      }
    }

    await packageApi.createPackage(packageData)
    toast.success('套餐创建成功')
    router.push('/packages')
  } catch (error) {
    toast.error(error.message || '创建失败')
  } finally {
    loading.value = false
  }
}

const calculateEndDate = (durationType, customDays) => {
  const now = new Date()
  const endDate = new Date(now)

  switch (durationType) {
    case 'monthly':
      endDate.setMonth(endDate.getMonth() + 1)
      break
    case 'quarterly':
      endDate.setMonth(endDate.getMonth() + 3)
      break
    case 'yearly':
      endDate.setFullYear(endDate.getFullYear() + 1)
      break
    case 'custom':
      if (customDays && customDays > 0) {
        endDate.setDate(endDate.getDate() + customDays)
      }
      break
    default:
      return null
  }

  return endDate
}
</script>

<style scoped>
.add-package-page {
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

.package-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  background: #fff;
  border-radius: 0;
  padding: 20px;
  margin: 0;
  border: none;
  border-bottom: 1px solid #e0e0e0;
  overflow: hidden;
}

.form-section:last-child {
  border-bottom: none;
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
.form-group textarea:focus {
  outline: none;
  border-color: #1890ff;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-item input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.checkbox-label {
  font-size: 16px;
  color: #1a1a1a;
  user-select: none;
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

.venue-share-suggestions {
  margin-top: 12px;
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

.form-actions {
  display: flex;
  gap: 15px;
  margin: 0;
  padding: 20px;
  background: #fff;
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
  color: #1890ff;
  border: 2px solid #1890ff;
}

.btn-cancel:hover {
  background: #f0f9ff;
}

.btn-save {
  background: #1890ff;
  color: #fff;
  border: 2px solid #1890ff;
}

.btn-save:hover {
  background: #096dd9;
  border-color: #096dd9;
}

.btn-save:disabled {
  background: #ccc;
  cursor: not-allowed;
  border-color: #ccc;
}
</style>