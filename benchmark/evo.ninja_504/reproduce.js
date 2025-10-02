const fs = require('fs');
const path = require('path');

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

const possiblePaths = [
  'apps/browser/src/api/ProxyEmbeddingApi.ts'
];

let embeddingApiFile = null;
for (const filePath of possiblePaths) {
  if (fs.existsSync(filePath)) {
    console.log(`Found embedding API file at: ${filePath}`);
    embeddingApiFile = filePath;
    break;
  }
}

if (!embeddingApiFile) {
  console.log('❌ Could not find embedding API file.');
  process.exit(1);
}

const fileContent = fs.readFileSync(embeddingApiFile, 'utf8');

const modelConfigPattern = /modelConfig\s*:\s*\{[^}]*maxTokensPerInput[^}]*maxInputsPerRequest[^}]*\}/s;
const hasModelConfigFix = modelConfigPattern.test(fileContent);

console.log(`modelConfig with maxTokensPerInput and maxInputsPerRequest found: ${hasModelConfigFix}`);

if (version === 'buggy') {
  if (!hasModelConfigFix) {
    console.log('✅ BUG REPRODUCED: modelConfig does not specify maxTokensPerInput and maxInputsPerRequest.');
    process.exit(0);
  } else {
    console.log('❌ BUG NOT REPRODUCED: modelConfig fix found in buggy version.');
    process.exit(1);
  }
} else {
  if (hasModelConfigFix) {
    console.log('✅ FIX VERIFIED: modelConfig specifies maxTokensPerInput and maxInputsPerRequest.');
    process.exit(0);
  } else {
    console.log('❌ FIX NOT VERIFIED: modelConfig does not specify maxTokensPerInput and maxInputsPerRequest.');
    process.exit(1);
  }
}