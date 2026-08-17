import js from '@eslint/js'
import pluginVue from 'eslint-plugin-vue'
import globals from 'globals'

export default [
  { ignores: ['dist'] },
  js.configs.recommended,
  ...pluginVue.configs['flat/essential'],
  {
    rules: {
      // 单词组件名是路由视图惯例（Login/Students/Toast），重命名波及路由与引用
      'vue/multi-word-component-names': 'off',
    },
  },
  {
    languageOptions: {
      globals: { ...globals.browser, ...globals.node },
    },
    rules: {
      'max-lines': ['error', { max: 500, skipBlankLines: true, skipComments: true }],
      'max-params': ['error', 5],
      'max-lines-per-function': ['warn', { max: 120, skipBlankLines: true, skipComments: true }],
      complexity: ['warn', 15],
    },
  },
  {
    // 存量基线，只减不增：文件行数超限的组件豁免 max-lines
    files: [
      'src/components/student/StudentDetailCards.vue',
      'src/views/CalendarAppointment.vue',
    ],
    rules: {
      'max-lines': 'off',
    },
  },
]
