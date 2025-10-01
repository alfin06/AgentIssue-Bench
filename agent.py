import os
import json
from dataclasses import dataclass
from typing import Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv(override=True)

@dataclass
class Config:
    """Configuration class for the AI Agent Bug Reproduction Pipeline."""
    github_pat: str
    openai_api_key: Optional[str]
    openai_base_url: Optional[str] = None
    min_stars: int = 1000
    target_repositories: Optional[List[str]] = None
    enable_discovery: bool = True  # Flag to enable/disable auto discovery
    model_name: str = "gpt-4o"
    max_issues: int = 5  # Maximum number of issues to process

    @classmethod
    def from_env(cls) -> 'Config':
        """Create a Config instance from environment variables."""
        github_pat = os.environ.get('GITHUB_PAT')
        if not github_pat:
            raise ValueError("GITHUB_PAT environment variable is required")
        
        # Parse comma-separated repo list from env var
        target_repos_str = os.environ.get('TARGET_REPOS', '')
        target_repos = [repo.strip() for repo in target_repos_str.split(',')] if target_repos_str else None
        
        # Default to True unless explicitly set to "false"
        enable_discovery = os.environ.get('ENABLE_DISCOVERY', 'true').lower() != 'false'
        
        return cls(
            github_pat=github_pat,
            openai_api_key=os.environ.get('OPENAI_API_KEY'),
            openai_base_url=os.environ.get('OPENAI_API_BASE'),
            min_stars=int(os.environ.get('MIN_STARS', cls.min_stars)),
            target_repositories=target_repos,
            enable_discovery=enable_discovery,
            model_name=os.environ.get('MODEL_NAME', 'gpt-4o'),
            max_issues=int(os.environ.get('MAX_ISSUES_TO_PROCESS', 5))
        )

# Initialize configuration
config = Config.from_env()

from crewai import Agent, Task, Crew, Process
from crewai.tools.base_tool import BaseTool
from langchain_openai import ChatOpenAI

# --- 1. Import helper functions at the top level ---
from find_issue import search_github_issues, scrape_pr_urls_from_issue_page
from reproduce import get_repo_url_and_commit_from_pr, generate_repro_script_with_gpt4o, find_repro_script_with_regex

# --- 2. Centralized LLM Configuration ---
# Configure the LLM to be used by all agents, including the custom base URL
# for the OpenAI API proxy.
openai_llm = ChatOpenAI(
    model_name=config.model_name,
    temperature=1,
    api_key=config.openai_api_key,
    base_url=config.openai_base_url
)

def generate_repro_script_with_config_model(issue_description: str):
    """Generate a reproduction script using the configured model from .env."""
    print(f"        Attempting to generate repro script using {config.model_name}...")
    
    # Store original API URL in case we need to restore it
    original_api_base = os.environ.get('OPENAI_API_BASE')
    
    # Set the API base to our config value if it exists
    if config.openai_base_url:
        os.environ['OPENAI_API_BASE'] = config.openai_base_url
    
    try:
        # Call the existing function (which will use our environment variables)
        return generate_repro_script_with_gpt4o(issue_description)
    finally:
        # Restore original environment
        if original_api_base:
            os.environ['OPENAI_API_BASE'] = original_api_base
        elif config.openai_base_url:
            # If there was no original value but we set one, remove it
            del os.environ['OPENAI_API_BASE']

# --- 3. Define Custom Tools ---

class RepoDiscoveryTool(BaseTool):
    name: str = "GitHub Repository Discovery"
    description: str = "Discovers popular GitHub repositories related to AI agents."

    def _run(self, min_stars: int) -> List[str]:
        import requests
        import time
        print(f"--- [Tool Call] Discovering repositories with >{min_stars} stars ---")
        headers = {"Authorization": f"Bearer {config.github_pat}"}
        query = f'topic:ai-agents stars:>{min_stars}'
        
        try:
            response = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params={"q": query, "sort": "stars", "order": "desc", "per_page": 10},
                timeout=30
            )
            response.raise_for_status()
            repos = response.json().get("items", [])
            repo_names = [repo["full_name"] for repo in repos]
            print(f"--- [Tool Result] Discovered {len(repo_names)} repositories. ---")
            return repo_names
        except Exception as e:
            print(f"Error during repository discovery: {e}")
            return []

class GitHubIssueScoutTool(BaseTool):
    name: str = "GitHub Issue Scout"
    description: str = (
        "For a given list of repositories, finds closed bug reports that have a linked Pull Request. "
        "Returns a list of issues, each with its URL, title, description, and PR details."
    )

    def _run(self, repositories: List[str]) -> List[dict]:
        print(f"--- [Tool Call] Scouting {len(repositories)} repositories for issues... ---")
        all_found_issues = []
        
        # Create headers once to be reused
        headers = {"Authorization": f"Bearer {config.github_pat}"}
        
        for repo in repositories:
            print(f"\n--- Scouting repo: {repo} ---")
            found_issues_for_repo = []
            
            # Try multiple search queries to maximize chances of finding issues
            search_queries = [
                f"repo:{repo} is:issue is:closed -reason:duplicate label:bug",
                f"repo:{repo} is:issue is:closed -reason:duplicate \"reproduce\" OR \"steps\" OR \"traceback\" OR \"error\" in:title,body",
                f"repo:{repo} is:issue is:closed -reason:duplicate \"bug\" OR \"fix\" OR \"issue\" OR \"problem\" OR \"fail\" in:title,body"
            ]
            
            for query in search_queries:
                raw_issues = search_github_issues(query, max_pages_per_repo=1, items_per_page=10)
                if raw_issues:
                    found_issues_for_repo.extend(raw_issues)
            
            # Process the issues found for this repo
            if found_issues_for_repo:
                print(f"  Found a total of {len(found_issues_for_repo)} potential issues to process for this repo.")
                
                # Process each issue to find linked PRs
                for issue in found_issues_for_repo:
                    # Skip processing if we already found this issue
                    if any(found["github_url"] == issue.get("html_url") for found in all_found_issues):
                        continue
                        
                    linked_pr_url = None
                    # First, check for an officially linked PR
                    if issue.get('pull_request') and issue['pull_request'].get('html_url'):
                        linked_pr_url = issue['pull_request']['html_url']
                    # If not found, scrape the page for mentions
                    elif issue.get('html_url'):
                        # Pass the headers to the scrape_pr_urls_from_issue_page function
                        scraped_pr_urls = scrape_pr_urls_from_issue_page(issue.get('html_url'), headers)
                        if scraped_pr_urls:
                            linked_pr_url = scraped_pr_urls[0]  # Get the first mentioned PR
                    
                    if linked_pr_url:
                        repo_url, buggy_commit, fixed_commit = get_repo_url_and_commit_from_pr(linked_pr_url, headers)
                        if repo_url and buggy_commit and fixed_commit:
                            all_found_issues.append({
                                "github_url": issue.get("html_url"),
                                "title": issue.get("title"),
                                "description": issue.get("body"),
                                "linked_pr_url": linked_pr_url,
                                "repo_url": repo_url,
                                "buggy_commit": buggy_commit,
                                "fixed_commit": fixed_commit,
                            })
            else:
                print(f"  No issues found for repo: {repo}")
                
        print(f"--- [Tool Result] Found {len(all_found_issues)} actionable issues. ---")
        return all_found_issues

class TestPackageGeneratorTool(BaseTool):
    name: str = "Test Package Generator"
    description: str = (
        "Takes a single issue object and generates a failure-triggering test script and Dockerfile for it."
    )

    def _run(self, issue: dict) -> dict:
        print(f"--- [Tool Call] Generating test package for: {issue['github_url']} ---")
        script_name, script_content = generate_repro_script_with_config_model(issue.get("description", ""))

        if not script_content:
            return {"status": "FAILED", "reason": "LLM failed to generate a reproduction script."}
        
        # Extract the repository name from the repo_url
        repo_name = issue["repo_url"].split('/')[-1] if issue.get("repo_url") else "unknown-repo"
        
        # Generate requirements by analyzing the script content
        requirements = self._extract_requirements(script_content)
        
        # Generate a proper Dockerfile for the reproduction
        dockerfile_content = self._generate_dockerfile(
            script_name=script_name,
            repo_name=repo_name,
            repo_url=issue.get("repo_url", ""),
            buggy_commit=issue.get("buggy_commit", ""),
            requirements=requirements
        )
            
        return {
            "status": "SUCCESS",
            "issue_url": issue['github_url'],
            "repro_script_filename": script_name,
            "repro_script_content": script_content,
            "dockerfile_content": dockerfile_content,
            "buggy_commit": issue["buggy_commit"],
            "fixed_commit": issue["fixed_commit"]
        }
    
    def _extract_requirements(self, script_content: str) -> list:
        """Extract Python package requirements from the reproduction script."""
        import re
        
        # Find all import statements
        imports = re.findall(r'import\s+([a-zA-Z0-9_.,\s]+)', script_content)
        from_imports = re.findall(r'from\s+([a-zA-Z0-9_.]+)\s+import', script_content)
        
        # Combine and process all imports
        all_imports = []
        
        for imp in imports:
            # Handle multiple imports in one line (e.g., import os, sys, re)
            modules = [module.strip() for module in imp.split(',')]
            all_imports.extend(modules)
        
        all_imports.extend(from_imports)
        
        # Convert module names to package names (best effort)
        packages = set()
        for module in all_imports:
            # Extract the top-level package name
            package = module.split('.')[0].lower()
            
            # Skip standard library modules
            if package in ('os', 'sys', 're', 'json', 'time', 'datetime', 'math', 
                        'random', 'collections', 'functools', 'itertools', 'typing',
                        'asyncio', 'pathlib'):
                continue
                
            # Handle special cases for package naming
            package_mapping = {
                'autogen_agentchat': 'autogen',
                'autogen_core': 'autogen',
                'autogen_ext': 'autogen',
                'crewai': 'crewai',
                'langchain': 'langchain',
                'pydantic': 'pydantic',
                'openai': 'openai',
                'numpy': 'numpy',
                'pandas': 'pandas',
                'torch': 'torch',
                'transformers': 'transformers'
            }
            
            if package in package_mapping:
                packages.add(package_mapping[package])
            else:
                # Only add if it's likely a pip package (not a local import)
                if not package.startswith('.'):
                    packages.add(package)
                    
        return sorted(list(packages))
    
    def _generate_dockerfile(self, script_name: str, repo_name: str, repo_url: str,
                            buggy_commit: str, requirements: list) -> str:
        """Generate a complete Dockerfile for the reproduction script."""
        
        # Start with a base Python image
        dockerfile = "FROM python:3.11-slim\n\n"
        
        # Add labels for better identification
        dockerfile += f"LABEL description=\"Reproduction for {repo_name} bug\"\n"
        dockerfile += f"LABEL github_repo=\"{repo_url}\"\n"
        dockerfile += f"LABEL buggy_commit=\"{buggy_commit}\"\n\n"
        
        # Set working directory
        dockerfile += "WORKDIR /app\n\n"
        
        # Install git and other dependencies
        dockerfile += "# Install git and other dependencies\n"
        dockerfile += "RUN apt-get update && \\\n"
        dockerfile += "    apt-get install -y git && \\\n"
        dockerfile += "    apt-get clean && \\\n"
        dockerfile += "    rm -rf /var/lib/apt/lists/*\n\n"
        
        # Clone the repository at the specific buggy commit
        if repo_url and buggy_commit:
            dockerfile += f"# Clone the repository at the buggy commit\n"
            dockerfile += f"RUN git clone {repo_url} /app/repo && \\\n"
            dockerfile += f"    cd /app/repo && \\\n"
            dockerfile += f"    git checkout {buggy_commit}\n\n"
            
            # If it's a Python package, install it in development mode
            dockerfile += f"# Install the package in development mode\n"
            dockerfile += f"RUN cd /app/repo && \\\n"
            dockerfile += f"    pip install -e .\n\n"
        
        # Install Python requirements
        if requirements:
            dockerfile += "# Install required packages\n"
            dockerfile += "RUN pip install --no-cache-dir \\\n"
            for req in requirements[:-1]:
                dockerfile += f"    {req} \\\n"
            if requirements:
                dockerfile += f"    {requirements[-1]}\n\n"
        
        # Copy the reproduction script
        dockerfile += f"# Copy the reproduction script\n"
        dockerfile += f"COPY {script_name} /app/{script_name}\n\n"
        
        # Set the entrypoint
        dockerfile += f"# Run the reproduction script\n"
        dockerfile += f"ENTRYPOINT [\"python\", \"/app/{script_name}\"]\n"
        
        return dockerfile

# --- 4. Define Pydantic Model for Final Output ---
class TestPackage(BaseModel):
    issue_url: str = Field(description="The URL of the GitHub issue.")
    status: str = Field(description="The status of the generation (e.g., SUCCESS or FAILED).")
    repro_script_filename: Optional[str] = Field(description="The filename of the generated script.")
    repro_script_content: Optional[str] = Field(description="The content of the generated script.")
    dockerfile_content: Optional[str] = Field(description="The content of the generated Dockerfile.")
    buggy_commit: Optional[str] = Field(description="The buggy commit hash.")
    fixed_commit: Optional[str] = Field(description="The fixed commit hash.")
    reason: Optional[str] = Field(description="Reason for failure, if any.")

class FinalReport(BaseModel):
    processed_issues: List[TestPackage] = Field(description="A list of all the test packages that were generated.")
    summary: str = Field(description="A brief summary of the pipeline's execution.")

# --- 5. Create the Agents ---

repo_hunter_agent = Agent(
    role='Repository Hunter',
    goal='Discover popular and relevant GitHub repositories for AI agents.',
    backstory='An expert at using GitHub search to find active and significant projects in the AI agent space.',
    tools=[RepoDiscoveryTool()],
    verbose=True,
    llm=openai_llm
)

scout_agent = Agent(
    role='Software Scout',
    goal='Find actionable, closed bug reports with linked pull requests from a list of repositories.',
    backstory='An expert at navigating GitHub to find high-quality bug reports with clear fixes.',
    tools=[GitHubIssueScoutTool()],
    verbose=True,
    llm=openai_llm
)

test_engineer_agent = Agent(
    role='Test Automation Engineer',
    goal='Create a complete, runnable failure-triggering test package for each bug report provided.',
    backstory='A specialist in software testing who writes reproduction scripts and Dockerfiles.',
    tools=[TestPackageGeneratorTool()],
    verbose=True,
    output_pydantic=FinalReport,
    llm=openai_llm
)

# --- 6. Define the Tasks ---

discover_repos_task = Task(
    description=f'Discover popular AI agent repositories on GitHub with at least {config.min_stars} stars.',
    expected_output='A list of repository full names (e.g., ["org/repo1", "org/repo2"]).',
    agent=repo_hunter_agent
)

find_issues_task = Task(
    description=(
        'Take the list of repositories from the previous step and use the GitHub Issue Scout tool '
        'to find all actionable bug reports within them. It is crucial that you pass the entire list '
        'of repositories to the tool.'
    ),
    expected_output=(
        'A list of JSON objects, where each object represents a fully analyzed bug report with its URL, '
        'description, PR link, and commit hashes.'
    ),
    agent=scout_agent,
    context=[discover_repos_task]
)

create_tests_task = Task(
    description=(
        'Process the given issue and generate a failure-triggering test package for it.\n'
        'Use the Test Package Generator tool to create a complete test package including:\n'
        '1. A reproduction script\n'
        '2. A Dockerfile to run the test\n'
        '3. Information about the buggy and fixed commits\n'
        'Then compile a final report in the requested Pydantic format.'
    ),
    expected_output=(
        'A final JSON object conforming to the FinalReport Pydantic model, containing the generated test package.'
    ),
    agent=test_engineer_agent,
    context=[find_issues_task]
)

# Helper function to get target repositories with hybrid approach
def get_target_repositories(config):
    """Get repositories from user input and/or discovery, handling duplicates."""
    repositories = set()  # Using a set to automatically eliminate duplicates
    
    # 1. First add any user-specified repositories
    if config.target_repositories:
        user_repos = [repo.strip() for repo in config.target_repositories if repo.strip()]
        repositories.update(user_repos)
        print(f"Added {len(user_repos)} user-specified repositories")
    
    # 2. If automatic discovery is enabled, add those repositories
    if config.enable_discovery and (not config.target_repositories or len(repositories) < 5):
        repo_tool = RepoDiscoveryTool()
        discovered_repos = repo_tool._run(min_stars=config.min_stars)
        
        # Count new repos (not already in the set)
        new_repos_count = len([r for r in discovered_repos if r not in repositories])
        repositories.update(discovered_repos)
        
        print(f"Added {new_repos_count} newly discovered repositories")
        
    # 3. Convert back to a list for processing
    final_repos = list(repositories)
    print(f"Final repository list contains {len(final_repos)} unique repositories")
    
    return final_repos

# --- 7. Create the Crew and Run the Pipeline ---
discovery_crew = Crew(
    agents=[repo_hunter_agent, scout_agent],
    tasks=[discover_repos_task, find_issues_task],
    process=Process.sequential,
    verbose=True
)

test_generation_crew = Crew(
    agents=[test_engineer_agent],
    tasks=[create_tests_task],
    process=Process.sequential,
    verbose=True
)

if __name__ == "__main__":
    print("--- Starting the AI Agent Bug Reproduction Pipeline ---")
    
    # Get repositories using the hybrid approach
    repositories = get_target_repositories(config)
    
    # Handle execution based on repository source
    if not config.enable_discovery and config.target_repositories:
        print("--- Using user-specified repositories only ---")
        # Skip the discovery task and directly use the GitHubIssueScoutTool
        scout_tool = GitHubIssueScoutTool()
        discovered_issues = scout_tool._run(repositories)
    else:
        print("--- Running full discovery pipeline ---")
        # Run the full discovery pipeline
        discovered_issues = discovery_crew.kickoff()
    
    # Continue with test generation if issues were found
    if not discovered_issues or not isinstance(discovered_issues, list) or len(discovered_issues) == 0:
        print("\n--- No actionable issues found. Exiting. ---")
    else:
        print(f"\n--- Discovered {len(discovered_issues)} actionable issues. ---")
        
        # Limit the number of issues to process based on config
        issues_to_process = min(config.max_issues, len(discovered_issues))
        print(f"--- Processing {issues_to_process} issues as specified in MAX_ISSUES_TO_PROCESS ---")
        
        # Create a list to store all processed issues
        all_processed_issues = []
        successful_count = 0
        
        for i in range(issues_to_process):
            current_issue = discovered_issues[i]
            print(f"\n--- Processing issue {i+1}/{issues_to_process}: {current_issue.get('github_url')} ---")
            print(f"Title: {current_issue.get('title')}")
            
            # Generate test package
            print("--- Generating test package ---")
            test_tool = TestPackageGeneratorTool()
            test_package = test_tool._run(current_issue)
            
            # Create test package object
            issue_package = TestPackage(
                issue_url=test_package.get("issue_url", current_issue.get("github_url", "")),
                status=test_package.get("status", "UNKNOWN"),
                repro_script_filename=test_package.get("repro_script_filename"),
                repro_script_content=test_package.get("repro_script_content"),
                dockerfile_content=test_package.get("dockerfile_content"),
                buggy_commit=test_package.get("buggy_commit", current_issue.get("buggy_commit")),
                fixed_commit=test_package.get("fixed_commit", current_issue.get("fixed_commit")),
                reason=test_package.get("reason")
            )
            
            # Add to our list of processed issues
            all_processed_issues.append(issue_package)
            print(f"Status: {issue_package.status}")
            
            if issue_package.status == "SUCCESS":
                successful_count += 1
        
        # Create final report with all processed issues
        final_report = FinalReport(
            processed_issues=all_processed_issues,
            summary=f"Processed {len(all_processed_issues)} issues from repositories with {successful_count} successful reproductions."
        )
        
        # Output results
        print("\n--- Pipeline Execution Complete ---")
        print("\nFinal Report Summary:")
        print(f"  Total issues processed: {len(final_report.processed_issues)}")
        print(f"  Successfully reproduced: {successful_count}")
        
        # Print details for each issue
        for i, issue in enumerate(final_report.processed_issues):
            print(f"\nIssue {i+1}:")
            print(f"  URL: {issue.issue_url}")
            print(f"  Status: {issue.status}")
            print(f"  Script: {issue.repro_script_filename}")
            print(f"  Buggy commit: {issue.buggy_commit}")
            if issue.status == "SUCCESS":
                print("  [Successfully generated reproduction script]")

        # Save the final structured report
        output_filename = "final_reproduction_package.json"
        with open(output_filename, "w", encoding='utf-8') as f:
            json.dump(final_report.model_dump(), f, indent=2)
        print(f"\n--- Final test package saved to {output_filename} ---")