/**
 * 套餐服务
 * 处理套餐类型相关的业务逻辑
 */

export class PackageService {
  // 套餐类别
  static PACKAGE_CATEGORIES = {
    count_based: '记次套餐',
    time_based: '时长套餐'
  }

  // 时长套餐类型
  static DURATION_TYPES = {
    monthly: '月卡',
    quarterly: '季卡',
    yearly: '年卡',
    custom: '自定义'
  }

  /**
   * 计算套餐到期时间
   * @param {string} durationType 时长类型
   * @param {Date} startDate 开始时间
   * @param {number} customDays 自定义天数
   * @returns {Date|null} 到期时间
   */
  static calculatePackageEndDate(durationType, startDate = new Date(), customDays = null) {
    if (!startDate) {
      startDate = new Date()
    }

    const endDate = new Date(startDate)

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
        } else {
          return null
        }
        break
      default:
        return null
    }

    return endDate
  }

  /**
   * 获取套餐状态文本
   * @param {Object} packageData 套餐数据
   * @returns {string} 状态文本
   */
  static getPackageStatusText(packageData) {
    const packageCategory = packageData.package_category || 'count_based'

    if (packageCategory === 'count_based') {
      // 记次套餐
      const remaining = packageData.remaining_lessons || 0
      const total = packageData.total_lessons || 0
      return `${remaining}/${total}次`
    } else {
      // 时长套餐
      if (packageData.unlimited_access) {
        return '永久有效'
      }

      const packageEndDate = packageData.package_end_date
      if (!packageEndDate) {
        return '永久有效'
      }

      // 处理字符串格式的日期
      let endDate
      if (typeof packageEndDate === 'string') {
        endDate = new Date(packageEndDate)
      } else {
        endDate = packageEndDate
      }

      if (isNaN(endDate.getTime())) {
        return '无效日期'
      }

      const now = new Date()
      const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24))

      if (daysLeft <= 0) {
        return '已过期'
      } else if (daysLeft <= 30) {
        return `${daysLeft}天后过期`
      } else {
        return endDate.toLocaleDateString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit'
        }) + '到期'
      }
    }
  }

  /**
   * 检查套餐是否有效
   * @param {Object} packageData 套餐数据
   * @returns {boolean} 是否有效
   */
  static isPackageValid(packageData) {
    const packageCategory = packageData.package_category || 'count_based'

    if (packageCategory === 'count_based') {
      // 记次套餐：检查剩余课程
      const remaining = packageData.remaining_lessons || 0
      return remaining > 0
    } else {
      // 时长套餐：检查到期时间
      if (packageData.unlimited_access) {
        return true
      }

      const packageEndDate = packageData.package_end_date
      if (!packageEndDate) {
        return true
      }

      // 处理字符串格式的日期
      let endDate
      if (typeof packageEndDate === 'string') {
        endDate = new Date(packageEndDate)
      } else {
        endDate = packageEndDate
      }

      if (isNaN(endDate.getTime())) {
        return false
      }

      return new Date() <= endDate
    }
  }

  /**
   * 处理创建学生时的套餐数据
   * @param {Object} createData 创建数据
   * @returns {Object} 处理后的数据
   */
  static processPackageDataForCreation(createData) {
    const packageCategory = createData.package_category || 'count_based'

    // 设置兼容字段
    const processedData = { ...createData }
    processedData.package_type = createData.original_package_type || '1v1'

    if (packageCategory === 'count_based') {
      // 记次套餐：设置初始剩余课程数
      const totalLessons = createData.total_lessons || 0
      processedData.remaining_lessons = totalLessons
      // 清空时长套餐相关字段
      processedData.package_end_date = null
      processedData.package_duration_type = null
      processedData.package_duration_days = null
      processedData.unlimited_access = false
    } else {
      // 时长套餐：计算到期时间
      const durationType = createData.package_duration_type
      const customDays = createData.package_duration_days
      const unlimited = createData.unlimited_access || false

      if (!unlimited && durationType) {
        const endDate = this.calculatePackageEndDate(durationType, new Date(), customDays)
        processedData.package_end_date = endDate
      } else {
        processedData.package_end_date = null
      }

      // 清空记次套餐相关字段
      processedData.total_lessons = null
      processedData.remaining_lessons = null
    }

    return processedData
  }

  /**
   * 获取套餐显示信息
   * @param {Object} packageData 套餐数据
   * @returns {Object} 显示信息
   */
  static getPackageInfoDisplay(packageData) {
    const packageCategory = packageData.package_category || 'count_based'
    const originalPackageType = packageData.original_package_type || '1v1'

    const result = {
      category: this.PACKAGE_CATEGORIES[packageCategory] || packageCategory,
      type: originalPackageType === '1v1' ? '一对一' : '一对多',
      status: this.getPackageStatusText(packageData),
      valid: this.isPackageValid(packageData) ? '有效' : '无效'
    }

    if (packageCategory === 'time_based') {
      const durationType = packageData.package_duration_type
      if (durationType) {
        result.duration = this.DURATION_TYPES[durationType] || durationType
      }

      if (packageData.unlimited_access) {
        result.duration = '永久'
      }
    }

    return result
  }

  /**
   * 验证套餐数据
   * @param {Object} packageData 套餐数据
   * @returns {Array} 错误信息数组
   */
  static validatePackageData(packageData) {
    const errors = []
    const packageCategory = packageData.package_category || 'count_based'

    if (packageCategory === 'count_based') {
      const totalLessons = packageData.total_lessons
      if (!totalLessons || totalLessons <= 0) {
        errors.push('记次套餐必须设置总课程数')
      }
    } else {
      const durationType = packageData.package_duration_type
      const unlimited = packageData.unlimited_access

      if (!unlimited && !durationType) {
        errors.push('时长套餐必须选择时长类型或设置永久有效')
      }

      if (durationType === 'custom') {
        const customDays = packageData.package_duration_days
        if (!customDays || customDays <= 0) {
          errors.push('自定义时长套餐必须设置有效天数')
        }
      }
    }

    return errors
  }
}