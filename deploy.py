# Install fabric-cicd: https://microsoft.github.io/fabric-cicd/
from azure.identity import InteractiveBrowserCredential, ClientSecretCredential
from fabric_cicd import FabricWorkspace, publish_all_items, change_log_level
import argparse
import os

#change_log_level("DEBUG") # Uncomment for more verbose logging

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# Change default=False to action="store_true" for boolean flag
parser.add_argument("--spn-auth", action="store_true", default=False, help="Use Service Principal Name (SPN) for authentication.")
parser.add_argument("--workspace", default = "RR - Pipeline Refresh Demo", help="Target Fabric workspace name.")
parser.add_argument("--src", default = ".\\src", help="Source directory containing Fabric items (e.g., .pbip components).")

args = parser.parse_args()

spn_auth = args.spn_auth
workspace_name = args.workspace
src_path = args.src

# Authentication (SPN or Interactive)

if (not spn_auth):
    print("Authenticating interactively (this path is generally not supported in pipelines).")
    credential = InteractiveBrowserCredential() # This will attempt to open a browser window
else:
    print("Authenticating using Service Principal Name (SPN) via environment variables.")
    client_id = os.getenv("FABRIC_CLIENT_ID")
    client_secret = os.getenv("FABRIC_CLIENT_SECRET")
    tenant_id = os.getenv("FABRIC_TENANT_ID")

    # Add a check for missing environment variables for clearer error messages
    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("FABRIC_CLIENT_ID, FABRIC_CLIENT_SECRET, or FABRIC_TENANT_ID environment variable is not set. Cannot perform SPN authentication.")

    credential = ClientSecretCredential(client_id=client_id, client_secret=client_secret, tenant_id=tenant_id)

target_workspace = FabricWorkspace(    
    workspace_name = workspace_name,    
    repository_directory = src_path,
    item_type_in_scope = ["SemanticModel", "Report"],      
    token_credential = credential,
)

print(f"Attempting to publish all items to workspace: '{workspace_name}' from source: '{src_path}'")
publish_all_items(target_workspace)
print("Publishing process initiated. Check Fabric workspace for status.")