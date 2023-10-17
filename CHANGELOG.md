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

## [0.1.0] - 2023-10-16

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
  - Implemented continuous database backup, with snapshots taken every 30 minutes.
  - All backups are securely stored in Azure Blob Storage, ensuring data integrity and recovery.
  - Refresh tokens are securely stored in Azure Key Vault, enhancing the security posture.

- **Deployment and Scalability**
  - Included a deployment script for rolling out all services on Azure Container apps.
  - The application is accessible via the custom domain: `tallulah.ai`.
  - MongoDB, RabbitMQ, and the backend service are containerized, each running in its own isolated environment.

- **Client Libraries and API Interaction**
  - Added codebase for generating Python and TypeScript clients, facilitating interaction with our REST APIs.

- **Containerization and Microservices**
  - Structured the application into microservices including MongoDB, RabbitMQ, and backend services.
  - Each service runs in its own container for isolated environments and scalability.

- **Azure AD Integration for Mailbox Addition**
  - Integrated Azure Active Directory (AD) app creation, allowing users to effortlessly link their Outlook mailboxes.
  - Users can now securely add their mailboxes using the permissions and security provided by Azure AD, simplifying the setup process while ensuring robust security protocols are adhered to.
