# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.x.x] - 2023-10-16

### Added

-

### Fixed

-

### Changed

-

### Removed

-

## [0.4.1] - 2024-02-08

### Fixed

- **User Email Case Sensitivity**
  -User email changed to case insensitive for login and registration.


## [0.4.0] - 2024-02-07

### Added

- **Form template editor and viewer**
  - Users can now create and edit form templates for their surveys.
  - Implemented a backend service that fetches form templates from the database and sends them to the user.
  - The templates can be customized by the user before publishing.

- **Survey response**
  - Patients can respond to surveys directly from the Tallulah application or even the embedded form on PAOs website.
  - Implemented a backend service that records survey responses and displays them on the dashboard.
  - The form data is stored in a MongoDB database and Elasticsearch for easy retrieval and analysis.
  - The responses are also visible to all the stakeholders in the PAO.

- **User Roles and Permissions**
  - Introduced user roles and permissions for different user types.
  - Users get a different view of the tallulah web application based on their roles.

- **Storage account to store the media files**
  - Included an Azure Storage account to store media files like images and videos for the form templates.
  - The storage account is created during the Terraform deployment and is accessible via the Tallulah web application.

### Fixed

- **Email Classifier**
  - Fixed a bug where the email classifier did not reconnect to the RabbitMQ queue after a connection failure.
  - Added a retry mechanism to the classifier service to ensure no emails are lost during classification.


## [0.3.0] - 2023-12-15

### Added

- **Elasticsearch + Logstash + Kibana (ELK)**
  - Included ELK stack for logging and monitoring.
  - All logs are pushed to Elasticsearch via Logstash.
  - Kibana is used for visualizing the logs and monitoring the API calls.

- **Customer logo in the email signature**
  - Users can now use their company logo to the email signature.
  - The logo is stored in Azure Blob Storage.

- **Automatic certificate creation in the Terraform script**
  - Included a Terraform script for automatic certificate creation using LetsEncrypt and GoDaddy and binding to the Azure Application Gateway.

### Fixed

- ** Email delete bug **
  - Fixed a bug where emails were not being deleted from the database after delete mailbox call was made.


## [0.2.0] - 2023-11-30

### Added

- **Email sort and filter**
  - Users can now sort and filter their emails based on tags and other metadata.
  - Implemented a backend service that fetches emails from the database and sorts them based on user preferences.

- **Email response**
  - Users can now respond to emails directly from the application based on tags or even individually.
  - Implemented a backend service that responds to emails on behalf of the user.

- **Email templates**
  - Users can now create email templates for frequently sent emails.
  - Implemented a backend service that fetches email templates from the database and sends them to the user.
  - The templates can be customized by the user before sending.
  - The templates also support images in the signature.

- **Mailbox deletion**
  - Users can now delete their mailboxes from the application.
  - Implemented a backend service that deletes the mailbox from the database and the corresponding token from Azure Key Vault.


### Changed

- **Migration to Terraform**
  - Included a terraform deployment script for rolling out all services on Azure Container apps.
  - The application is accessible via the custom domain: `touch.tallulah.ai`, the certificate for which is managed by Terraform.

- **Azure Application Gateway**
  - Included Azure Application Gateway for load balancing, security and traffic management.

- **MongoDB Atlas**
  - Mongodb Atlas now connects via a private endpoint, enhancing security and data integrity.


## [0.1.0] - 2023-10-30

We are thrilled to announce the first release of our product! This release lays the groundwork for efficient email management and processing, with several robust services ensuring security, data integrity, and seamless integration. Our services are containerized for ease of deployment and scalability.

### Added

- **User Account Management**
  - Introduced user account creation and authentication service.
  - Implemented JSON Web Token (JWT) for secure and efficient user authentication.

- **Email Integration and Storage**
  - Users can now link their Outlook mailboxes for seamless integration.
  - Implemented a backend service that polls connected mailboxes every hour, fetching new emails.
  - New emails are stored securely in a MongoDB database.

- **Email Processing and Tagging**
  - All incoming emails are pushed to a RabbitMQ message queue.
  - Emails in the queue are ready for processing and tagging by the Machine Learning (ML) classifier service.

- **Data Backup and Security**
  - Database hosted on Mongodb Atlas with continuous backups and incremental snapshots.
  - All backups are securely stored in Azure Blob Storage, ensuring data integrity and recovery.
  - Refresh tokens are securely stored in Azure Key Vault, enhancing the security posture.

- **Deployment and Scalability**
  - Included a deployment script for rolling out all services on Azure Container apps.
  - The application is accessible via the custom domain: `tallulah.ai`.
  - MongoDB, RabbitMQ, and the backend service are containerized, each running in its own isolated environment.

- **Client Libraries and API Interaction**
  - Added codebase for generating Python and TypeScript clients, facilitating interaction with our REST APIs.

- **Containerization and Microservices**
  - Structured the application into microservices including RabbitMQ, Backend and classifier services.
  - Each service runs in its own container for isolated environments and scalability.

- **Azure AD Integration for Mailbox Addition**
  - Integrated Azure Active Directory (AD) app creation, allowing users to effortlessly link their Outlook mailboxes.
  - Users can now securely add their mailboxes using the permissions and security provided by Azure AD, simplifying the setup process while ensuring robust security protocols are adhered to.

- **Email Classification and Tagging**
  - Implemented a Machine Learning (ML) classifier service that tags incoming emails based on their content.
  - The classifier service is containerized with the model loaded into it at build time.

- **Frontend Application**
  - Added a frontend application for users to interact with the backend services.
  - Users can now add their mailboxes, view their tagged emails.
