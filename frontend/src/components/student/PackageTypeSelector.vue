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

    <!-- 原套餐类型 -->
    <div class="form-group">
      <label class="form-label">课程类型 *</label>
      <select v-model="packageData.original_package_type" class="package-form-select">
        <option value="1v1">一对一</option>
        <option value="1v多">一对多</option>
      </select>
    </div>

    <!-- 记次套餐选项 -->
    <div v-if="packageData.package_category === 'count_based'" class="count-based-options">
      <div class="form-group">
        <label class="form-label">总课程数 *</label>
        <input
          type="number"
          v-model.number="packageData.total_lessons"
          min="1"
          class="package-form-input"
          placeholder="请输入总课程数"
        />
      </div>
    </div>

    <!-- 时长套餐选项 -->
    <div v-else class="time-based-options">
      <div class="form-group">
        <label class="form-label">时长类型</label>
        <select
          v-model="packageData.package_duration_type"
          @change="onDurationTypeChange"
          class="package-form-select"
        >
          <option value="">请选择</option>
          <option value="monthly">月卡</option>
          <option value="quarterly">季卡</option>
          <option value="yearly">年卡</option>
          <option value="custom">自定义</option>
        </select>
      </div>

      <!-- 自定义天数 -->
      <div v-if="packageData.package_duration_type === 'custom'" class="form-group">
        <label class="form-label">有效天数 *</label>
        <input
          type="number"
          v-model.number="packageData.package_duration_days"
          min="1"
          class="package-form-input"
          placeholder="请输入有效天数"
        />
      </div>

      <!-- 无限制选项 -->
      <div class="form-group">
        <label class="checkbox-item">
          <input
            type="checkbox"
            v-model="packageData.unlimited_access"
          />
          <span class="checkbox-label">永久有效</span>
        </label>
      </div>

      <!-- 预览到期时间 -->
      <div v-if="showPreviewEndDate" class="preview-info">
        <div class="preview-label">预计到期时间：</div>
        <div class="preview-value">{{ previewEndDate }}</div>
      </div>
    </div>

    <!-- 套餐信息预览 -->
    <div class="package-preview">
      <div class="preview-title">套餐信息预览</div>
      <div class="preview-content">
        <div class="preview-row">
          <span class="preview-label">套餐类别：</span>
          <span class="preview-value">{{ packageCategoryText }}</span>
        </div>
        <div class="preview-row">
          <span class="preview-label">课程类型：</span>
          <span class="preview-value">{{ originalPackageTypeText }}</span>
        </div>
        <div v-if="packageData.package_category === 'count_based'" class="preview-row">
          <span class="preview-label">课程数量：</span>
          <span class="preview-value">{{ packageData.total_lessons || 0 }}次</span>
        </div>
        <div v-else class="preview-row">
          <span class="preview-label">套餐类型：</span>
          <span class="preview-value">{{ durationTypeText }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { PackageService } from '@/services/package'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

// 套餐数据
const packageData = ref({
  package_category: 'count_based',
  original_package_type: '1v1',
  total_lessons: null,
  package_duration_type: '',
  package_duration_days: null,
  unlimited_access: false
})

// 计算属性
const packageCategoryText = computed(() => {
  return packageData.value.package_category === 'count_based' ? '记次套餐' : '时长套餐'
})

const originalPackageTypeText = computed(() => {
  return packageData.value.original_package_type === '1v1' ? '一对一' : '一对多'
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
         packageData.value.package_duration_type &&
         !packageData.value.unlimited_access
})

const previewEndDate = computed(() => {
  if (!showPreviewEndDate.value) return ''

  try {
    const endDate = PackageService.calculatePackageEndDate(
      packageData.value.package_duration_type,
      new Date(),
      packageData.value.package_duration_days
    )
    return endDate ? endDate.toLocaleDateString('zh-CN') : ''
  } catch (error) {
    return '计算错误'
  }
})

// 方法
const onCategoryChange = () => {
  // 切换类别时重置相关字段
  if (packageData.value.package_category === 'count_based') {
    packageData.value.package_duration_type = ''
    packageData.value.package_duration_days = null
    packageData.value.unlimited_access = false
  } else {
    packageData.value.total_lessons = null
  }
  emitUpdate()
}

const onDurationTypeChange = () => {
  // 切换时长类型时重置自定义天数
  if (packageData.value.package_duration_type !== 'custom') {
    packageData.value.package_duration_days = null
  }
  emitUpdate()
}

const emitUpdate = () => {
  emit('update:modelValue', { ...packageData.value })
}

// 监听变化
watch(packageData, emitUpdate, { deep: true })

// 初始化
if (props.modelValue) {
  Object.assign(packageData.value, props.modelValue)
}
</script>

<style scoped>
.package-type-selector {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
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

.radio-group {
  display: flex;
  gap: 20px;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.radio-label {
  font-size: 16px;
  color: #1a1a1a;
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
  padding-left: 20px;
  border-left: 3px solid #e0e0e0;
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
</style>