const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const browser = await chromium.launch();
  const device = { name: 'iPhone-14', width: 390, height: 844 };

  const context = await browser.newContext({
    viewport: { width: device.width, height: device.height },
    deviceScaleFactor: 2,
  });

  const page = await context.newPage();
  const filePath = 'file://' + path.resolve(__dirname, 'Relocation_Analysis_Hodges_Family_v2.html');
  await page.goto(filePath);
  await page.waitForTimeout(1500);

  // Screenshot the Why Leave section with new immigration updates
  await page.screenshot({ path: `updated-why-leave.png`, fullPage: true });
  console.log('✓ Why Leave section (with immigration updates)');

  // Click to Tier 1 and screenshot
  await page.click('#nav-tier1');
  await page.waitForTimeout(500);
  await page.screenshot({ path: `updated-tier1.png`, fullPage: true });
  console.log('✓ Tier 1 Countries (with update notices)');

  await context.close();
  await browser.close();
  console.log('\n✅ Updated screenshots captured!');
})();
