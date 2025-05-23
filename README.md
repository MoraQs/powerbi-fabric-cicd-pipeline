# 📘 Power BI (.pbip) CI/CD Pipeline with Azure DevOps and fabric-cicd

## 🚀 Overview

This repository implements a **CI/CD pipeline** for deploying **Power BI `.pbip` semantic models and reports** to Microsoft Fabric workspaces across environments (**DEV → UAT → PROD**) using:

- Azure DevOps Pipelines
- `fabric-cicd` Python CLI
- Service Principal (SPN) authentication
- Self-hosted agent (Windows)

## ✅ Key Features

- **Trigger on push to `main` and `feature/*` branches**
- **Build-only validation for `feature/*`**
- **Multi-stage deployment: DEV → UAT → PROD**
- **Secure SPN-based authentication**
- **Environment-based variables via Azure DevOps Variable Groups**

## ⚙️ Prerequisites

- Azure DevOps Project & Repo
- Microsoft Fabric workspace(s) provisioned
- Registered Microsoft Entra ID App (SPN) with API permissions:
  - `Dataset.ReadWrite.All`
  - `Workspace.Read.All`
- SPN added as **Admin** or **Member** on target workspaces
- A **self-hosted Windows agent** with:
  - Python 3.12+
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

> ⚠️ If this setting is not enabled, your SPN will not be able to authenticate with the Fabric service.

### 🔐 Step 0.2: Create Service Principal in Entra ID & Generate Client Secret

You’ll need a **Service Principal (SPN)** to authenticate programmatically with Microsoft Fabric via Azure DevOps during deployment.

#### 🧾 Follow these steps in Microsoft Entra ID (Azure Portal)

#### 🔹 1. Register a New Application

1. Go to the **[Azure Portal](https://portal.azure.com)**
2. Navigate to: **Microsoft Entra ID** → **App registrations**
3. Click **New registration**
   - **Name**: e.g., `PowerBI-Fabric-CICD`
   - Click **Register**

#### 🔹 2. Copy the Client ID and Tenant ID

After registration, go to the app’s **Overview** page and copy:

- `Application (client) ID`
- `Directory (tenant) ID`

Save them securely for Azure DevOps variable group creation.

#### 🔹 3. Create a Client Secret

1. Go to the **Certificates & secrets** tab
2. Click **New client secret**
   - Add a description: e.g., `CI/CD Deployment Key`
   - Set an expiration period (e.g., 6 or 12 months)
3. Click **Add**
4. Copy the **Value** immediately

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

#### **Grant access to the security group `FabricPipelineDeployer` in each Fabric workspace (DEV, UAT, PROD)**  

- Go to the Fabric workspace → **Manage access**
- Add `FabricPipelineDeployer` group
- Assign role: **Admin** (recommended) or **Contributor**

> 🧠 This avoids hardcoding the SPN per workspace and follows RBAC best practices.

### 🧾 Step 0.4: Create and Set-up Azure DevOps Variable group

Create a variable group e.g., `PowerBIDevelopmentVariables` in Azure DevOps:

| Variable Name             | Value                            | Secret |
|---------------------------|----------------------------------|--------|
| `powerbi_client_id`       | Application (client) ID          | ✅     |
| `powerbi_client_secret`   | Client Secret (Value)            | ✅     |
| `tenant_id`               | Directory (tenant) ID            | ❌     |
| `workspace_name_dev`      | e.g., `ContosoDEV`               | ❌     |
| `workspace_name_uat`      | e.g., `ContosoUAT`               | ❌     |
| `workspace_name_prod`     | e.g., `Contoso`                  | ❌     |
| `workspace_id`(Each wrksp)| `xxxxxxxx-xxxx-xxxx-xxxx-xxx...` | ❌     |

`workspace_id` is the `uuid`, which is a part of your workspace URL. See example below:
`https://app.powerbi.com/groups/`xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`/list?redirectedFromSignup=1&experience=power-bi&clientSideAuth=0`

## 2. 🌿 Branching Strategy

- `main`: Used for **PROD** deployment
- `feature/*`: Used for **DEV → UAT**
- PRs from `feature/* → main` trigger validation builds

### 🚦Pipeline Behavior

- Triggered on changes to:
  - `**/*.SemanticModel/**`
  - `**/*.Report/**`

- Feature branches only run the **Build → DEV → UAT** stages if changes are made to the  `Semantic Model & Report folders`
- Main branch runs full flow: **Build → DEV → UAT → PROD** provided that changes are made to the `Semantic Model & Report folders`
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
