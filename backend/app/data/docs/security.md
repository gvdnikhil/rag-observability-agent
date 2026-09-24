# Nimbus Platform — Security Policy

All data in transit to and from Nimbus is encrypted with TLS 1.3. Data at rest is encrypted with AES-256, using per-tenant encryption keys managed through AWS KMS.

Nimbus undergoes an annual SOC 2 Type II audit and a quarterly third-party penetration test. Audit reports are available to Enterprise customers under NDA.

Customer data is logically isolated per tenant at the database layer. There is no shared storage between tenants, even on the Free tier.

Nimbus enforces multi-factor authentication (MFA) for all internal engineering access to production systems. Access to customer data requires a documented support ticket and is logged in an immutable audit trail retained for 400 days.

Security vulnerabilities can be reported to security@nimbus.example and are triaged within 24 hours under Nimbus's responsible disclosure policy.
