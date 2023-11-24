# Azure Infrastructure Deployment with Terraform

## Overview

This project contains Terraform configurations to deploy and manage Azure resources, including Resource Groups, Virtual Machines, Container Apps, Gateways, Storage Accounts, and KeyVaults. The project is structured to use Terraform modules for reusable and maintainable infrastructure as code practices.

## Prerequisites
    Terraform v1.6.3 or higher
    Azure CLI or Azure account credentials configured
    Basic understanding of Terraform syntax and Azure services

## Directory Structure

### modules:
Contains reusable Terraform modules for different Azure resources like container_app, gateway, etc.
### environments:
Terraform configurations for different environments like staging and production.
### main.tf:
The root Terraform configuration file that calls modules and configures providers.
### .gitignore:
Gitignore file to exclude sensitive files and directories.

## Usage

### Initialization:
Navigate to the root of the project and initialize Terraform.

``` bash
terraform init
```

### Configuration:
Update the terraform.tfvars or equivalent files in the environments directory with necessary values.

### Planning:
Review the changes that will be applied.
``` bash
terraform plan
```

### Apply Configuration:
Apply the Terraform configuration to create resources.

``` bash
terraform apply
```

### Apply Configuration to Specific Environment:
Apply the Terraform configuration to create resources in a specific environment.

``` bash
terraform apply -var-file=environments/staging/terraform.tfvars
```



### Destruction (If Necessary):
To destroy the resources managed by Terraform.

``` bash
terraform destroy
```
