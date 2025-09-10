try:
    page_size = 100  # Jira default page size
    start = 0
    issues = []
    max_issues = 3000  # safety cap
    fields_param = (
        "summary,description,reporter,assignee,created,status,"
        "customfield_17591,customfield_17636,customfield_14707"
    )

    while True:
        remaining = max_issues - len(issues)
        if remaining <= 0:
            print("Reached max_issues cap; stopping pagination.")
            break

        current_limit = min(page_size, remaining)
        # Use Jira Cloud v3 search via SDK's generic GET (stable)
        result = jira.get(
            "rest/api/3/search",
            params={
                "jql": jql_query,
                "startAt": start,
                "maxResults": current_limit,
                "fields": fields_param,
            },
        )

        page_issues = (result or {}).get("issues", [])
        issues.extend(page_issues)

        print(f"Fetched {len(page_issues)} issues (Total so far: {len(issues)})")

        if len(page_issues) < current_limit:
            break  # last page reached

        start += current_limit

    print(f"Found {len(issues)} issues (capped at {max_issues}).")
except Exception as e:
    raise RuntimeError(f"Failed to fetch issues: {e}") from e
