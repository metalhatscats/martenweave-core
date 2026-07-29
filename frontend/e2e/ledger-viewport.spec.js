import { test, expect } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5173";

/**
 * The Catalog replaced the retired ledger route. Keep the regression focused
 * on the live canonical-results surface: it must not create horizontal
 * overflow at a standard 1280px desktop viewport.
 */
test.describe("catalog viewport", () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  test("catalog results fit without horizontal overflow at 1280px", async ({ page }) => {
    await page.goto(`${BASE_URL}/#/models`);
    const results = page.locator(".result-list");
    await page.waitForSelector(".result-row", { timeout: 15000 });

    await expect(results).toBeVisible();

    const metrics = await results.evaluate((el) => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
    }));
    expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.clientWidth + 1);
  });
});
