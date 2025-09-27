import os
import sys
import json
import subprocess
import glob

# Get version parameter from command line
version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
source_dir = sys.argv[2] if len(sys.argv) > 2 else "/app/source_code_buggy"

print(f"Testing superagent issue #953 - Installation Error - supabase: not found")
print(f"Version being tested: {version}")
print(f"Source directory: {source_dir}")

def find_package_json():
    """Find the UI package.json file in the repository"""
    print("\nSearching for package.json in the UI directory...")
    
    # Possible locations for package.json
    locations = [
        os.path.join(source_dir, "ui", "package.json"),  # Standard location
        os.path.join(source_dir, "libs", "ui", "package.json"),  # Found in fixed version
        os.path.join(source_dir, "apps", "ui", "package.json"),  # Possible monorepo structure
        os.path.join(source_dir, "packages", "ui", "package.json"),  # Another monorepo structure
    ]
    
    # Try the specific paths first
    for path in locations:
        if os.path.exists(path):
            print(f"Found package.json at: {path}")
            return path
    
    # If not found, search recursively for any ui/package.json
    print("Searching recursively for UI package.json...")
    for root, dirs, files in os.walk(source_dir):
        if "node_modules" in root:  # Skip node_modules directories
            continue
        if "package.json" in files and ("ui" in root.lower() or "dashboard" in root.lower()):
            path = os.path.join(root, "package.json")
            print(f"Found potential UI package.json at: {path}")
            return path
    
    # If still not found, search for any Dockerfile that might contain the supabase command
    print("Searching for Dockerfiles...")
    dockerfiles = []
    for root, dirs, files in os.walk(source_dir):
        if "node_modules" in root:  # Skip node_modules directories
            continue
        for file in files:
            if file == "Dockerfile" or file.endswith(".dockerfile"):
                dockerfiles.append(os.path.join(root, file))
    
    if dockerfiles:
        print(f"Found {len(dockerfiles)} Dockerfiles to check")
        for dockerfile in dockerfiles:
            with open(dockerfile, 'r') as f:
                content = f.read()
                if "supabase" in content:
                    print(f"Found supabase reference in Dockerfile: {dockerfile}")
                    # Look for package.json in the same directory
                    package_json = os.path.join(os.path.dirname(dockerfile), "package.json")
                    if os.path.exists(package_json):
                        print(f"Found associated package.json at: {package_json}")
                        return package_json
    
    print("❌ Could not locate UI package.json")
    return None

def check_docker_compose():
    """Check docker-compose files for supabase service"""
    print("\nChecking docker-compose files...")
    
    compose_files = glob.glob(os.path.join(source_dir, "**", "docker-compose*.yml"), recursive=True)
    compose_files += glob.glob(os.path.join(source_dir, "**", "docker-compose*.yaml"), recursive=True)
    
    if not compose_files:
        print("No docker-compose files found")
        return False
    
    print(f"Found {len(compose_files)} docker-compose files")
    
    supabase_found = False
    
    for file_path in compose_files:
        print(f"Checking {os.path.basename(file_path)}...")
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                if "supabase" in content:
                    supabase_found = True
                    print(f"✅ Found supabase reference in {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error reading file: {e}")
    
    return supabase_found

def check_dockerfile_for_supabase():
    """Check Dockerfiles for supabase installation"""
    print("\nChecking Dockerfiles for supabase installation...")
    
    dockerfiles = []
    for root, dirs, files in os.walk(source_dir):
        if "node_modules" in root:  # Skip node_modules directories
            continue
        for file in files:
            if file == "Dockerfile" or file.endswith(".dockerfile"):
                dockerfiles.append(os.path.join(root, file))
    
    supabase_installed_in_docker = False
    
    if dockerfiles:
        print(f"Found {len(dockerfiles)} Dockerfiles to check")
        for dockerfile in dockerfiles:
            print(f"Checking {os.path.relpath(dockerfile, source_dir)}...")
            try:
                with open(dockerfile, 'r') as f:
                    content = f.read()
                    # Look for supabase installation in Docker
                    if "npm i -g supabase" in content or "npm install -g supabase" in content or "yarn global add supabase" in content:
                        supabase_installed_in_docker = True
                        print(f"✅ Found supabase installation in {os.path.relpath(dockerfile, source_dir)}")
            except Exception as e:
                print(f"Error reading file: {e}")
    else:
        print("No Dockerfiles found")
    
    return supabase_installed_in_docker

def check_package_json(package_json_path):
    """Check if the package.json file contains the supabase dependency"""
    print("\nExamining package.json...")
    
    if not package_json_path or not os.path.exists(package_json_path):
        print(f"❌ ERROR: package.json not found at {package_json_path}")
        return False, False, None
    
    try:
        with open(package_json_path, 'r') as file:
            package_data = json.load(file)
            
        # Check if the supabase command is used in any script
        has_supabase_script = False
        supabase_script_name = None
        supabase_scripts = []
        
        if "scripts" in package_data:
            for script_name, script_cmd in package_data["scripts"].items():
                if isinstance(script_cmd, str) and "supabase" in script_cmd:
                    has_supabase_script = True
                    supabase_script_name = script_name
                    supabase_scripts.append((script_name, script_cmd))
                    print(f"Found script using supabase: {script_name}: {script_cmd}")
        
        # Check if the supabase dependency exists
        has_supabase_dep = False
        all_deps = {}
        if "dependencies" in package_data:
            all_deps.update(package_data["dependencies"])
        if "devDependencies" in package_data:
            all_deps.update(package_data["devDependencies"])
            
        if "supabase" in all_deps:
            has_supabase_dep = True
            print(f"Found supabase dependency: {all_deps['supabase']}")
        
        # Also look for npx usage, which might not require a local dependency
        uses_npx = any("npx supabase" in cmd for _, cmd in supabase_scripts)
        if uses_npx:
            print("Note: Scripts use 'npx supabase' which might not require a local dependency")
        
        return has_supabase_script, has_supabase_dep, supabase_scripts
        
    except Exception as e:
        print(f"❌ ERROR reading package.json: {e}")
        return False, False, None

def run_test():
    """Run the appropriate tests based on version"""
    # Find package.json location
    package_json_path = find_package_json()
    
    # Check docker-compose files for supabase references
    has_supabase_in_compose = check_docker_compose()
    
    # Check Dockerfiles for supabase installation
    supabase_installed_in_docker = check_dockerfile_for_supabase()
    
    # Check package.json
    if package_json_path:
        has_supabase_script, has_supabase_dep, supabase_scripts = check_package_json(package_json_path)
    else:
        has_supabase_script = False
        has_supabase_dep = False
        supabase_scripts = []
    
    # Check if scripts use npx which might not require local dependency
    uses_npx = False
    if supabase_scripts:
        uses_npx = any("npx supabase" in cmd for _, cmd in supabase_scripts)
    
    if version == "buggy":
        if has_supabase_script and not has_supabase_dep and not supabase_installed_in_docker:
            print("\n✅ BUG REPRODUCED: supabase script exists but dependency is missing")
            print("This would cause 'supabase: not found' error when running in Docker")
            return 0
        elif has_supabase_in_compose and not has_supabase_dep and not supabase_installed_in_docker:
            print("\n✅ BUG REPRODUCED: supabase used in docker-compose but dependency is missing")
            return 0
        elif has_supabase_script and (has_supabase_dep or supabase_installed_in_docker):
            print("\n❌ FAILURE: Supabase is properly set up in buggy version")
            return 1
        else:
            # As a fallback, check any scripts directory or Dockerfiles for supabase command
            found_references = []
            for root, dirs, files in os.walk(source_dir):
                if "node_modules" in root:  # Skip node_modules directories
                    continue
                for file in files:
                    if file.endswith(".sh") or file == "Dockerfile" or file.endswith(".dockerfile") or file.endswith(".yml") or file.endswith(".yaml"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r') as f:
                                content = f.read()
                                if "supabase" in content:
                                    found_references.append(file_path)
                        except:
                            pass  # Skip files that can't be read
            
            if found_references:
                print(f"\nFound {len(found_references)} files with 'supabase' references:")
                for ref in found_references:
                    print(f"- {ref}")
                print("\n✅ BUG REPRODUCED: supabase command used in scripts/Docker but dependency is missing")
                return 0
            else:
                print("\n❓ INDETERMINATE: Couldn't find supabase script in any files")
                return 1
    else:
        # Fixed version - consider it fixed if:
        # 1. supabase dependency is added, OR
        # 2. supabase is installed in Docker, OR
        # 3. all scripts use npx which doesn't require local installation
        if has_supabase_script and has_supabase_dep:
            print(f"\n✅ FIX CONFIRMED: supabase dependency added for scripts")
            return 0
        elif supabase_installed_in_docker:
            print("\n✅ FIX CONFIRMED: supabase is now installed in Docker")
            return 0
        elif uses_npx and len(supabase_scripts) > 0:
            print("\n✅ FIX CONFIRMED: All supabase scripts use npx which doesn't require local installation")
            return 0
        elif not has_supabase_script and not has_supabase_in_compose:
            print("\n✅ FIX CONFIRMED: supabase scripts/references removed")
            return 0
        else:
            # Additional check: Compare Docker files between buggy and fixed
            if os.path.exists("/app/source_code_buggy") and version == "fixed":
                buggy_docker_files = find_docker_files("/app/source_code_buggy")
                fixed_docker_files = find_docker_files(source_dir)
                
                # Check if any Dockerfile changed that might be related to supabase
                docker_changes = []
                for buggy_path in buggy_docker_files:
                    rel_path = os.path.relpath(buggy_path, "/app/source_code_buggy")
                    fixed_path = os.path.join(source_dir, rel_path)
                    
                    if os.path.exists(fixed_path):
                        try:
                            with open(buggy_path, 'r') as f1, open(fixed_path, 'r') as f2:
                                buggy_content = f1.read()
                                fixed_content = f2.read()
                                if buggy_content != fixed_content and "supabase" in (buggy_content + fixed_content):
                                    docker_changes.append(rel_path)
                        except:
                            pass
                
                if docker_changes:
                    print("\n✅ FIX CONFIRMED: Found changes in Docker files that might address the issue:")
                    for change in docker_changes:
                        print(f"- {change}")
                    return 0
                
            print("\n❌ FAILURE: Fix not confirmed - supabase references exist without dependency or Docker installation")
            return 1

def find_docker_files(directory):
    """Find all Docker files in the repository"""
    docker_files = []
    for root, dirs, files in os.walk(directory):
        if "node_modules" in root:  # Skip node_modules directories
            continue
        for file in files:
            if file == "Dockerfile" or file.endswith(".dockerfile"):
                docker_files.append(os.path.join(root, file))
    return docker_files

if __name__ == "__main__":
    exit_code = run_test()
    sys.exit(exit_code)