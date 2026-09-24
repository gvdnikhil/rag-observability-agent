# Nimbus Platform — Deployment Guide

Nimbus supports three deployment modes: Managed Cloud, Self-Hosted, and Hybrid.

Managed Cloud is the default mode. Nimbus provisions and operates the control plane on your behalf across AWS us-east-1 and eu-west-1. New environments are ready within 4 minutes of creation.

Self-Hosted mode runs the full Nimbus control plane inside your own Kubernetes cluster. It requires Kubernetes 1.27 or later, a PostgreSQL 14+ database, and at minimum 3 worker nodes with 4 vCPU / 16GB RAM each.

Hybrid mode keeps the control plane in Nimbus Managed Cloud while running data-plane workers inside your own VPC, connected via an outbound-only WireGuard tunnel. This is the recommended mode for customers with strict data-residency requirements.

Every deployment mode supports zero-downtime upgrades. Upgrades are rolled out node-by-node with automatic rollback if health checks fail for more than 90 seconds.
