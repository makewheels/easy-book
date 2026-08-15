import { defineConfig } from '@playwright/test';

// 移动端视口（与 App 430px 布局一致），对已部署环境做冒烟走查
export default defineConfig({
  testDir: './tests',
  timeout: 60_000,
  retries: 1,
  reporter: [['list']],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'https://easybook.a4.fit',
    viewport: { width: 430, height: 900 },
    deviceScaleFactor: 2,
    trace: 'retain-on-failure',
  },
});
