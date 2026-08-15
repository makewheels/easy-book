import { test, expect } from '@playwright/test';

const PHONE = process.env.E2E_PHONE || '13800138000';
const PASSWORD = process.env.E2E_PASSWORD || '';

// 记录数据接口的鉴权/服务器错误，用于断言"登录后不应 401"
const trackApiErrors = (page, bucket) => {
  page.on('response', (r) => {
    const url = r.url();
    if (url.includes('/api/') && (r.status() === 401 || r.status() === 500)) {
      bucket.push(`${r.status()} ${url}`);
    }
  });
};

const login = async (page) => {
  await page.goto('/login');
  await expect(page.getByText('手机号')).toBeVisible();
  await page.fill('input[type=tel]', PHONE);
  await page.fill('input[type=password]', PASSWORD);
  await page.click('button[type=submit]');
  await page.waitForURL(/\/$/, { timeout: 15000 });
};

test.describe('登录与全局导航', () => {
  test('登录页渲染且登录成功跳转首页', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByText('泳课预约系统')).toBeVisible();
    await expect(page.getByText('手机号')).toBeVisible();
    await login(page);
    await expect(page.locator('.bottom-nav')).toBeVisible();
  });

  test('登录后数据接口不应 401/500', async ({ page }) => {
    const apiErrors = [];
    trackApiErrors(page, apiErrors);
    await login(page);
    await page.waitForTimeout(2500); // 等课表批量取数完成
    expect(apiErrors, `发现鉴权/服务器错误:\n${apiErrors.join('\n')}`).toEqual([]);
  });

  test('底部导航在课表/学员/AI 三个页签都保留', async ({ page }) => {
    await login(page);
    // 课表
    await expect(page.locator('.bottom-nav .nav-item')).toHaveCount(3);
    // 学员
    await page.click('.bottom-nav .nav-item:has-text("学员")');
    await expect(page.getByText('学员管理')).toBeVisible();
    await expect(page.locator('.bottom-nav .nav-item')).toHaveCount(3);
    // AI 助手
    await page.click('.bottom-nav .nav-item:has-text("AI")');
    await page.waitForTimeout(3000);
    await expect(page.locator('.bottom-nav .nav-item')).toHaveCount(3);
    // 回课表
    await page.click('.bottom-nav .nav-item:has-text("课表")');
    await expect(page.locator('.bottom-nav .nav-item:has-text("课表")')).toHaveClass(/active/);
  });
});

test.describe('AI 助手（iframe 嵌入）', () => {
  test('iframe 加载 Chainlit 且欢迎语出现', async ({ page }) => {
    await login(page);
    await page.click('.bottom-nav .nav-item:has-text("AI")');
    const frame = page.frameLocator('iframe.assistant-frame');
    await expect(frame.getByText('泳课管理 AI 助手')).toBeVisible({ timeout: 15000 });
  });
});
