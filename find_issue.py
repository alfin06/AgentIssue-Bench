import requests
import time
import os
import json
import re
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Configuration ---
GITHUB_TOKEN = os.environ.get("GITHUB_PAT")
if not GITHUB_TOKEN:
    print("Error: GITHUB_PAT environment variable not set.")
    print("Please set it by running: export GITHUB_PAT='your_token'")
    exit()

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHubIssuePRLinkFinder/1.0"
}
BASE_URL = "https://api.github.com/search/issues"

PR_URL_REGEX = re.compile(r"(https://github\.com/[\w.-]+/[\w.-]+/pull/\d+)")

# --- Helper Functions ---
def count_operators(term_lists):
    num_ors = 0
    num_ands = 0
    active_lists = 0
    for term_list in term_lists:
        if term_list:
            num_ors += max(0, len(term_list) - 1)
            active_lists +=1
    if active_lists > 1:
        num_ands = active_lists - 1
    return num_ors + num_ands

def construct_query(agent_terms, issue_terms, repro_terms, base_qualifiers=""):
    all_term_lists = [agent_terms, issue_terms, repro_terms]
    keyword_operators = 0
    active_keyword_lists = 0
    for term_list in all_term_lists:
        if term_list:
            keyword_operators += max(0, len(term_list) - 1)
            active_keyword_lists +=1
    if active_keyword_lists > 1:
        keyword_operators += active_keyword_lists -1
    
    MAX_KEYWORD_OPERATORS = 5 
    if keyword_operators > MAX_KEYWORD_OPERATORS:
        print(f"\n--- KEYWORD QUERY COMPLEXITY ERROR ---")
        print(f"The combination of your keywords would generate {keyword_operators} boolean operators.")
        print(f"GitHub API allows a maximum of {MAX_KEYWORD_OPERATORS} total (AND, OR, NOT) operators.")
        print(f"Please reduce the number of keywords in your keyword lists.")
        return None

    query_segments = []
    if agent_terms:
        query_segments.append("(" + " OR ".join([f'"{term}"' if " " in term else term for term in agent_terms]) + ")")
    if issue_terms:
        query_segments.append("(" + " OR ".join([f'"{term}"' if " " in term else term for term in issue_terms]) + ")")
    if repro_terms:
        query_segments.append("(" + " OR ".join([f'"{term}"' if " " in term else term for term in repro_terms]) + ")")
    
    keyword_query_string = " AND ".join(filter(None, query_segments))

    if keyword_query_string:
        keyword_query_string += " in:title,body"

    if base_qualifiers:
        if keyword_query_string:
            return f"{keyword_query_string} {base_qualifiers}"
        else:
            return base_qualifiers
    else: 
        return keyword_query_string if keyword_query_string else None


def scrape_pr_urls_from_issue_page(issue_html_url, request_headers):
    print(f"      Scraping for PR URLs on: {issue_html_url}")
    pr_urls_found = []
    try:
        response = requests.get(issue_html_url, headers=request_headers, timeout=20)
        response.raise_for_status()
        html_content = response.text
        pr_urls_found = list(set(PR_URL_REGEX.findall(html_content)))
        if pr_urls_found:
            print(f"        Found {len(pr_urls_found)} potential PR URL(s) via scraping: {pr_urls_found}")
        else:
            print(f"        No PR URLs found in HTML content via regex.")
    except requests.exceptions.RequestException as e:
        print(f"      Error scraping issue page {issue_html_url}: {e}")
    except Exception as e:
        print(f"      Unexpected error during scraping of {issue_html_url}: {e}")
    return pr_urls_found


def search_github_issues(query, max_pages_per_repo=2, items_per_page=10):
    all_issues_raw = []
    if not query:
        print("  Search query is empty/invalid, skipping API call.")
        return all_issues_raw
        
    print(f"  Executing search for: {query}")
    for page_num in range(1, max_pages_per_repo + 1):
        params = { "q": query, "sort": "updated", "order": "desc", "per_page": items_per_page, "page": page_num }
        try:
            response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=30)
            if response.status_code == 422:
                print(f"  HTTP Error 422 (Unprocessable Entity). Query: {query}")
                error_details = {}
                try: error_details = response.json()
                except json.JSONDecodeError: print(f"  Response body (not JSON): {response.text[:500]}")
                else: print(f"  Response body: {json.dumps(error_details, indent=2)}")
                return all_issues_raw 
            response.raise_for_status()
            data = response.json()
            issues_page = data.get("items", [])
            all_issues_raw.extend(issues_page)
            print(f"    Page {page_num}: Found {len(issues_page)} issues. Total collected for this repo query: {len(all_issues_raw)}")
            if not issues_page or len(issues_page) < items_per_page or \
                (data.get('total_count',0) <= items_per_page * page_num and len(all_issues_raw) >= data.get('total_count',0)) or \
                len(all_issues_raw) >= 990 : 
                if len(all_issues_raw) >= 990 and data.get('total_count',0) > 1000: print("  Warning: Approaching GitHub's 1000 result limit for this query within the repo.")
                break
            time.sleep(1.5) 
        except requests.exceptions.HTTPError as e: 
            print(f"  HTTP Error during search: {e}")
            if response.status_code == 403: 
                print("  Rate limit likely hit during search. Sleeping for 60s.")
                time.sleep(60) 
            break 
        except Exception as e:
            print(f"  Error during search: {e}")
            break
    return all_issues_raw

# --- Main Execution ---
if __name__ == "__main__":
    TARGET_REPOSITORIES = [
        "crewAIInc/crewAI"
        # Add more "owner/repo" strings here
    ]

    # Adjusted keywords to be within limits (example)
    custom_agent_terms = ["agent", "tool use"]      # 2 terms => 1 OR
    custom_issue_terms = ["bug", "error"]           # 2 terms => 1 OR
    custom_repro_terms = ["reproduce", "minimal example"] # 2 terms => 1 OR
    # Total operators: 1+1+1+2 = 5. This is within the limit.
    
    date_filter = "2025-01-01" 
    # MODIFIED: Added '-reason:duplicate' to exclude issues closed as duplicates.
    base_extra_qualifiers = f"is:issue state:closed -reason:duplicate updated:>={date_filter}"

    all_discovered_issues_raw = [] 
    
    max_pages_per_repo_search = 3 
    items_per_page_search = 30
    output_filename = "results.json"

    print(f"--- Starting targeted issue search in {len(TARGET_REPOSITORIES)} repositories ---")
    for repo_name in TARGET_REPOSITORIES:
        print(f"\n--- Searching in repository: {repo_name} ---")
        current_repo_qualifiers = f"repo:{repo_name} {base_extra_qualifiers}"
        current_search_query = construct_query(
            custom_agent_terms,
            custom_issue_terms,
            custom_repro_terms,
            base_qualifiers=current_repo_qualifiers
        )

        if not current_search_query:
            print(f"  Skipping {repo_name} due to invalid query construction (e.g., keyword complexity or empty).")
            continue
            
        repo_issues = search_github_issues(
            query=current_search_query,
            max_pages_per_repo=max_pages_per_repo_search,
            items_per_page=items_per_page_search
        )
        
        if repo_issues:
            print(f"  Fetched {len(repo_issues)} raw issues from {repo_name}.")
            all_discovered_issues_raw.extend(repo_issues)
        else:
            print(f"  No issues found in {repo_name} for the current query and page limits.")
        time.sleep(2) 

    if all_discovered_issues_raw:
        processed_issues = []
        print(f"\n--- Processing {len(all_discovered_issues_raw)} total issues found to find and link PRs ---")
        
        for i, issue_data in enumerate(all_discovered_issues_raw):
            print(f"Processing issue {i+1}/{len(all_discovered_issues_raw)}: {issue_data.get('html_url')}")
            linked_pr_url = None
            api_pr_link_was_found = False # Flag to track if API provided the link
            
            # 1. Try direct API link first
            if issue_data.get('pull_request') and issue_data['pull_request'].get('html_url'):
                linked_pr_url = issue_data['pull_request']['html_url']
                api_pr_link_was_found = True
                print(f"  Found PR via direct API 'pull_request' field: {linked_pr_url}")
            
            # 2. If not found from API, try scraping the issue page (HTML)
            if not linked_pr_url and issue_data.get('html_url'):
                print(f"  No direct PR link from API. Attempting to scrape issue page: {issue_data.get('html_url')}")
                time.sleep(0.5) 
                scraped_pr_urls = scrape_pr_urls_from_issue_page(issue_data.get('html_url'), HEADERS)
                if scraped_pr_urls:
                    # MODIFIED: Get the last PR mentioned from the scraped list.
                    linked_pr_url = scraped_pr_urls[-1] 
                    print(f"    Found last mentioned PR via scraping: {linked_pr_url}")

            # 3. Always add the issue. linked_pr_url will be None if not found.
            processed_issues.append({
                "github_url": issue_data.get("html_url"),
                "title": issue_data.get("title"),
                "description": issue_data.get("body"),
                "linked_pr_url": linked_pr_url, # This will be None if no PR was found
                "closed_at": issue_data.get("closed_at"),
                "state": issue_data.get("state"),
                "repository_url": issue_data.get("repository_url"),
                "api_pr_link_found": api_pr_link_was_found,
                "scraped_pr_link_used": (not api_pr_link_was_found) and bool(linked_pr_url)
            })
            
            if linked_pr_url:
                    print(f"  Added issue to output with PR link: {issue_data.get('html_url')}")
            else:
                    print(f"  Added issue to output (no PR link found): {issue_data.get('html_url')}")
            print("-" * 10)
            if (i+1) % 10 == 0 : print(f"  Processed {i+1}/{len(all_discovered_issues_raw)} issues...")

        with open(output_filename, "w", encoding='utf-8') as f:
            json.dump(processed_issues, f, indent=4)
        
        print(f"\n--- Processing Complete ---")
        num_with_pr = sum(1 for issue in processed_issues if issue.get("linked_pr_url"))
        print(f"{len(processed_issues)} total issues processed and saved to {output_filename}")
        print(f"{num_with_pr} issues had a linked PR found (via API or scraping).")
        print(f"{len(processed_issues) - num_with_pr} issues did not have a PR link found and have 'linked_pr_url: null'.")
        
        if len(all_discovered_issues_raw) >= (max_pages_per_repo_search * items_per_page_search * len(TARGET_REPOSITORIES) * 0.9) and \
            any(len(r) >= (max_pages_per_repo_search*items_per_page_search*0.9) for r in [all_discovered_issues_raw]): # Heuristic for hitting limits
                print("\nReminder: You might have hit GitHub's 1000 result limit within one or more repo searches if many issues were found.")
    else:
        print("No issues found across the targeted repositories, or an error occurred during search.")

    print("\n--- Next Steps ---")
    print(f"Review '{output_filename}'. Issues without a PR will have 'linked_pr_url: null'.")
