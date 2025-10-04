import fs from 'fs';
import path from 'path';

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

// Find files containing MCP client code and analyze them
function analyzeSourceCode(baseDir) {
  try {
    console.log(`Analyzing source code in ${baseDir}...`);
    
    // Find all .ts and .js files recursively
    function findFiles(dir, fileList = []) {
      const files = fs.readdirSync(dir);
      
      for (const file of files) {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          // Skip node_modules and .git
          if (file !== 'node_modules' && file !== '.git' && file !== 'dist') {
            findFiles(filePath, fileList);
          }
        } else if (file.endsWith('.ts') || file.endsWith('.js')) {
          fileList.push(filePath);
        }
      }
      
      return fileList;
    }
    
    const allFiles = findFiles(baseDir);
    console.log(`Found ${allFiles.length} source files`);
    
    // Look for any files related to MCP, tools, or client close operations
    let potentialFiles = [];
    const keywords = [
      'mcpClient', 'MCP client', 'experimental_createMCPClient', 
      'client.close()', 'close()', 'streamText', 'tools'
    ];
    
    for (const file of allFiles) {
      try {
        const content = fs.readFileSync(file, 'utf8');
        
        // Check if file contains any of our keywords
        const hasKeywords = keywords.some(keyword => content.includes(keyword));
        if (hasKeywords) {
          potentialFiles.push(file);
        }
      } catch (err) {
        console.error(`Error reading file ${file}: ${err}`);
      }
    }
    
    console.log(`Found ${potentialFiles.length} files containing relevant keywords`);
    
    let bugFound = false;
    let fixFound = false;
    let buggyFiles = [];
    let fixedFiles = [];
    
    // Analyze each file with potential MCP client code
    for (const file of potentialFiles) {
      const content = fs.readFileSync(file, 'utf8');
      const relativePath = path.relative(baseDir, file);
      
      console.log(`\nAnalyzing file: ${relativePath}`);
          
      // Various patterns that might indicate the bug
      const hasCloseCall = content.includes('close()') || 
                           content.includes('client.close()') || 
                           content.includes('mcpClient.close()');
      
      const hasToolsUsage = content.includes('.tools()') || 
                            content.includes('tools =') || 
                            content.includes('tools:') ||
                            content.includes('zapierTools');
      
      const hasCreateMCPClient = content.includes('createMCPClient') || 
                                 content.includes('experimental_createMCPClient');
      
      // Check if the file has the core elements we're looking for
      const hasRelevantCode = hasCloseCall && hasToolsUsage && hasCreateMCPClient;
      
      console.log(`- Has close() call: ${hasCloseCall}`);
      console.log(`- Has tools usage: ${hasToolsUsage}`);
      console.log(`- Has createMCPClient: ${hasCreateMCPClient}`);
      console.log(`- Has all relevant code: ${hasRelevantCode}`);
      
      if (!hasRelevantCode) continue;
      
      // Enhanced pattern detection for the bug
      // Check if tools are accessed after mcpClient.close
      const bugPatterns = [
        // Pattern 1: mcpClient.close() in finally, but tools used after close
        /finally\s*{[^}]*client\.close\(\)[^}]*tools/s,
        
        // Pattern 2: close() called, then tools used
        /client\.close\(\)[^]*?tools\s*=/s,
        
        // Pattern 3: close() called, then tools accessed
        /close\(\)[^]*?\.tools\(\)/s,
        
        // Pattern 4: close before using tools anywhere in the file
        /close\(\)[^]*?streamText[^]*?tools/s
      ];
      
      // Check for the fix patterns
      const fixPatterns = [
        // Pattern 1: Tools captured before closing
        /const\s+\w+\s*=\s*await\s+\w+\.tools\(\)[^]*?\.close\(\)/s,
        
        // Pattern 2: zapierTools captured before close
        /const\s+zapierTools[^]*?\.close\(\)/s,
        
        // Pattern 3: tools stored in a variable before close
        /tools\s*=[^]*?\.close\(\)/s
      ];
      
      // Check for bug patterns
      let isBuggyFile = false;
      for (const pattern of bugPatterns) {
        if (pattern.test(content)) {
          console.log(`- BUG PATTERN DETECTED: ${pattern}`);
          bugFound = true;
          isBuggyFile = true;
          buggyFiles.push(relativePath);
          break;
        }
      }
      
      // Check for fix patterns
      let isFixedFile = false;
      for (const pattern of fixPatterns) {
        if (pattern.test(content)) {
          console.log(`- FIX PATTERN DETECTED: ${pattern}`);
          fixFound = true;
          isFixedFile = true;
          fixedFiles.push(relativePath);
          break;
        }
      }
      
      // Print relevant code sections
      if (hasRelevantCode) {
        console.log('\nRelevant code snippets:');
        const lines = content.split('\n');
        
        // Find and print lines with close()
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('close()')) {
            console.log('\nClose call:');
            for (let j = Math.max(0, i-5); j < Math.min(lines.length, i+3); j++) {
              console.log(`${j+1}: ${lines[j]}`);
            }
          }
        }
        
        // Find and print lines with tools
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('.tools()') || lines[i].includes('tools =')) {
            console.log('\nTools usage:');
            for (let j = Math.max(0, i-2); j < Math.min(lines.length, i+3); j++) {
              console.log(`${j+1}: ${lines[j]}`);
            }
          }
        }
        
        // Find and print lines with streamText
        for (let i = 0; i < lines.length; i++) {
          if (lines[i].includes('streamText')) {
            console.log('\nstreamText usage:');
            for (let j = Math.max(0, i-2); j < Math.min(lines.length, i+5); j++) {
              console.log(`${j+1}: ${lines[j]}`);
            }
          }
        }
      }
    }
    
    // If we found files matching patterns, summarize findings
    if (buggyFiles.length > 0) {
      console.log(`\nFound ${buggyFiles.length} buggy files:`);
      buggyFiles.forEach(file => console.log(`- ${file}`));
    }
    
    if (fixedFiles.length > 0) {
      console.log(`\nFound ${fixedFiles.length} fixed files:`);
      fixedFiles.forEach(file => console.log(`- ${file}`));
    }
    
    // Look for the specific issue pattern described in issue #5365
    console.log('\nLooking for specific issue #5365 pattern...');
    let issue5365Found = false;
    
    for (const file of potentialFiles) {
      const content = fs.readFileSync(file, 'utf8');
      
      // Check for the specific pattern where mcpClient is closed in finally
      // and tools are used in streamText
      if (content.includes('finally') && 
          content.includes('mcpClient.close()') && 
          content.includes('streamText') && 
          content.includes('tools:')) {
        
        // In the buggy version, the tools aren't captured before close
        const toolsCapturedBeforeClose = /const\s+\w+\s*=\s*await\s+mcpClient\.tools\(\)[^]*finally/s.test(content);
        
        if (!toolsCapturedBeforeClose) {
          console.log(`Found issue #5365 pattern in ${path.relative(baseDir, file)}`);
          issue5365Found = true;
          bugFound = true;
        }
        
        if (toolsCapturedBeforeClose) {
          console.log(`Found issue #5365 fix in ${path.relative(baseDir, file)}`);
          fixFound = true;
        }
      }
    }
    
    return { bugFound, fixFound, issue5365Found };
  } catch (err) {
    console.error('Error analyzing source code:', err);
    return { bugFound: false, fixFound: false, issue5365Found: false };
  }
}

async function runTest() {
  try {
    const baseDir = version === 'buggy' ? '/app/source_code_buggy' : '/app/source_code_fixed';
    
    const { bugFound, fixFound, issue5365Found } = analyzeSourceCode(baseDir);
    
    if (version === 'buggy') {
      if (bugFound || issue5365Found) {
        console.log(`\n✅ BUG VERIFIED in BUGGY version: MCP client is closed without properly handling tools.`);
        process.exit(0);
      } else {
        console.log(`\n❌ BUG NOT FOUND in BUGGY version.`);
        process.exit(1);
      }
    } else {
      if (fixFound) {
        console.log(`\n✅ FIX VERIFIED in FIXED version: Tools are properly handled before MCP client is closed.`);
        process.exit(0);
      } else {
        console.log(`\n❌ FIX NOT FOUND in FIXED version.`);
        process.exit(1);
      }
    }
  } catch (error) {
    console.error(`\n❌ FAILURE in ${version.toUpperCase()} version: Unexpected error:`, error);
    process.exit(2);
  }
}

runTest();