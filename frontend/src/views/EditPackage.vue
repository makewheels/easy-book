<template>
  <div class="edit-package-page">
    <div class="header">
      <BackButton />
      <h1>编辑套餐</h1>
    </div>

    <div class="content">
      <div v-if="loading" class="loading">
        加载中...
      </div>

      <form v-else @submit.prevent="handleSubmit" class="package-form">
        <div class="form-section">
          <h3>套餐类型</h3>

          <PackageTypeSelector v-model="packageTypeData" :disabled="true" />
        </div>


        <div class="form-section">
          <h3>价格信息</h3>

          <div class="form-group">
            <label>售价（元）*</label>
            <input
              type="number"
              v-model="form.price"
              required
              min="0.01"
              step="0.01"
              placeholder="请输入售价"
              disabled
              readonly
            />
          </div>

          <div class="form-group">
            <label>上交俱乐部（元）*</label>
            <input
              type="number"
              v-model="form.venue_share"
              required
              min="0"
              step="0.01"
              placeholder="请输入上交俱乐部金额"
              disabled
              readonly
            />
            </div>

          <div class="form-group" v-if="form.price && form.venue_share">
            <label>利润</label>
            <div class="profit-display">
              {{ form.price - form.venue_share }} 元
            </div>
          </div>
        </div>

        <div class="creation-time-section">
          <div class="info-row">
            <label class="info-label">创建时间</label>
            <div class="info-display">
              {{ formatDate(form.create_time) }}
            </div>
          </div>
        </div>

        <div class="form-actions">
          <button type="button" class="btn-cancel" @click="goBack">
            返回
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { packageApi } from '@/api/package'
import { toast } from '@/utils/toast'
import BackButton from '@/components/common/BackButton.vue'
import PackageTypeSelector from '@/components/student/PackageTypeSelector.vue'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const packageId = route.params.id

const form = reactive({
  name: '',
  price: '',
  venue_share: '',
  is_active: true,
  sort_order: 0,
  create_time: null,
  update_time: null
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

const selectVenueShare = (amount) => {
  form.venue_share = amount
}

// 监听套餐类型数据变化，将其合并到表单数据中
watch(packageTypeData, (newData) => {
  Object.assign(form, newData)
}, { deep: true })

onMounted(async () => {
  await fetchPackageData()
})

const fetchPackageData = async () => {
  loading.value = true
  try {
    const response = await packageApi.getPackageById(packageId)
    // API 直接返回包数据，不需要 .data
    const packageData = response

    // 填充基本信息
    Object.assign(form, {
      name: packageData.name,
      price: packageData.price,
      venue_share: packageData.venue_share,
      is_active: packageData.is_active,
      sort_order: packageData.sort_order || 0,
      create_time: packageData.create_time,
      update_time: packageData.update_time
    })

    // 填充套餐类型信息
    packageTypeData.value = {
      package_category: packageData.package_category || 'count_based',
      original_package_type: packageData.package_type || '1v1',
      original_package_type_display: packageData.package_type || '',
      total_lessons: packageData.total_lessons,
      package_duration_type: packageData.package_duration_type,
      package_duration_days: packageData.package_duration_days,
      unlimited_access: packageData.unlimited_access || false,
      package_start_date: packageData.package_start_date,
      package_end_date: packageData.package_end_date
    }
  } catch (error) {
    toast.error(error.message || '获取套餐信息失败')
    router.back()
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const goBack = () => {
  router.back()
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
    if (!packageTypeData.value.package_end_date) {
      toast.warning('时长套餐必须设置结束日期')
      return
    }
  }

  loading.value = true

  try {
    // 生成套餐名称
    const packageTypeName = packageTypeData.value.original_package_type_display || '课程类型'
    const categoryTypeName = packageTypeData.value.package_category === 'count_based' ? '记次套餐' : '时长套餐'
    const generatedName = `${packageTypeName} ${categoryTypeName}`

    // 构建套餐数据 - 使用新的简化结构
    const packageData = {
      name: generatedName,
      package_type: packageTypeData.value.package_category === 'count_based'
        ? packageTypeData.value.original_package_type
        : 'time_based',
      price: parseFloat(form.price),
      venue_share: parseFloat(form.venue_share)
    }

    // 根据套餐类型添加特定的JSON对象
    if (packageTypeData.value.package_category === 'count_based') {
      packageData.count_based_info = {
        total_lessons: packageTypeData.value.total_lessons,
        remaining_lessons: packageTypeData.value.total_lessons // 编辑时重置剩余课程
      }
    } else {
      packageData.time_based_info = {
        start_date: packageTypeData.value.package_start_date || new Date().toISOString().split('T')[0],
        end_date: packageTypeData.value.package_end_date
      }
    }

    await packageApi.updatePackage(packageId, packageData)
    toast.success('套餐更新成功')
    router.back()
  } catch (error) {
    toast.error(error.message || '更新失败')
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
.edit-package-page {
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

.loading {
  text-align: center;
  padding: 50px 0;
  color: #666;
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

/* 创建时间区域样式 - 无框 */
.creation-time-section {
  padding: 20px;
  margin: 0;
}

/* 创建时间的横向显示样式 */
.info-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 0;
}

.info-label {
  min-width: 120px;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  flex-shrink: 0;
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

.profit-display,
.info-display {
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

.info-display {
  font-size: 16px;
  font-weight: 500;
  color: #666;
  border-color: #e0e0e0;
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