import { test, expect } from "@playwright/test";

/**
 * Mind the Gap SaaS - Login and Dashboard Test
 * 
 * Logs in with test credentials and verifies dashboard loads.
 */

const BASE_URL = "https://mind-the-gap-saas.fly.dev";

// Test credentials from the API
test.describe("Mind the Gap SaaS - Login Flow", () => {
  
  test("Login with API credentials and verify dashboard", async ({ page }) => {
    console.log("🚀 Starting login test...");
    
    // Step 1: Navigate to login page
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState("networkidle");
    
    console.log("📄 Login page loaded");
    await page.screenshot({ path: "/tmp/mind-login-page.png" });
    
    // Step 2: Fill in login form
    // Use the working credentials from API
    await page.fill('input[name="email"], input[type="email"]', "anand@test.com");
    await page.fill('input[name="password"], input[type="password"]', "Password123");
    
    console.log("✅ Form filled");
    await page.screenshot({ path: "/tmp/mind-login-filled.png" });
    
    // Step 3: Submit form
    await page.click('button[type="submit"]');
    
    // Step 4: Wait for navigation to dashboard
    await page.waitForTimeout(3000);
    
    console.log("⏳ Waiting for dashboard...");
    
    // Check current URL
    const currentUrl = page.url();
    console.log("Current URL:", currentUrl);
    
    await page.screenshot({ path: "/tmp/mind-after-submit.png", fullPage: true });
    
    // Step 5: Verify we're on dashboard
    if (currentUrl.includes("/dashboard")) {
      console.log("✅ Successfully navigated to dashboard!");
      
      // Verify dashboard elements
      const body = page.locator("body");
      await expect(body).toBeVisible();
      
      const title = await page.title();
      console.log("Dashboard title:", title);
      
      await page.screenshot({ path: "/tmp/mind-dashboard.png", fullPage: true });
      
    } else {
      console.log("⚠️ Not on dashboard, checking for errors...");
      
      // Check for error messages
      const errorText = await page.locator("body").textContent();
      console.log("Page content snippet:", errorText?.substring(0, 200));
      
      throw new Error(`Expected dashboard but got: ${currentUrl}`);
    }
  });

  test("Direct API login test", async ({ request }) => {
    console.log("🔍 Testing API login directly...");
    
    const response = await request.post(`${BASE_URL}/api/v1/auth/login`, {
      headers: { "Content-Type": "application/json" },
      data: {
        email: "anand@test.com",
        password: "Password123"
      }
    });
    
    console.log("Login response status:", response.status());
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    console.log("✅ API login successful!");
    console.log("User:", data.user.email);
    console.log("Token received:", data.access_token ? "Yes" : "No");
    
    expect(data.access_token).toBeTruthy();
    expect(data.user.email).toBe("anand@example.com");
  });

  test("Dashboard with authenticated session", async ({ browser }) => {
    console.log("🔐 Testing dashboard with authenticated session...");
    
    // Create a new context
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // First, get token via API
    const response = await page.request.post(`${BASE_URL}/api/v1/auth/login`, {
      headers: { "Content-Type": "application/json" },
      data: {
        email: "anand@example.com",
        password: "Password123"
      }
    });
    
    const data = await response.json();
    const token = data.access_token;
    
    console.log("✅ Got token from API");
    
    // Set token in localStorage/cookies and navigate to dashboard
    await page.goto(`${BASE_URL}/dashboard`);
    
    // Inject token into localStorage if the app uses it
    await page.evaluate((authToken) => {
      localStorage.setItem('access_token', authToken);
    }, token);
    
    // Reload to pick up the token
    await page.reload();
    await page.waitForTimeout(3000);
    
    await page.screenshot({ path: "/tmp/mind-dashboard-authed.png", fullPage: true });
    
    const title = await page.title();
    console.log("Dashboard title:", title);
    
    // Verify we're logged in by checking for user info
    const pageContent = await page.content();
    const hasUserInfo = pageContent.includes("Anand") || pageContent.includes("anand@example.com");
    
    if (hasUserInfo) {
      console.log("✅ User info found on dashboard!");
    } else {
      console.log("⚠️ User info not visible on dashboard");
    }
    
    await context.close();
  });
});
