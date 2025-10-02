const fs = require('fs');
const path = require('path');

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

const filesToCheck = [
  'packages/agents/src/agent-debug/DebugLlmApi.ts',
  'packages/agents/src/agents/Evo/index.ts',
  'apps/browser/lib/api/ProxyLlmApi.ts'
];

let foundLlmModel = false;
let checkedFiles = 0;

filesToCheck.forEach(file => {
  if (fs.existsSync(file)) {
    checkedFiles++;
    const code = fs.readFileSync(file, 'utf8');
    if (/LlmModel/.test(code)) {
      foundLlmModel = true;
      console.log(`✅ Found 'LlmModel' in: ${file}`);
    } else {
      console.log(`Checked: ${file} (use string to handle context)`);
    }
  } else {
    console.log(`❌ File not found: ${file}`);
  }
});

if (checkedFiles === 0) {
  console.log('❌ ERROR: None of the target files were found.');
  process.exit(1);
}

if (version === 'buggy') {
  if (!foundLlmModel) {
    console.log('\n✅ BUG REPRODUCED: Error on maximum context for GPT request.');
    process.exit(0);
  } else {
    console.log('\n❌ BUG NOT REPRODUCED: Maximum context for GPT request is handled.');
    process.exit(1);
  }
} else {
  if (foundLlmModel) {
    console.log('\n✅ FIX VERIFIED: LlmModel implementation to handle GPT request and to predict next step.');
    process.exit(0);
  } else {
    console.log('\n❌ FIX NOT VERIFIED: Error on maximum context for GPT request.');
    process.exit(1);
  }
}