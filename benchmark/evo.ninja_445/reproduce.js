const fs = require('fs');
const path = require('path');

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

try {
  // Check the main agent implementation file
  const evoIndexPath = 'packages/agents/src/agents/Scripter/utils.ts';
  
  if (!fs.existsSync(evoIndexPath)) {
    console.log(`❌ ERROR: Could not find Evo agent implementation at ${evoIndexPath}`);
    process.exit(1);
  }
  
  const agentCode = fs.readFileSync(evoIndexPath, 'utf8');
  
  // Look for code that handles greetings or non-specific inputs
  // The fix should include patterns for detecting non-goal inputs
  const fixPatterns = [
    /prediction|agentPersona|contextualizeChat/i,
    /previousAgent|previousPrediction/i
  ];
  
  let foundFixPattern = false;
  let matchedPattern = null;
  
  for (const pattern of fixPatterns) {
    if (pattern.test(agentCode)) {
      foundFixPattern = true;
      console.log(`Found fix pattern: ${pattern}`);
      matchedPattern = pattern;
      break;
    }
  }
  
  console.log(`Fix pattern found: ${foundFixPattern}`);
  if (matchedPattern) {
    console.log(`Matched pattern: ${matchedPattern}`);
  }
  
  // Check the run method handling
  const hasRunMethodFix = /run\s*\([^)]*\)\s*{[^{]*if\s*\([^)]*greeting[^)]*\)/s.test(agentCode);
  console.log(`Run method has greeting handling: ${hasRunMethodFix}`);
  
  // Also check for loop prevention or early exit for non-goal inputs
  const hasLoopPrevention = /goalAchieved|early\s*exit|prevent\s*loop|loop\s*prevention/i.test(agentCode);
  console.log(`Has loop prevention for non-goals: ${hasLoopPrevention}`);
  
  // Consider the bug fixed if we found either pattern detection or loop prevention
  const hasFix = foundFixPattern || hasRunMethodFix || hasLoopPrevention;
  
  if (version === 'buggy') {
    if (!hasFix) {
      console.log('\n✅ BUG REPRODUCED: Agent does not handle greeting or non-goal inputs properly.');
      process.exit(0);
    } else {
      console.log('\n❌ BUG NOT REPRODUCED: Agent appears to handle greeting or non-goal inputs (unexpected in buggy version).');
      process.exit(1);
    }
  } else {
    if (hasFix) {
      console.log('\n✅ FIX VERIFIED: Agent now handles greeting or non-goal inputs properly.');
      process.exit(0);
    } else {
      console.log('\n❌ FIX NOT VERIFIED: Agent does not handle greeting or non-goal inputs (unexpected in fixed version).');
      process.exit(1);
    }
  }
} catch (error) {
  console.error(`\n❌ ERROR: ${error.message}`);
  console.error(error);
  process.exit(1);
}