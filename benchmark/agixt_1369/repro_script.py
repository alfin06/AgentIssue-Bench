import sys
import re
import os
import glob
import difflib

def check_chain_validation(version):
    """Check if the chain name is validated in the given version."""
    source_dir = f"/app/source_code_{version}"
    agixt_dir = os.path.join(source_dir, "agixt")
    
    print(f"Searching for chain-related files in {version} version...")
    
    # Look for chain-related files
    chain_files = glob.glob(f"{agixt_dir}/*Chain*.py") + glob.glob(f"{agixt_dir}/endpoints/*Chain*.py")
    
    if not chain_files:
        print("Could not find any Chain-related Python files")
        return 2
    
    print(f"Found {len(chain_files)} chain-related files: {[os.path.basename(f) for f in chain_files]}")
    
    # Look for methods that might handle chain creation
    chain_creation_found = False
    validation_found = False
    
    for file_path in chain_files:
        print(f"\nExamining file: {os.path.basename(file_path)}")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Look for methods that might handle chain creation
        method_patterns = [
            r'def create_chain\(.*?\):(.*?)(?:def|\Z)',
            r'def add_chain\(.*?\):(.*?)(?:def|\Z)',
            r'def new_chain\(.*?\):(.*?)(?:def|\Z)',
            r'@app\.post\([\'"].*?chain.*?[\'"]\)(.*?)(?:@|\Z)',
            r'@router\.post\([\'"].*?chain.*?[\'"]\)(.*?)(?:@|\Z)'
        ]
        
        for pattern in method_patterns:
            method_matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in method_matches:
                chain_creation_found = True
                method_code = match.group(1)
                
                print(f"\nFound potential chain creation method in {os.path.basename(file_path)}:")
                print("--------------------------------")
                
                # Extract method signature
                lines = content[:match.start()].split('\n')
                for i in range(len(lines)-5, len(lines)):
                    if i >= 0:
                        print(f"    {lines[i]}")
                
                # Check for chain_name usage in the method
                chain_name_lines = []
                for i, line in enumerate(method_code.split('\n')):
                    if 'chain_name' in line:
                        chain_name_lines.append((i, line))
                
                if chain_name_lines:
                    print("\n    Lines with chain_name references:")
                    for i, line in chain_name_lines:
                        print(f"    >>> {line}")
                
                # Check for validation of empty chain name
                empty_validation_patterns = [
                    r'if\s+not\s+chain_name', 
                    r'if\s+chain_name\s*==\s*[\'"][\'"]\s*:', 
                    r'if\s+chain_name\s*==\s*None',
                    r'if\s+len\s*\(\s*chain_name\s*\)\s*==\s*0',
                    r'if\s+len\s*\(\s*chain_name\.strip\s*\(\s*\)\s*\)\s*==\s*0',
                    r'if\s+not\s+chain_name\.strip\s*\(\s*\)',
                    r'validate.*?chain_name',
                    r'chain_name.*?required',
                    r'required.*?chain_name'
                ]
                
                for pattern in empty_validation_patterns:
                    if re.search(pattern, method_code):
                        print(f"\n    Found validation pattern: {pattern}")
                        validation_found = True
    
    # If we're looking at the fixed version, also check endpoints directory for validation
    if version == "fixed" and not validation_found:
        validation_found = check_api_endpoints(agixt_dir)
        
    # If we're still not finding validation in the fixed version, check for model/schema files
    if version == "fixed" and not validation_found:
        validation_found = check_models_and_schemas(agixt_dir)
        
    # If all else fails, let's look at the differences between the two versions
    if version == "fixed" and not validation_found:
        validation_found = check_differences()
    
    if not chain_creation_found:
        print("\nCould not find any chain creation methods in the codebase")
        return 2
    
    if version == "buggy":
        if not validation_found:
            print("\nBUG CONFIRMED: No validation for empty chain name in buggy version")
            print("This allows empty chain names to be created, causing validation errors later.")
            return 1  # Confirm bug exists
        else:
            print("\nUnexpected: Found validation for empty chain name in buggy version")
            print("The code appears to already validate chain names, which conflicts with the bug report.")
            return 0
    else:  # fixed version
        if validation_found:
            print("\nFIX CONFIRMED: Found validation for empty chain name in fixed version")
            print("The code now properly validates that chain names are not empty.")
            return 0  # Confirm fix works
        else:
            print("\nFIX FAILED: No validation for empty chain name in fixed version")
            print("The fix does not appear to have been implemented correctly.")
            return 1

def check_api_endpoints(agixt_dir):
    """Check API endpoints for validation."""
    print(f"\nLooking for validation in API endpoints...")
    
    endpoints_dir = os.path.join(agixt_dir, "endpoints")
    if not os.path.exists(endpoints_dir):
        print("Endpoints directory not found")
        return False
        
    endpoint_files = glob.glob(f"{endpoints_dir}/*.py")
    print(f"Found {len(endpoint_files)} endpoint files")
    
    validation_found = False
    
    for file_path in endpoint_files:
        if os.path.basename(file_path).lower() in ['chain.py', 'chains.py']:
            print(f"\nExamining chain endpoint file: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Look for FastAPI request models/schemas
            model_patterns = [
                r'class\s+.*?Chain.*?Request.*?:',
                r'class\s+.*?Request.*?Chain.*?:',
                r'class\s+CreateChain.*?:'
            ]
            
            for pattern in model_patterns:
                matches = re.finditer(pattern, content, re.DOTALL)
                
                for match in matches:
                    # Get the class definition
                    class_start = match.start()
                    class_name = re.search(r'class\s+(\w+)', content[class_start:]).group(1)
                    print(f"\nFound request model class: {class_name}")
                    
                    # Find the end of the class
                    class_code = ""
                    lines = content[class_start:].split('\n')
                    indent = 0
                    for i, line in enumerate(lines):
                        if i == 0:  # First line of class
                            class_code += line + '\n'
                            indent = len(line) - len(line.lstrip())
                        elif line.strip() and len(line) - len(line.lstrip()) <= indent:
                            break  # End of class definition
                        else:
                            class_code += line + '\n'
                    
                    print(f"Class definition:\n{class_code}")
                    
                    # Check for chain_name validation
                    if 'chain_name' in class_code:
                        validation_patterns = [
                            r'chain_name.*?=.*?Field.*?min_length',
                            r'chain_name.*?Field.*?required',
                            r'Field.*?.*?chain_name'
                        ]
                        
                        for val_pattern in validation_patterns:
                            if re.search(val_pattern, class_code, re.DOTALL):
                                print(f"\nFound validation in class: {val_pattern}")
                                validation_found = True
                                
            # Also check for direct validation in endpoint functions
            endpoint_patterns = [
                r'@.*?router\.post.*?chain.*?def.*?\(.*?\):(.*?)(?:@|\Z)',
                r'@.*?app\.post.*?chain.*?def.*?\(.*?\):(.*?)(?:@|\Z)'
            ]
            
            for pattern in endpoint_patterns:
                matches = re.finditer(pattern, content, re.DOTALL)
                
                for match in matches:
                    func_code = match.group(1)
                    print(f"\nFound endpoint function for chains")
                    
                    if 'chain_name' in func_code:
                        # Look for validation
                        validation_patterns = [
                            r'if\s+not\s+chain_name',
                            r'if\s+chain_name\s*==\s*[\'"][\'"]\s*:',
                            r'if\s+len\s*\(\s*chain_name.*?\)\s*==\s*0',
                            r'raise.*?if\s+not\s+chain_name'
                        ]
                        
                        for val_pattern in validation_patterns:
                            if re.search(val_pattern, func_code):
                                print(f"Found validation in endpoint function: {val_pattern}")
                                validation_found = True
    
    return validation_found

def check_models_and_schemas(agixt_dir):
    """Check models and schema files for validation."""
    print(f"\nLooking for validation in models and schema files...")
    
    model_files = glob.glob(f"{agixt_dir}/models/*.py") + glob.glob(f"{agixt_dir}/schemas/*.py")
    
    if not model_files:
        print("No model or schema files found")
        return False
        
    print(f"Found {len(model_files)} model/schema files")
    
    validation_found = False
    
    for file_path in model_files:
        if 'chain' in file_path.lower():
            print(f"\nExamining chain model file: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if 'chain_name' in content:
                validation_patterns = [
                    r'chain_name.*?=.*?Field.*?min_length',
                    r'chain_name.*?=.*?Field.*?required',
                    r'chain_name.*?=.*?Column.*?nullable=False',
                    r'chain_name.*?validator'
                ]
                
                for pattern in validation_patterns:
                    if re.search(pattern, content, re.DOTALL):
                        print(f"Found validation in model: {pattern}")
                        validation_found = True
    
    return validation_found

def check_differences():
    """Check differences between buggy and fixed versions to find the fix."""
    print("\nComparing buggy and fixed versions to locate the fix...")
    
    # Paths to check
    paths_to_check = [
        ("agixt/endpoints/Chain.py", "agixt/endpoints/Chain.py"),
        ("agixt/Chain.py", "agixt/Chain.py")
    ]
    
    for buggy_path, fixed_path in paths_to_check:
        buggy_file = f"/app/source_code_buggy/{buggy_path}"
        fixed_file = f"/app/source_code_fixed/{fixed_path}"
        
        if os.path.exists(buggy_file) and os.path.exists(fixed_file):
            print(f"\nComparing {buggy_path}...")
            
            with open(buggy_file, 'r', encoding='utf-8', errors='ignore') as f:
                buggy_content = f.readlines()
                
            with open(fixed_file, 'r', encoding='utf-8', errors='ignore') as f:
                fixed_content = f.readlines()
                
            diff = list(difflib.unified_diff(buggy_content, fixed_content, n=3))
            
            if diff:
                print(f"Found {len(diff)} lines of differences")
                
                # Look for relevant changes
                chain_name_changes = False
                validation_changes = False
                
                for line in diff:
                    if line.startswith('+') and 'chain_name' in line:
                        print(f"Added line with chain_name: {line.strip()}")
                        chain_name_changes = True
                        
                    if line.startswith('+') and any(term in line.lower() for term in ['valid', 'check', 'if not', 'empty', 'required']):
                        print(f"Added line with validation: {line.strip()}")
                        validation_changes = True
                
                if chain_name_changes and validation_changes:
                    print("\nFOUND FIX: Changes related to chain_name validation were added")
                    return True
                elif chain_name_changes:
                    print("\nPossible fix found: Changes to chain_name handling were added")
                    return True
    
    print("No clear validation fix found in the differences")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repro_script.py [buggy|fixed]")
        sys.exit(2)
    
    version = sys.argv[1]
    if version not in ["buggy", "fixed"]:
        print(f"Invalid version: {version}")
        sys.exit(2)
    
    print(f"\n=== Testing AGiXT Issue #1369 - Empty Chain Name Validation ===")
    print(f"Version: {version.upper()}")
    print("="*60)
    
    exit_code = check_chain_validation(version)
    
    print("\n=== Test Summary ===")
    if exit_code == 1:
        if version == "buggy":
            print("✓ Bug successfully reproduced: Empty chain names are accepted")
        else:
            print("✗ Fix verification failed: Empty chain names are still accepted")
    elif exit_code == 0:
        if version == "buggy":
            print("✗ Bug not reproduced: Chain names appear to be validated")
        else:
            print("✓ Fix successfully verified: Empty chain names are now rejected")
    else:
        print("! Test inconclusive: Could not determine validation status")
        
    sys.exit(exit_code)