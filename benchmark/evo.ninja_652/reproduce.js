const fs = require('fs');
const path = require('path');

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

const sourceFilePath = path.join(process.cwd(), 'apps/browser/components/Workspace.tsx');

const fixedImportLine = 'import { workspaceFilesAtom, isChatLoadingAtom, welcomeModalAtom } from "@/lib/store";';

try {
  if (!fs.existsSync(sourceFilePath)) {
    console.log(`❌ ERROR: Source file not found at ${sourceFilePath}`);
    process.exit(1);
  }

  const sourceCode = fs.readFileSync(sourceFilePath, 'utf8');

  const hasFixedImport = sourceCode.includes(fixedImportLine);

  if (version === 'buggy') {
    if (!hasFixedImport) {
      console.log('\n✅ BUG REPRODUCED: Example Prompts Break If Previously Viewing Existing Chat.');
      process.exit(0);
    } else {
      console.log('\n❌ BUG NOT REPRODUCED: Example Prompts Not Break If Previously Viewing Existing Chat.');
      process.exit(1);
    }
  } else {
    if (hasFixedImport) {
      console.log('\n✅ FIX VERIFIED: isChatLoadingAtom import found, confirming the fix.');
      process.exit(0);
    } else {
      console.log('\n❌ FIX NOT VERIFIED: isChatLoadingAtom import NOT found, fix missing.');
      process.exit(1);
    }
  }
} catch (error) {
  console.error('\n❌ ERROR: Failed to analyze the source code:', error);
  process.exit(1);
}