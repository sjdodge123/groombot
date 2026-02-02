import os
import json
import urllib.request
import sys

def graphql_request(api_key, query, variables=None):
    if variables is None:
        variables = {}
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(e)
        return {}

def main():
    api_key = os.environ.get("LINEAR_API_KEY")
    # Read parent issue ID from export
    try:
        with open("./input-output-data/parent_issue_export.json") as f:
            data = json.load(f)
            parent_id = data["meta"]["parentIssueId"]
    except:
        print("No export found")
        return

    query = """
    query GetTeamStates($id: String!) {
      issue(id: $id) {
        team {
          id
          name
          states {
            nodes {
              id
              name
              type
            }
          }
        }
      }
    }
    """
    res = graphql_request(api_key, query, {"id": parent_id})
    team = res.get("data", {}).get("issue", {}).get("team", {})
    print(f"Team: {team.get('name')}")
    for state in team.get("states", {}).get("nodes", []):
        print(f"State: {state['name']} ({state['type']}) -> {state['id']}")

if __name__ == "__main__":
    main()
