// UI 自主走查：移动视口登录并逐页截图，收集控制台/页面错误
import { chromium } from 'playwright';
import fs from 'node:fs';

const BASE = 'https://easybook.a4.fit';
const SHOT_DIR = new URL('./shots/', import.meta.url).pathname;
fs.mkdirSync(SHOT_DIR, { recursive: true });

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 430, height: 900 },
  deviceScaleFactor: 2,
});
const page = await ctx.newPage();

const problems = [];
page.on('console', (m) => {
  if (m.type() === 'error') problems.push(`[console] ${m.text().slice(0, 200)}`);
});
page.on('pageerror', (e) => problems.push(`[pageerror] ${String(e).slice(0, 200)}`));
page.on('requestfailed', (r) => problems.push(`[net-fail] ${r.url().slice(0, 120)} :: ${r.failure()?.errorText}`));

const shot = async (name, full = true) => {
  await page.screenshot({ path: `${SHOT_DIR}${name}.png`, fullPage: full });
  console.log('📸', name);
};

// 1. 登录页
await page.goto(`${BASE}/login`, { waitUntil: 'networkidle' });
await shot('01-login');

// 2. 登录
await page.fill('input[type=tel]', '13800138000');
await page.fill('input[type=password]', 'gMwsxpTON8EoRA');
await page.click('button[type=submit]');
await page.waitForURL(`${BASE}/`, { timeout: 15000 });
await page.waitForTimeout(2000);
await shot('02-home-calendar');

// 3. 学员页
await page.click('.bottom-nav .nav-item:has-text("学员")');
await page.waitForTimeout(1500);
await shot('03-students');

// 4. 学员详情（如果有学员）
const studentCard = page.locator('.student-item, .student-card, [class*=student]').first();
if (await studentCard.count()) {
  try {
    await studentCard.click();
    await page.waitForTimeout(1500);
    await shot('04-student-detail');
    await page.goBack();
    await page.waitForTimeout(1000);
  } catch { /* 点不进去就跳过 */ }
}

// 5. AI 助手（iframe 嵌入页）
await page.click('.bottom-nav .nav-item:has-text("AI")');
await page.waitForTimeout(4000);
await shot('05-assistant', false);

// iframe 内部是否正常加载
const frame = page.frameLocator('iframe.assistant-frame');
try {
  const bodyText = await frame.locator('body').innerText({ timeout: 5000 });
  console.log('iframe 内容前 100 字:', bodyText.replace(/\s+/g, ' ').slice(0, 100));
} catch (e) {
  problems.push(`[iframe] 内容加载失败: ${String(e).slice(0, 150)}`);
}

// 6. 回到课表
await page.click('.bottom-nav .nav-item:has-text("课表")');
await page.waitForTimeout(1500);
await shot('06-back-to-calendar');

console.log('\n=== 收集到的问题 ===');
console.log(problems.length ? problems.join('\n') : '（无控制台/网络错误）');

await browser.close();
