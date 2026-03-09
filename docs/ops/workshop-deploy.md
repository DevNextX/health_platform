Workshop Deploy Instructions
===========================

Purpose
-------
This workflow allows workshop participants to push branches (for example `feature/alice`, `workshop/bob`) and automatically build+push both frontend and backend images and deploy them into a per-branch Kubernetes namespace on a shared cluster.

Namespace naming
----------------
- Branch names are sanitized to create namespace names: lowercase, invalid chars replaced with `-`, trimmed. Example: `feature/Alice-TEST` -> `ws-feature-alice-test`.
- Namespaces are prefixed with `ws-` to avoid collisions with cluster namespaces used by other teams.

Image tags
----------
- Images are pushed to GHCR with tags derived from the sanitized branch name:
  - frontend: `ghcr.io/<org>/health-platform-frontend:<branch>-<short-sha>`
  - backend: `ghcr.io/<org>/health-platform-backend:<branch>-<short-sha>`

Resource requests and limits
---------------------------
- Both backend and frontend pods are deployed with resource requests and limits set to:
  - CPU request: `250m` (0.25 CPU)
  - Memory request: `200Mi`
  - CPU limit: `250m`
  - Memory limit: `200Mi`
- These values ensure the cluster's scheduler accounts for resource usage and will enable autoscaling behavior configured at the cluster level (HPA/VPA) if present.

How to trigger
--------------
- Push to a branch matching these patterns: `feature/**`, `workshop/**`, `dev/**`.
- Or run the workflow manually via GitHub UI: `Actions -> Workshop Build & Deploy per-branch -> Run workflow` and provide the `branch` input.

Testing guidance
----------------
- To test without impacting production resources, create a short-lived branch `workshop/test-<yourname>` and push a tiny change (e.g., edit README).
- Monitor the Actions run for `build-and-push` and `deploy` jobs. Verify images are present in GHCR and the `ws-<sanitized-branch>` namespace has `backend` and `frontend` deployments.
- Example kubectl commands (requires cluster kubeconfig configured in repo secrets and runner environment):

```bash
# view pods
kubectl get pods -n ws-<sanitized-branch>

# view resources
kubectl describe deployment backend -n ws-<sanitized-branch>
kubectl describe deployment frontend -n ws-<sanitized-branch>

# get logs
kubectl logs deployment/backend -n ws-<sanitized-branch> --tail=100
kubectl logs deployment/frontend -n ws-<sanitized-branch> --tail=100
```

Cleanup
-------
- To remove the per-branch environment when no longer needed:

```bash
kubectl delete namespace ws-<sanitized-branch>
```

Security notes
--------------
- The workflow creates a `ghcr-secret` in each namespace using the `GITHUB_TOKEN`. For long-lived workshop namespaces consider using a pull secret with limited scope or a service account with least privilege.

Namespace safeguards
--------------------
- The workflow automatically applies a `LimitRange` and a `ResourceQuota` to each `ws-` namespace using defaults (and values read from `deploy/config/development.env` if available). This prevents a single workshop namespace from exhausting cluster resources. Current quota defaults applied by the workflow are:
  - requests.cpu: 4
  - requests.memory: 8Gi
  - limits.cpu: 8
  - limits.memory: 16Gi

Further improvements
--------------------
- Use SHA suffixes for image tags to avoid surprising updates when branches are rebuilt.
- Add Health checks / readiness probes to the container specs in the manifest.
- Add HPA (HorizontalPodAutoscaler) template or integrate cluster-level autoscaler parameters to exercise autoscaling during the workshop.
