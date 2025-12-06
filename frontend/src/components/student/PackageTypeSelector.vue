<template>
  <div class="package-type-selector">
    <div class="form-group">
      <label class="form-label">套餐类别 *</label>
      <div class="radio-group">
        <label class="radio-item">
          <input
            type="radio"
            v-model="packageData.package_category"
            value="count_based"
            @change="onCategoryChange"
          />
          <span class="radio-label">记次套餐</span>
        </label>
        <label class="radio-item">
          <input
            type="radio"
            v-model="packageData.package_category"
            value="time_based"
            @change="onCategoryChange"
          />
          <span class="radio-label">时长套餐</span>
        </label>
      </div>
    </div>

    <!-- 原套餐类型 - 只在记次套餐时显示 -->
    <div v-if="packageData.package_category === 'count_based'" class="form-group">
      <label class="form-label">课程类型 *</label>
      <input
        type="text"
        v-model="packageData.original_package_type_display"
        @input="onPackageTypeInput"
        class="package-form-input"
        placeholder="请输入课程类型"
      />
      <div class="package-type-suggestions">
        <div class="form-suggestion-chips">
          <span
            v-for="type in packageTypeSuggestions"
            :key="type.value"
            class="form-suggestion-chip"
            @click="selectPackageType(type)"
          >
            {{ type.display }}
          </span>
        </div>
      </div>
    </div>

    <!-- 记次套餐选项 -->
    <div v-if="packageData.package_category === 'count_based'" class="count-based-options">
      <div class="form-group">
        <label class="form-label">课程总数（节） *</label>
        <input
          type="number"
          v-model.number="packageData.total_lessons"
          min="1"
          class="package-form-input"
          placeholder="请输入课程总节数"
        />
        <div class="form-suggestion-chips">
          <span
            class="form-suggestion-chip"
            @click="selectPackageCount(12)"
          >
            12节
          </span>
        </div>
      </div>
    </div>

    <!-- 时长套餐选项 -->
    <div v-else class="time-based-options">
      <!-- 显示开始时间 -->
      <div v-if="packageData.package_category === 'time_based'" class="form-group">
        <label class="form-label">开始日期 *</label>
        <input
          type="date"
          v-model="packageData.package_start_date"
          @change="onStartDateChange"
          class="package-form-input"
          required
        />
      </div>

      <!-- 显示结束时间 -->
      <div v-if="packageData.package_category === 'time_based'" class="form-group end-date-group">
        <label class="form-label">结束日期 *</label>
        <input
          type="date"
          v-model="packageData.package_end_date"
          @change="onEndDateChange"
          class="package-form-input"
          required
        />
        <div class="package-type-suggestions">
          <div class="form-suggestion-chips">
            <span
              class="form-suggestion-chip"
              @click="selectDurationType('monthly')"
              :class="{ active: packageData.package_duration_type === 'monthly' }"
            >
              月卡
            </span>
            <span
              class="form-suggestion-chip"
              @click="selectDurationType('quarterly')"
              :class="{ active: packageData.package_duration_type === 'quarterly' }"
            >
              季卡
            </span>
          </div>
        </div>
      </div>

    </div>

    </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PackageService } from '@/services/package'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const route = useRoute()
const router = useRouter()

// 套餐数据
const packageData = ref({
  package_category: 'count_based',
  original_package_type: '',
  original_package_type_display: '',
  total_lessons: null,
  package_duration_type: '',
  package_duration_days: null,
  package_start_date: '',
  package_end_date: '',
  unlimited_access: false
})

// 课程类型建议列表
const packageTypeSuggestions = [
  { value: '1v1', display: '1 v 1' },
  { value: '1v2', display: '1 v 2' },
  { value: '1v3', display: '1 v 3' },
  { value: '1v5', display: '1 v 5' }
]

// 计算属性
const packageCategoryText = computed(() => {
  return packageData.value.package_category === 'count_based' ? '记次套餐' : '时长套餐'
})

const originalPackageTypeText = computed(() => {
  return packageData.value.original_package_type_display || '1 v 1'
})

const durationTypeText = computed(() => {
  if (packageData.value.unlimited_access) return '永久有效'
  if (!packageData.value.package_duration_type) return '未设置'

  const typeMap = {
    'monthly': '月卡',
    'quarterly': '季卡',
    'yearly': '年卡',
    'custom': `自定义${packageData.value.package_duration_days || 0}天`
  }
  return typeMap[packageData.value.package_duration_type] || '未设置'
})

const showPreviewEndDate = computed(() => {
  return packageData.value.package_category === 'time_based' &&
         packageData.value.package_duration_type
})

const previewEndDate = computed(() => {
  if (!showPreviewEndDate.value) return ''

  try {
    const startDate = packageData.value.package_start_date ? new Date(packageData.value.package_start_date) : new Date()
    const endDate = PackageService.calculatePackageEndDate(
      packageData.value.package_duration_type,
      startDate,
      packageData.value.package_duration_days
    )
    return endDate ? endDate.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }) : ''
  } catch (error) {
    return '计算错误'
  }
})

const onStartDateChange = () => {
  // 当开始日期改变时，重新计算结束日期
  if (packageData.value.package_duration_type) {
    calculateEndDate()
  }
  emitUpdate()
  updateURL()
}

const onEndDateChange = () => {
  emitUpdate()
  updateURL()
}

const calculateEndDate = () => {
  if (packageData.value.package_duration_type && packageData.value.package_start_date) {
    const startDate = new Date(packageData.value.package_start_date)
    const endDate = new Date(startDate)

    switch (packageData.value.package_duration_type) {
      case 'monthly':
        endDate.setMonth(endDate.getMonth() + 1)
        break
      case 'quarterly':
        endDate.setMonth(endDate.getMonth() + 3)
        break
    }

    packageData.value.package_end_date = endDate.toISOString().split('T')[0]
  }
}

// 方法
const onCategoryChange = () => {
  // 切换类别时重置相关字段
  if (packageData.value.package_category === 'count_based') {
    packageData.value.package_duration_type = ''
    packageData.value.package_duration_days = null
  } else {
    packageData.value.total_lessons = null
    // 时长套餐自动设置课程类型为通用的"时长套餐"
    packageData.value.original_package_type = 'time_based'
    packageData.value.original_package_type_display = '时长套餐'
  }
  emitUpdate()
  updateURL()
}

const onDurationTypeChange = () => {
  // 当选择时长类型时，自动计算结束日期
  if (packageData.value.package_duration_type) {
    calculateEndDate()
  }
  emitUpdate()
  updateURL()
}

const onPackageTypeInput = () => {
  // 当用户手动输入时，同时更新两个字段
  packageData.value.original_package_type = packageData.value.original_package_type_display
  emitUpdate()
  updateURL()
}

const selectPackageType = (type) => {
  packageData.value.original_package_type_display = type.display
  packageData.value.original_package_type = type.value
  emitUpdate()
  updateURL()
}

const selectPackageCount = (count) => {
  packageData.value.total_lessons = count
  emitUpdate()
  updateURL()
}

const selectDurationType = (durationType) => {
  packageData.value.package_duration_type = durationType
  onDurationTypeChange()
}

const emitUpdate = () => {
  emit('update:modelValue', { ...packageData.value })
}

// 更新URL参数
const updateURL = () => {
  const query = { ...route.query }

  // 只保存重要的套餐类型信息
  if (packageData.value.package_category) {
    query.category = packageData.value.package_category
  }
  if (packageData.value.original_package_type) {
    query.type = packageData.value.original_package_type
  }

  // 移除空的参数
  Object.keys(query).forEach(key => {
    if (!query[key]) {
      delete query[key]
    }
  })

  router.replace({ query })
}

// 从URL参数初始化数据
const initFromURL = () => {
  const { category, type } = route.query

  if (category) {
    packageData.value.package_category = category
  }
  if (type) {
    packageData.value.original_package_type = type
    // 如果type是预定义的值，设置对应的显示文本
    const matchedType = packageTypeSuggestions.find(s => s.value === type)
    if (matchedType) {
      packageData.value.original_package_type_display = matchedType.display
    }
  }
}

// 监听变化
watch(packageData, emitUpdate, { deep: true })

// 初始化
onMounted(() => {
  // 先从props初始化
  if (props.modelValue) {
    Object.assign(packageData.value, props.modelValue)
  }
  // 设置默认开始日期为今天
  if (!packageData.value.package_start_date) {
    packageData.value.package_start_date = new Date().toISOString().split('T')[0]
  }
  // 然后从URL参数覆盖（URL优先级更高）
  initFromURL()
})
</script>

<style scoped>
.package-type-selector {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.package-form-input,
.package-form-select {
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.3s ease;
}

.package-form-input:focus,
.package-form-select:focus {
  outline: none;
  border-color: #1890ff;
}

.package-form-input.readonly {
  background: #f8f9fa;
  border-color: #e0e0e0;
  color: #666;
  cursor: default;
  user-select: none;
}

.radio-group {
  display: flex;
  gap: 16px;
  flex-wrap: nowrap;
  width: 100%;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  white-space: nowrap;
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: #fff;
  transition: all 0.3s ease;
  justify-content: center;
  min-height: 44px;
}

.radio-item:hover {
  border-color: #1890ff;
  background: #f0f9ff;
}

.radio-item input[type="radio"] {
  width: 18px;
  height: 18px;
  accent-color: #1890ff;
  margin: 0;
}

.radio-item input[type="radio"]:checked + .radio-label {
  color: #1890ff;
  font-weight: 600;
}

.radio-item:has(input[type="radio"]:checked) {
  border-color: #1890ff;
  background: #f0f9ff;
}

.radio-label {
  font-size: 16px;
  color: #1a1a1a;
  white-space: nowrap;
  user-select: none;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 16px;
  color: #1a1a1a;
}

.count-based-options,
.time-based-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #e3f2fd;
}

.preview-label {
  font-size: 14px;
  color: #666;
}

.preview-value {
  font-size: 14px;
  font-weight: 600;
  color: #1890ff;
}

.package-preview {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.preview-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 12px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-row .preview-label {
  font-size: 14px;
  color: #666;
}

.preview-row .preview-value {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a1a;
}

.package-type-suggestions {
  margin-top: 8px;
}

.form-suggestion-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.form-suggestion-chip {
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

.form-suggestion-chip:hover {
  background: #1989fa;
  color: #fff;
  transform: translateY(-1px);
}

.form-suggestion-chip.active {
  background: #1989fa;
  color: #fff;
}
</style>