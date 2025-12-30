---
title: 'Exercise 06: AI governance and model observability'
layout: default
nav_order: 7
has_children: true
---

# Exercise 06: AI governance and model observability

## Scenario

JumpStarX's AI services use Microsoft Foundry workspace deployments for chat completions that support Health Platform features such as health guidance and FAQs. JumpStarX wants to operate responsibly at enterprise scale, and requires that the platform enforce security best practices, content safety and auditability.

To ensure this, the platform must enforce:

- Identity-only access
- Content safety and guardrails
- Platform-native logging
- Auditability
- Model safety monitoring
- Operational observability

Microsoft Foundry emits **first-class diagnostic logs** for request behavior, safety events, latency, and auditing.

This exercise enables Responsible AI controls through a combination of infrastructure configuration and application-level safety enforcement. You will use GitHub Copilot to configure identity-only access and diagnostic logging via Bicep templates, add content safety filtering at the application layer, and deploy an observability workbook to visualize operational data.

## Objectives

After completing this exercise, you'll be able to:

- Review and enforce Entra ID-only authentication using Copilot and Bicep
- Restrict Microsoft Foundry connections to Managed Identity and validate RBAC assignments
- Enable Microsoft Foundry diagnostic logs and verify log ingestion
- Configure content safety filters at the application layer using Copilot
- Test and validate safety controls through safe and unsafe prompts
- Deploy an observability workbook using Copilot-generated Bicep templates
- Visualize operational diagnostics including request volume, latency, and operation breakdowns

## Duration

* **Estimated Time:** 30–45 minutes
