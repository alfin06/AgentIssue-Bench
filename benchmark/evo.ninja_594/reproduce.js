const fs = require('fs');
const path = require('path');

// Get test version from environment variable
const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

try {
  // This is the key file that potentiall cause anonymous file uploads issue
  let fileToCheck = 'apps/browser/lib/hooks/useFileUpload.ts';
  
  if (!fs.existsSync(fileToCheck)) {
    console.log(`❌ ERROR: Source file not found at ${fileToCheck}. Checking alternate locations...`);
    
    // Try alternative locations
    const alternateLocations = [
      'apps/browser/lib/hooks/useUploadFile.ts',
      'apps/browser/hooks/useFileUpload.ts',
      'packages/browser/lib/hooks/useFileUpload.ts'
    ];
    
    let found = false;
    for (const loc of alternateLocations) {
      if (fs.existsSync(loc)) {
        console.log(`✅ Found file at alternative location: ${loc}`);
        fileToCheck = loc;
        found = true;
        break;
      }
    }
    
    if (!found) {
      console.log("Searching for useUploadFile.ts in the codebase...");
      try {
        const files = fs.readdirSync('apps/browser', { recursive: true });
        const uploadFile = files.find(f => f.endsWith('useWorkspaceUploadDrop.ts') || f.endsWith('useWorkspaceUploadUpdate.ts'));
        if (uploadFile) {
          fileToCheck = path.join('apps/browser', uploadFile);
          console.log(`✅ Found file at: ${fileToCheck}`);
          found = true;
        }
      } catch (e) {
        console.log("Error searching files:", e.message);
      }
      
      if (!found) {
        console.log("❌ Could not find useFileUpload.ts or useUploadFile.ts");
        process.exit(1);
      }
    }
  }
  
  const fileContent = fs.readFileSync(fileToCheck, 'utf8');
  console.log(`File found and read: ${fileToCheck}`);
  
  // The fix ensures that uploaded files are copied from anonymous to new chat sessions
  // Look for code that transfers files between workspaces
  const fixPattern = /setWorkspaceUploads\s*\(\s*uploads\s*\)/i;
  const fixExists = fixPattern.test(fileContent);
  
  console.log(`Fix pattern matched: ${fixExists}`);
  
  if (version === 'buggy') {
    if (!fixExists) {
      console.log('✅ BUG REPRODUCED: Files uploaded in anonymous workspace are not transferred to new chat workspace.');
      process.exit(0);
    } else {
      console.log('❌ BUG NOT REPRODUCED: Code appears to handle file transfers between workspaces.');
      process.exit(1);
    }
  } else {
    if (fixExists) {
      console.log('✅ FIX VERIFIED: Code now handles transferring files from anonymous workspace to new chat.');
      process.exit(0);
    } else {
      console.log('❌ FIX NOT VERIFIED: Code does not appear to handle file transfers between workspaces.');
      process.exit(1);
    }
  }
} catch (error) {
  console.error(`❌ ERROR: ${error.message}`);
  console.error(error);
  process.exit(1);
}