const fs = require('fs');
const path = require('path');

const version = process.env.VERSION || 'buggy';
console.log(`Testing ${version.toUpperCase()} version`);

const promptsPath = 'packages/agents/src/agents/Evo/prompts.ts';

if (!fs.existsSync(promptsPath)) {
  console.log(`❌ ERROR: Could not find prompts file at ${promptsPath}`);
  process.exit(1);
}

const promptsCode = fs.readFileSync(promptsPath, 'utf8');

// Look for the evoExplainer prompt and persona mentions
const explainerPattern = /evoExplainer\s*:\s*new\s*Prompt\s*\(`[\s\S]*personas available to you are: CsvAnalyst, Researcher, Synthesizer[\s\S]*`\)/i;
const personaPattern = /CsvAnalyst.*expertise|Researcher.*expertise|Synthesizer.*expertise/i;

const hasExplainer = explainerPattern.test(promptsCode);
const hasPersonas = personaPattern.test(promptsCode);

console.log(`evoExplainer prompt found: ${hasExplainer}`);
console.log(`Persona expertise lines found: ${hasPersonas}`);

if (version === 'buggy') {
  if (!hasExplainer && !hasPersonas) {
    console.log('\n✅ BUG REPRODUCED: Evo does not explain its personas or expertise.');
    process.exit(0);
  } else {
    console.log('\n❌ BUG NOT REPRODUCED: Evo explainer or persona expertise found (unexpected in buggy version).');
    process.exit(1);
  }
} else {
  if (hasExplainer && hasPersonas) {
    console.log('\n✅ FIX VERIFIED: Evo now explains its personas and expertise.');
    process.exit(0);
  } else {
    console.log('\n❌ FIX NOT VERIFIED: Evo explainer or persona expertise missing (unexpected in fixed version).');
    process.exit(1);
  }
}