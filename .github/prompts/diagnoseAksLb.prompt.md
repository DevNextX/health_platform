---
name: diagnoseAksLb
description: Diagnose AKS LoadBalancer connection refusals and low connection counts.
argument-hint: "Service/ports, externalTrafficPolicy, pod replica distribution, LB probe config, client errors"
---

You are troubleshooting a Kubernetes workload on Azure AKS exposed via a `Service` of type `LoadBalancer` (Public or Internal). Clients report they cannot scale concurrent TCP connections (e.g., MQTT) and see errors like `ECONNREFUSED` or timeouts.

## Inputs
Use the provided context (or ask for it if missing):
- AKS networking mode (e.g., Azure CNI overlay), nodepool count, node count
- The Service spec (ports, `nodePort`, `externalTrafficPolicy`, `healthCheckNodePort`, annotations)
- Pod replica count and distribution across nodes (output of `kubectl get pod -o wide`)
- Client test details: tool/command, connection count, interval, error types (`ECONNREFUSED` vs timeout)
- Azure Load Balancer configuration from Portal:
  - Load balancing rule for the target port
  - Health probe protocol/port/path used by that rule
  - Backend pool membership and backend health

## Goals
1. Determine whether failures originate from:
   - Azure LB health probe/backend selection
   - Kubernetes Service semantics (`externalTrafficPolicy` Local vs Cluster)
   - Node-level forwarding (kube-proxy/iptables/IPVS) behavior
   - Application/broker limits (max connections, per-IP limits, fd/ulimit, accept backlog)
   - Client-side issues (duplicate client IDs, aggressive reconnect)
2. Provide a minimal set of validation steps to prove the root cause.
3. Recommend the safest fix options, preserving source IP if required.

## Method (step-by-step)
### 1) Classify the symptom by error type
- If the client sees **timeouts**: prioritize routing/NAT/SNAT/NSG/UDR investigation.
- If the client sees **`ECONNREFUSED` / immediate reset**: prioritize "traffic is reaching a node/port and being explicitly rejected" (often Service semantics or app rejection).

### 2) Check Service semantics and pod placement
- If `externalTrafficPolicy: Local` and the workload has **few replicas** (especially 1), expect that only nodes with local endpoints should accept NodePort traffic; other nodes may reject.
- Capture:
  - `externalTrafficPolicy`
  - `healthCheckNodePort` (if present)
  - servicePort ↔ nodePort mapping
  - number of endpoints and which nodes host them

### 3) Map Azure LB rule → probe → backend health
- Identify which **health probe** the **specific LB rule for the target service port** is using.
- Verify whether that probe truly filters to only nodes with local endpoints when `externalTrafficPolicy: Local` is required.
- If the LB rule uses a probe that can succeed on nodes **without local endpoints** (e.g., probing a different HTTP service/port), the LB may mark many nodes healthy and route connections to nodes that will reject, causing `ECONNREFUSED`.

### 4) Validate with on-the-wire checks aligned to probe protocol
- Do not rely on TCP connect checks if the LB probe is HTTP.
- If probe is HTTP, run:
  - `curl -s -o /dev/null -w "%{http_code}\n" http://<node-ip>:<probePort><probePath>`
  on each node IP and compare nodes with and without endpoints.
- Optionally confirm which node returns RST by packet capture on nodes.

### 5) Rule out application/broker limits
- Check broker logs for max connections, per-IP limits, rate limits, and fd exhaustion.
- Confirm client uses unique IDs per connection if protocol requires it (e.g., MQTT `clientId`).
- Try increasing connection interval to separate rate limits from hard connection caps.

## Fix guidance
Provide recommendations in this order (based on constraints):
- If source IP preservation is **NOT required**: prefer `externalTrafficPolicy: Cluster` for stability.
- If source IP preservation **IS required** (`externalTrafficPolicy: Local`):
  - Ensure the LB rule’s probe filters nodes correctly (probe must fail on nodes without local endpoints).
  - Avoid binding the LB probe to an unrelated port/service that succeeds on all nodes.
  - Consider increasing replicas and spreading across nodes to reduce chance of routing to nodes without endpoints.

## Output format
- **Root cause hypothesis** (1–2 sentences)
- **Evidence checklist** (what confirms/denies it)
- **Exact commands to run** (kubectl + curl/nc)
- **Recommended fix** (primary + fallback), including tradeoffs (source IP, stability)
- **Post-fix verification** steps
