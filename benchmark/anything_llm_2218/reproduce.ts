import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

// Promisify the exec function to use it with async/await
const execAsync = promisify(exec);

async function testOpenApiSpec(version: string): Promise<number> {
    console.log(`--- Running test for '${version}' version ---`);
    console.log('Validating the OpenAPI specification file at server/swagger/openapi.json');

    const openApiFilePath = path.resolve(process.cwd(), 'server/swagger/openapi.json');
    const command = `npx redocly lint ${openApiFilePath}`;

    try {
        console.log(`Executing command: ${command}`);
        const { stdout, stderr } = await execAsync(command);

        // --- Analysis for when the validation command SUCCEEDS ---
        console.log('Validation command completed successfully.');
        if (stdout) console.log('stdout:', stdout);
        if (stderr) console.log('stderr:', stderr);

        if (version === 'buggy') {
            console.log("\n❌ BUG NOT REPRODUCED: OpenAPI spec passed validation, but it was expected to fail.");
            return 1; // This is a failure for the 'buggy' test run.
        } else { // version === 'fixed'
            console.log("\n✅ FIX CONFIRMED: OpenAPI spec passed validation, as expected for the fixed version.");
            return 0; // This is a success for the 'fixed' test run.
        }

    } catch (error: any) {
        // --- Analysis for when the validation command FAILS ---
        // The execAsync promise rejects for non-zero exit codes, which is expected for the buggy version.
        console.log('Validation command failed as expected or unexpectedly.');
        console.log(`Validator output:\n${error.stderr || error.stdout || error.message}`);

        if (version === 'buggy') {
            console.log("\n✅ BUG REPRODUCED: OpenAPI spec failed validation, as expected for the buggy version.");
            return 0; // This is a success for the 'buggy' test run.
        } else { // version === 'fixed'
            console.log("\n❌ FIX NOT CONFIRMED: OpenAPI spec failed validation unexpectedly in the fixed version.");
            return 1; // This is a failure for the 'fixed' test run.
        }
    }
}


// --- Main execution block ---
async function main() {
    const version = process.argv[2];
    if (!version || !['buggy', 'fixed'].includes(version)) {
        console.error("Usage: tsx repro_script.ts [buggy|fixed]");
        process.exit(1);
    }
    
    try {
        const exitCode = await testOpenApiSpec(version);
        process.exit(exitCode);
    } catch (error) {
        console.error(`An unhandled error occurred during the test run:`, error);
        process.exit(1);
    }
}

main();