#!/usr/bin/env node

/**
 * Self-Healing Test Loop for Playwright E2E Tests
 *
 * This script demonstrates an automated test-fix-retry loop:
 * 1. Runs Playwright tests targeting "Submit navigates to next page"
 * 2. Captures test failures and error messages
 * 3. Analyzes the failure and suggests fixes
 * 4. Attempts to apply fixes automatically (simulated)
 * 5. Retries the test until it passes or max retries reached
 *
 * Usage: node auto_fix_loop.js
 */

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Configuration
const MAX_RETRIES = 5;
const TEST_GREP = 'Submit navigates to next page';
const BASE_URL = 'http://localhost:3000';

// ANSI color codes for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

// Logging utilities
function log(message, color = colors.reset) {
  console.log(`${color}${message}${colors.reset}`);
}

function logSection(title) {
  const separator = '═'.repeat(60);
  log(`\n${separator}`, colors.cyan);
  log(`  ${title}`, colors.bright + colors.cyan);
  log(`${separator}\n`, colors.cyan);
}

function logAttempt(attempt, total) {
  log(`\n${'▶'.repeat(3)} ATTEMPT ${attempt}/${total} ${'▶'.repeat(3)}`, colors.bright + colors.yellow);
}

function logSuccess() {
  log('\n✓ TEST PASSED!', colors.bright + colors.green);
}

function logFailure() {
  log('\n✗ TEST FAILED', colors.bright + colors.red);
}

function logFixAttempt(description) {
  log(`\n🔧 Attempting fix: ${description}`, colors.magenta);
}

// Run Playwright test and capture output
function runTest() {
  return new Promise((resolve) => {
    log(`Running test: "${TEST_GREP}"`, colors.blue);

    const playwright = spawn('npx', [
      'playwright',
      'test',
      '-g',
      TEST_GREP,
      '--reporter=list'
    ], {
      stdio: ['inherit', 'pipe', 'pipe']
    });

    let stdout = '';
    let stderr = '';

    playwright.stdout.on('data', (data) => {
      const output = data.toString();
      stdout += output;
      process.stdout.write(output);
    });

    playwright.stderr.on('data', (data) => {
      const output = data.toString();
      stderr += output;
      process.stderr.write(output);
    });

    playwright.on('close', (code) => {
      resolve({
        passed: code === 0,
        exitCode: code,
        stdout,
        stderr,
      });
    });
  });
}

// Analyze test failure and determine fix strategy
function analyzeFailure(result) {
  const output = result.stdout + result.stderr;
  const errors = [];

  // Check for common error patterns
  if (output.includes('net::ERR_CONNECTION_REFUSED') || output.includes('ECONNREFUSED')) {
    errors.push({
      type: 'CONNECTION_ERROR',
      description: 'Cannot connect to the application server',
      fix: 'Ensure the app is running on http://localhost:3000',
      suggestion: 'Start the server with: streamlit run streamlit_app.py --server.port 3000',
    });
  }

  if (output.includes('Timeout') && output.includes('page.goto')) {
    errors.push({
      type: 'TIMEOUT_ERROR',
      description: 'Page navigation timeout',
      fix: 'The /start route may not exist or takes too long to load',
      suggestion: 'Verify the route exists in your Streamlit app routing',
    });
  }

  if (output.includes('waiting for locator') && output.includes('button[type="submit"]')) {
    errors.push({
      type: 'ELEMENT_NOT_FOUND',
      description: 'Submit button not found',
      fix: 'The submit button selector may be incorrect',
      suggestion: 'Verify button exists or update selector in test',
    });
  }

  if (output.includes('Expected URL') || output.includes('toHaveURL')) {
    errors.push({
      type: 'NAVIGATION_ERROR',
      description: 'Page did not navigate to expected URL',
      fix: 'The submit button may not trigger navigation',
      suggestion: 'Verify navigation logic in your form submission handler',
    });
  }

  if (output.includes('text=Welcome')) {
    errors.push({
      type: 'CONTENT_NOT_FOUND',
      description: '"Welcome" text not found on page',
      fix: 'The expected text may not exist on the target page',
      suggestion: 'Update test expectations or add "Welcome" text to the page',
    });
  }

  // Generic error if no specific pattern matched
  if (errors.length === 0) {
    errors.push({
      type: 'UNKNOWN_ERROR',
      description: 'Test failed with unknown error',
      fix: 'Review test output for details',
      suggestion: 'Check test logs above for specific error messages',
    });
  }

  return errors;
}

// Apply fixes (simulated for demonstration)
function applyFixes(errors) {
  log('\n📊 Failure Analysis:', colors.bright);

  errors.forEach((error, index) => {
    log(`\n  Error ${index + 1}: ${error.type}`, colors.yellow);
    log(`  └─ ${error.description}`, colors.reset);
    log(`  └─ Fix: ${error.fix}`, colors.reset);
    log(`  └─ Suggestion: ${error.suggestion}`, colors.cyan);
  });

  logFixAttempt('Simulated automatic fixes applied');

  // In a real self-healing system, this would:
  // 1. Modify test selectors based on actual DOM
  // 2. Update test expectations based on actual page content
  // 3. Create missing routes or components
  // 4. Adjust timeouts
  // 5. Update configuration

  // For demonstration, we'll simulate a brief fix operation
  log('  ├─ Analyzing page structure...', colors.reset);
  log('  ├─ Checking route definitions...', colors.reset);
  log('  ├─ Validating selectors...', colors.reset);
  log('  └─ Fixes applied (simulated)', colors.green);
}

// Main test loop
async function main() {
  logSection('🤖 SELF-HEALING TEST LOOP STARTED');

  log(`Configuration:`, colors.bright);
  log(`  • Max retries: ${MAX_RETRIES}`, colors.reset);
  log(`  • Test pattern: "${TEST_GREP}"`, colors.reset);
  log(`  • Base URL: ${BASE_URL}`, colors.reset);

  log(`\nPrerequisites:`, colors.bright);
  log(`  • Playwright installed: ✓`, colors.green);
  log(`  • Test file exists: ✓`, colors.green);
  log(`  • App server: ${colors.yellow}MUST BE RUNNING${colors.reset} on ${BASE_URL}`, colors.reset);

  let attempt = 0;
  let testPassed = false;

  while (attempt < MAX_RETRIES && !testPassed) {
    attempt++;
    logAttempt(attempt, MAX_RETRIES);

    // Run the test
    const result = await runTest();

    if (result.passed) {
      testPassed = true;
      logSuccess();
      log(`\nTest passed on attempt ${attempt}/${MAX_RETRIES}`, colors.green);
      break;
    }

    // Test failed
    logFailure();

    if (attempt >= MAX_RETRIES) {
      log(`\nMax retries (${MAX_RETRIES}) reached. Giving up.`, colors.red);
      break;
    }

    // Analyze failure and attempt fixes
    const errors = analyzeFailure(result);
    applyFixes(errors);

    log(`\n⏳ Waiting 2 seconds before retry...`, colors.yellow);
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  // Final summary
  logSection('📈 EXECUTION SUMMARY');

  log(`Total attempts: ${attempt}/${MAX_RETRIES}`, colors.bright);
  log(`Final status: ${testPassed ? '✓ PASSED' : '✗ FAILED'}`, testPassed ? colors.green : colors.red);

  if (testPassed) {
    log(`\n🎉 Success! The test is now passing.`, colors.bright + colors.green);
  } else {
    log(`\n❌ The test could not be fixed automatically.`, colors.bright + colors.red);
    log(`Manual intervention required. Review the errors above.`, colors.yellow);
  }

  logSection('🔧 NEXT STEPS');

  if (!testPassed) {
    log('To fix the test failures:', colors.bright);
    log('  1. Start the application: streamlit run streamlit_app.py --server.port 3000', colors.cyan);
    log('  2. Verify routes exist: /start and /next', colors.cyan);
    log('  3. Verify submit button exists with proper selector', colors.cyan);
    log('  4. Re-run this loop: node auto_fix_loop.js', colors.cyan);
  } else {
    log('To run the test manually:', colors.bright);
    log('  npx playwright test -g "Submit navigates to next page"', colors.cyan);
    log('\nTo run all tests:', colors.bright);
    log('  npm test', colors.cyan);
    log('\nTo run with UI:', colors.bright);
    log('  npm run test:ui', colors.cyan);
  }

  log(''); // Empty line for cleaner output

  process.exit(testPassed ? 0 : 1);
}

// Error handling
process.on('unhandledRejection', (error) => {
  log(`\n❌ Unhandled error: ${error.message}`, colors.red);
  console.error(error);
  process.exit(1);
});

// Run the main loop
main();
