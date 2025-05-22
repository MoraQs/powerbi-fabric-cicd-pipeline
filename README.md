# 📘 Power BI (.pbip) CI/CD Pipeline with Fabric and Azure DevOps

## 🚀 Overview

This repository implements a **CI/CD pipeline** for deploying **Power BI `.pbip` semantic models and reports** to Microsoft Fabric workspaces across environments (**DEV → UAT → PROD**) using:

- Azure DevOps Pipelines  
- `fabric-cicd` Python CLI  
- Service Principal (SPN) authentication  
- Self-hosted agent (Windows)  
- Dataset refresh via Power BI REST API

## ✅ Key Features

- **Trigger on push to `main` and `feature/*` branches**
- **Build-only validation for `feature/*`**
- **Multi-stage deployment: DEV → UAT → PROD**
- **Secure SPN-based authentication**
- **Post-deployment dataset refresh**
- **Environment-based variables via Azure DevOps Variable Groups**

## ⚙️ Prerequisites

- Azure DevOps Project & Repo
- Microsoft Fabric workspace(s) provisioned
- Registered Microsoft Entra ID App (SPN) with API permissions:
  - `Dataset.ReadWrite.All`
  - `Workspace.Read.All`
- SPN added as **Admin** or **Member** on target workspaces
- A **self-hosted Windows agent** with:
  - Python 3+
  - `fabric-cicd` installed (`pip install fabric-cicd`)

## 1. 🛠️ Step-by-Step Setup

### ⚙️ Step 0.1: Prerequisite: Enable SPN Access to Fabric APIs

Before creating your Service Principal (SPN) and configuring your Azure DevOps pipeline, you must enable access to Fabric APIs for service principals:

1. Go to the **Microsoft Fabric Admin Portal**  
   ➤ `https://app.fabric.microsoft.com/admin-portal`
2. Navigate to **Tenant Settings** → **Developer Settings**
3. Locate the option:  
   ✅ **"Service principals can use Fabric APIs"**
4. Set this to **Enabled**
5. *(Recommended)* Restrict access by specifying an Azure AD Security Group or App ID under **"Apply to specific security groups"**

> ⚠️ If this setting is not enabled, your SPN will not be able to authenticate with the Fabric service.

### 🔐 Step 0.2: Create Service Principal in Entra ID & Generate Client Secret

You’ll need a **Service Principal (SPN)** to authenticate programmatically with Microsoft Fabric via Azure DevOps during deployment and dataset refresh.

#### 🧾 Follow these steps in Microsoft Entra ID (Azure Portal)

#### 🔹 1. Register a New Application

1. Go to the **[Azure Portal](https://portal.azure.com)**
2. Navigate to: **Microsoft Entra ID** → **App registrations**
3. Click **New registration**
   - **Name**: `PowerBI-Fabric-CICD`
   - **Supported account types**: **Single tenant** (recommended)
   - Click **Register**

#### 🔹 2. Copy the Client ID and Tenant ID

After registration, go to the app’s **Overview** page and copy:

- `Application (client) ID` → Use this as `powerbi_client_id`
- `Directory (tenant) ID` → Use this as `tenant_id`

Save them securely for Azure DevOps.

#### 🔹 3. Create a Client Secret

1. Go to the **Certificates & secrets** tab
2. Click **New client secret**
   - Add a description: e.g., `CI/CD Deployment Key`
   - Set an expiration period (e.g., 6 or 12 months)
3. Click **Add**
4. Copy the **Value** immediately — use this as `powerbi_client_secret`

> ⚠️ **Important:** You won’t be able to view the secret again once you leave the page.

### ✅ Final Output

| Azure AD Item                  | Azure DevOps Variable           |
|-------------------------------|---------------------------------|
| Application (client) ID       | `powerbi_client_id`             |
| Client Secret (Value)         | `powerbi_client_secret`         |
| Directory (tenant) ID         | `tenant_id`                     |

These will be used in your Azure DevOps pipeline to authenticate the deployment steps using SPN.

#### 🔹 4. (Best Practice) Add Service Principal (SPN) to an Entra Security Group

To manage access securely and consistently across environments:

1. Go to **Microsoft Entra ID** → **Groups**
2. Create a new **Security Group**, e.g., `FabricPipelineDeployer`
3. Add your newly created Service Principal (App) as a **member**

### 🏗️ Step 0.3: Create Fabric/Power BI Workspaces for Each Environment

Create separate workspaces for each deployment environment in Microsoft Fabric:

| Environment | Workspace Name |
|-------------|----------------|
| DEV         | `ContosoDEV`   |
| UAT         | `ContosoUAT`   |
| PROD        | `Contoso`      |

These will be used to isolate deployments by environment stage.

#### **Grant the group access to each Fabric workspace (DEV, UAT, PROD)**  

- Go to the Fabric workspace → **Manage access**
- Add `FabricPipelineDeployer` group
- Assign role: **Admin** (recommended) or **Contributor**

> 🧠 This avoids hardcoding the SPN per workspace and follows RBAC best practices.

### 🧾 Step 0.4: Create and Set-up Azure DevOps Variables

Create a variable group `PowerBIDevelopmentVariables` in Azure DevOps:

| Variable Name             | Value                            | Secret |
|---------------------------|----------------------------------|--------|
| `powerbi_client_id`       | SPN client ID                    | ✅     |
| `powerbi_client_secret`   | SPN secret                       | ✅     |
| `tenant_id`               | Microsoft ENTRA Tenant ID        | ❌     |
| `workspace_name_dev`      | e.g., `ContosoDEV`               | ❌     |
| `workspace_name_uat`      | e.g., `ContosoUAT`               | ❌     |
| `workspace_name_prod`     | e.g., `Contoso`                  | ❌     |
| `dataset_name`            | Name of your Semantic Model      | ❌     |

`workspace_id` is the `uuid`, which is a part of your workspace URL. See example below:
`https://app.powerbi.com/groups/`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`/list?redirectedFromSignup=1&experience=power-bi&clientSideAuth=0`

## 2. 🌿 Branching Strategy

- `main`: Used for UAT and PROD deployment  
- `feature/*`: Used for build-only validation  
- PRs from `feature/* → main` trigger validation builds

### 🚦Pipeline Behavior

- Triggered on changes to:
  - `**/*.SemanticModel/**`
  - `**/*.Report/**`
  - `other files`
- Feature branches only run the **Build → DEV → UAT (on approval)** stage... See `Smart Build Filtering below`
- Main branch runs full flow: **Build → DEV → UAT → PROD**  
- UAT/PROD stages gated by branch checks and approval policies

### 🚚 Deployment Script: `deploy.py`

This script uses `fabric-cicd` to deploy both **Power BI semantic models** and **reports** to a Microsoft Fabric workspace.

#### 🧪 How to Run Locally (for testing)

```bash
python deploy.py ^
  --spn-auth ^
  --workspace "Contoso DEV" ^
  --src "./src"
```

⚠️ Make sure the following environment variables are set in your shell:

- "`FABRIC_CLIENT_ID`"
- "`FABRIC_CLIENT_SECRET`"
- "`FABRIC_TENANT_ID`"

## 🔧 Example Usage in Azure DevOps Pipeline

``` bash
- script: |
    python deploy.py ^
      --spn-auth ^
      --workspace "$(workspace_name)" ^
      --src "$(Build.SourcesDirectory)/src"
  displayName: 'Deploy to $(environment_name) Fabric Workspace'
  env:
    FABRIC_CLIENT_ID: $(powerbi_client_id)
    FABRIC_CLIENT_SECRET: $(powerbi_client_secret)
    FABRIC_TENANT_ID: $(tenant_id)
```

This script step is placed in the Deploy_DEV, Deploy_UAT, and Deploy_PROD stages of the pipeline.

The environment variables are injected securely via the Azure DevOps variable group (`PowerBIDevelopmentVariables`) and mapped inside the job using the env: block

### 🧠 Smart Build Filtering: Conditional Build Execution

To optimize performance and avoid unnecessary builds, the pipeline includes logic that evaluates which files have changed before deciding to run the `Build` stage.

#### ✅ Behavior

- The `Build` stage **always runs** on pushes to the `main` branch.
- On `feature/*` branches, the `Build` stage **only runs if** any files in:
  - `.Report/` (PBIP report folders)
  - `.SemanticModel/` (PBIP model folders)
  have changed.
- If only documentation, `.yml`, or unrelated files were changed (e.g., `README.md`), the `Build` stage is automatically **skipped**.

#### 🔧 YAML Implementation

A special job called `EvaluateBuildRun` is added at the beginning of the `Build` stage:

```yaml
- job: EvaluateBuildRun
  displayName: 'Evaluate File Changes'
  steps:
    - checkout: self
      fetchDepth: 0  # Ensure full Git history so HEAD~1 works

    - powershell: |
        $changes = git diff --name-only HEAD~1 HEAD
        Write-Host "Changed files:"
        $changes
        if ($changes -match '\.Report\\' -or $changes -match '\.SemanticModel\\') {
            Write-Host "##vso[task.setvariable variable=RunBuildStage]true"
        } elseif ("$(Build.SourceBranchName)" -eq "main") {
            Write-Host "##vso[task.setvariable variable=RunBuildStage]true"
        } else {
            Write-Host "##vso[task.setvariable variable=RunBuildStage]false"
        }
      displayName: 'Set RunBuildStage Variable'
```

#### 🧪 Example Usage in Build Jobs

Apply the `RunBuildStage` variable as a condition on each Build job:

```yaml
- job: BPA_SemanticModels
  displayName: 'BPA Semantic Models'
  condition: eq(variables['RunBuildStage'], 'true')
  ...

- job: BPA_Reports
  displayName: 'BPA Reports'
  condition: eq(variables['RunBuildStage'], 'true')
  ...
```

This setup ensures your CI pipeline is `smart`, `efficient`, and only runs validations when meaningful PBIP model or report changes are introduced.