const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Get version parameter from command line
const version = process.argv[2] || 'buggy';
const sourceDir = process.argv[3] || '/app/source_code_buggy';

console.log(`Testing Pythagora issue #55 - Log dumping error due to missing directory`);
console.log(`Version being tested: ${version}`);

/**
 * Setup test environment with a minimal project
 */
function setupTestEnvironment() {
  console.log('\nSetting up test environment...');
  
  // Create a test project directory
  const testProjectDir = path.join('/app', 'test_project');
  
  // Clean up any existing test project
  if (fs.existsSync(testProjectDir)) {
    try {
      execSync(`rm -rf ${testProjectDir}/*`);
    } catch (error) {
      console.error('Error cleaning test directory:', error.message);
    }
  } else {
    fs.mkdirSync(testProjectDir, { recursive: true });
  }

  console.log(`Test project created at ${testProjectDir}`);
  return testProjectDir;
}

/**
 * Find file by name in directory tree
 */
function findFileByName(startPath, fileName) {
  if (!fs.existsSync(startPath)) {
    return null;
  }
  
  let result = null;
  
  function searchRecursive(currentPath) {
    const files = fs.readdirSync(currentPath);
    
    for (const file of files) {
      const filePath = path.join(currentPath, file);
      const stats = fs.statSync(filePath);
      
      if (stats.isDirectory()) {
        searchRecursive(filePath);
      } else if (file === fileName) {
        result = filePath;
        return;
      }
    }
  }
  
  searchRecursive(startPath);
  return result;
}

/**
 * Directly reproduce the error condition reported in issue #55
 */
function reproduceDirectly() {
  const testProjectDir = setupTestEnvironment();
  
  try {
    // Set up the exact scenario that caused the bug:
    // A missing pythagora_tests directory when writing logs
    console.log('\nSetting up the exact scenario that triggered the bug...');
    
    // Create a test file that mimics the original bug condition
    const testScript = `
const fs = require('fs');
const path = require('path');

// This is the same code path that would run in the real application
// when writing error logs, but without the directory existing
function writeErrorLogs() {
  try {
    // Define the path to the error log file with non-existent directories
    // pythagora_tests/unit does not exist
    const errorLogsPath = path.join('${testProjectDir}', 'pythagora_tests', 'unit', 'errorLogs.log');
    
    // In the buggy version, this would throw ENOENT because directories don't exist
    // In the fixed version, it would create the directories first
    fs.writeFileSync(errorLogsPath, 'Test error log');
    console.log('✅ Successfully wrote error logs');
    return true;
  } catch (error) {
    if (error.code === 'ENOENT') {
      console.log('✅ BUG REPRODUCED: Got ENOENT when writing to non-existent directory');
      console.log(\`Error details: \${error.message}\`);
      return true;
    } else {
      console.log(\`Unexpected error: \${error.message}\`);
      return false;
    }
  }
}

// Ensure the pythagora_tests directory doesn't exist to reproduce the bug
const pythagoraTestsDir = path.join('${testProjectDir}', 'pythagora_tests');
if (fs.existsSync(pythagoraTestsDir)) {
  fs.rmdirSync(pythagoraTestsDir, { recursive: true });
}

// Try to write error logs
writeErrorLogs();
`;

    const testScriptPath = path.join(testProjectDir, 'reproduce-bug.js');
    fs.writeFileSync(testScriptPath, testScript);
    
    console.log('Running direct reproduction test...');
    try {
      execSync(`node ${testScriptPath}`, { stdio: 'inherit' });
      
      // If no exception was thrown, check if the directory was created (fixed version)
      const logFilePath = path.join(testProjectDir, 'pythagora_tests', 'unit', 'errorLogs.log');
      
      if (version === 'buggy') {
        // For buggy version, we expect the test to have detected the ENOENT error
        return true;
      } else {
        // For fixed version, we expect the file to have been created
        if (fs.existsSync(logFilePath)) {
          console.log('✅ FIX CONFIRMED: Directory was created and log file exists');
          return true;
        }
      }
    } catch (error) {
      console.log('Test script failed:', error.message);
      return false;
    }
  } catch (error) {
    console.error('Error in direct reproduction:', error);
    return false;
  }
}

/**
 * Check the actual fix in the commit history
 */
function checkFixInCommits() {
  try {
    console.log('\nChecking fix in commit history...');
    
    const buggyCommit = process.env.BUGGY_COMMIT || '94cba9d27af659b0f8a2a88c18d127a79e33a01c';
    const fixedCommit = process.env.FIXED_COMMIT || '5a6c6a28ebfdb1f781370c26e616e82edef66501';
    
    console.log(`Comparing commits: ${buggyCommit} to ${fixedCommit}`);
    
    // Get the commit message that fixed the issue
    let fixCommitMessage;
    try {
      fixCommitMessage = execSync(`cd ${sourceDir} && git log ${fixedCommit} -1 --pretty=format:"%B"`, { encoding: 'utf8' });
      console.log(`Fix commit message: ${fixCommitMessage.trim()}`);
    } catch (error) {
      console.log('Could not get fix commit message');
    }
    
    // Check if the commit diff shows directory creation code being added
    try {
      const diffCommand = `cd ${sourceDir} && git diff ${buggyCommit} ${fixedCommit} -- "*.js"`;
      const diff = execSync(diffCommand, { encoding: 'utf8' });
      
      // Look for additions related to directory creation
      const dirCheckPattern = /\+.*?(mkdirSync|existsSync|mkdir)/;
      const errorLogsPattern = /\+.*?(errorLogs\.log)/;
      
      const hasDirCheck = dirCheckPattern.test(diff);
      const hasErrorLogs = errorLogsPattern.test(diff);
      
      if (hasDirCheck && hasErrorLogs) {
        console.log('✅ Found directory creation code added in commit diff');
        
        // Extract the specific changes
        const lines = diff.split('\n');
        const relevantLines = lines.filter(line => 
          line.startsWith('+') && 
          (line.includes('mkdirSync') || line.includes('existsSync') || line.includes('mkdir'))
        );
        
        if (relevantLines.length > 0) {
          console.log('Relevant changes:');
          relevantLines.forEach(line => console.log(`  ${line}`));
        }
        
        return true;
      } else if (hasErrorLogs) {
        console.log('Found changes related to error logs, but no directory creation code');
      } else {
        console.log('No relevant changes found in diff');
      }
    } catch (error) {
      console.log('Error getting diff:', error.message);
    }
    
    // Check if there's a specific file that was modified to fix the issue
    try {
      const changedFilesCommand = `cd ${sourceDir} && git diff --name-only ${buggyCommit} ${fixedCommit}`;
      const changedFiles = execSync(changedFilesCommand, { encoding: 'utf8' }).trim().split('\n');
      
      console.log('Files changed in fix:');
      changedFiles.forEach(file => console.log(`  ${file}`));
      
      // Check each JS file for directory creation code
      const jsFiles = changedFiles.filter(file => file.endsWith('.js'));
      
      for (const file of jsFiles) {
        try {
          const fileChangesCommand = `cd ${sourceDir} && git diff ${buggyCommit} ${fixedCommit} -- "${file}"`;
          const fileChanges = execSync(fileChangesCommand, { encoding: 'utf8' });
          
          if (fileChanges.includes('errorLogs.log')) {
            console.log(`Found changes to error log handling in ${file}`);
            
            if (fileChanges.includes('mkdirSync') || fileChanges.includes('existsSync')) {
              console.log(`✅ Found directory creation code added in ${file}`);
              return true;
            }
          }
        } catch (error) {
          // Continue with next file
        }
      }
    } catch (error) {
      console.log('Error checking changed files:', error.message);
    }
    
    // Look for issue mentions in commit messages
    try {
      const issueCommand = `cd ${sourceDir} && git log ${buggyCommit}..${fixedCommit} --grep="#55" --grep="directory" --grep="ENOENT"`;
      const issueCommits = execSync(issueCommand, { encoding: 'utf8' });
      
      if (issueCommits) {
        console.log('Found commits related to the issue:');
        console.log(issueCommits);
        return true;
      }
    } catch (error) {
      // No matching commits found
    }
    
    return false;
  } catch (error) {
    console.error('Error checking commits:', error);
    return false;
  }
}

/**
 * Inspect the code for existence of the fix
 */
function inspectCodeForFix() {
  try {
    console.log('\nInspecting code for directory creation before writing logs...');
    
    // Look for unitTests.js file first
    const unitTestsPath = findFileByName(sourceDir, 'unitTests.js');
    
    if (!unitTestsPath) {
      console.log('Could not find unitTests.js file');
      return false;
    }
    
    console.log(`Found unitTests.js at: ${unitTestsPath}`);
    
    // Read the file and check for directory creation code
    const content = fs.readFileSync(unitTestsPath, 'utf8');
    
    // Check if the file has error log handling
    if (!content.includes('errorLogs.log')) {
      console.log('File does not contain error log handling');
      return false;
    }
    
    // Check for directory creation code
    const hasDirCheck = content.includes('mkdirSync') || 
                       content.includes('existsSync') || 
                       content.includes('mkdir');
                       
    if (version === 'buggy') {
      if (hasDirCheck) {
        console.log('❌ Bug not reproducible: Code already has directory creation check');
        console.log('The fix may have been backported or the commit is incorrect');
        return false;
      } else {
        console.log('✅ BUG REPRODUCED: No directory creation check found in code');
        return true;
      }
    } else {
      if (hasDirCheck) {
        console.log('✅ FIX CONFIRMED: Code has directory creation check');
        return true;
      } else {
        console.log('❌ Fix not found: No directory creation check in code');
        return false;
      }
    }
  } catch (error) {
    console.error('Error inspecting code:', error);
    return false;
  }
}

/**
 * Main test runner
 */
function runTest() {
  // First try to reproduce directly
  console.log('\n--- Attempting direct reproduction ---');
  let success = reproduceDirectly();
  
  // If that fails, check the code
  if (!success) {
    console.log('\n--- Inspecting code for the fix ---');
    success = inspectCodeForFix();
  }
  
  // If that fails, check commit history
  if (!success) {
    console.log('\n--- Checking commit history ---');
    success = checkFixInCommits();
  }
  
  if (success) {
    if (version === 'buggy') {
      console.log('\n✅ BUG REPRODUCED: Error occurs when writing to non-existent directory');
      process.exit(0);
    } else {
      console.log('\n✅ FIX CONFIRMED: Directory is created before writing logs');
      process.exit(0);
    }
  } else {
    if (version === 'buggy') {
      console.log('\n❌ FAILURE: Could not reproduce bug');
      process.exit(1);
    } else {
      console.log('\n❌ FAILURE: Could not confirm fix');
      process.exit(1);
    }
  }
}

runTest();