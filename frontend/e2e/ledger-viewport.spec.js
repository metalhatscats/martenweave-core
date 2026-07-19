import { test, expect } from "@playwright/test";

const BASE_URL = "http://127.0.0.1:5173";

/**
 * Regression spec for ledger columns clipping at a 1280px viewport: the
 * responsive band must drop the "Updated" column and relax the 920px minimum
 * row width so the remaining seven columns fit without horizontal overflow.
 */
test.describe("ledger viewport", () => {
  test.use({ viewport: { width: 1280, height: 720 } });

  test("ledger columns fit without horizontal overflow at 1280px", async ({ page }) => {
    await page.goto(`${BASE_URL}/#/home`);
    const table = page.locator(".ledger-table");
    await page.waitForSelector(".ledger-row", { timeout: 15000 });

    const ownerHeader = table.locator(".ledger-table-head > span", { hasText: "Owner" });
    await expect(ownerHeader).toBeVisible();

    const metrics = await table.evaluate((el) => ({
      scrollWidth: el.scrollWidth,
      clientWidth: el.clientWidth,
    }));
    expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.clientWidth + 1);
  });
});
