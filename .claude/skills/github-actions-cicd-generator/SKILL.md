---
name: github-actions-cicd-generator
description: Generate production-ready GitHub Actions CI/CD workflows for building Docker images, running tests, and deploying Helm charts to Kubernetes with support for Minikube testing and cloud deployment.
version: 1.0.0
---

# GitHub Actions CI/CD Workflow Generator Skill

## When to Use This Skill

Use this skill when you need to:
- Generate GitHub Actions workflows for CI/CD pipelines
- Automate Docker image builds and pushes to a container registry
- Run test suites (unit, integration, e2e) as part of CI
- Deploy applications to Kubernetes via Helm charts
- Set up Minikube-based testing in CI before cloud deployment
- Create multi-environment pipelines (dev, staging, production)
- Standardize CI/CD across multiple services in a repository

## How This Skill Works

1. **Gather Pipeline Information**
   - Service name, Dockerfile path, and build context
   - Docker registry (Docker Hub, GHCR, ACR, ECR)
   - Test commands and frameworks
   - Helm chart path and release name
   - Target environments and Kubernetes cluster details

2. **Generate Workflow File**
   - Create `.github/workflows/deploy.yml` with all jobs
   - Configure triggers (push, pull_request, manual dispatch)
   - Set up secret references for registry credentials and kubeconfig
   - Add caching for Docker layers and dependencies

3. **Apply Best Practices**
   - Multi-stage jobs with proper dependencies
   - Secret management via GitHub Secrets (never hardcoded)
   - Docker layer caching for faster builds
   - Helm lint and dry-run before deploy
   - Environment-specific value overrides
   - Concurrency control to prevent duplicate deployments

4. **Validate and Document**
   - List all required GitHub Secrets to configure
   - Provide Minikube local testing instructions
   - Include rollback and manual dispatch guidance

## Output Files Generated

```
.github/
└── workflows/
    └── deploy.yml              # Full CI/CD pipeline
```

## Instructions

### 1. Full Pipeline Template (.github/workflows/deploy.yml)

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: "Target environment"
        required: true
        default: "staging"
        type: choice
        options:
          - staging
          - production

permissions:
  contents: read
  packages: write

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  REGISTRY: {{ registry }}                    # e.g. ghcr.io, docker.io
  IMAGE_NAME: {{ image-name }}                # e.g. ${{ github.repository }}
  HELM_CHART_PATH: {{ helm-chart-path }}      # e.g. ./charts/my-service
  HELM_RELEASE_NAME: {{ release-name }}       # e.g. my-service
  KUBE_NAMESPACE: {{ namespace }}              # e.g. default

jobs:
  # ──────────────────────────────────────────────
  # Job 1: Lint & Test
  # ──────────────────────────────────────────────
  test:
    name: Lint & Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint
        run: |
          pip install ruff
          ruff check .

      - name: Run tests
        run: |
          pytest tests/ --tb=short --junitxml=test-results.xml -q
        env:
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml

  # ──────────────────────────────────────────────
  # Job 2: Build & Push Docker Image
  # ──────────────────────────────────────────────
  build:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: test
    outputs:
      image-tag: ${{ steps.meta.outputs.version }}
      image-digest: ${{ steps.build-push.outputs.digest }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_PASSWORD }}

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        id: build-push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64

  # ──────────────────────────────────────────────
  # Job 3: Helm Lint & Validate
  # ──────────────────────────────────────────────
  helm-validate:
    name: Helm Lint & Validate
    runs-on: ubuntu-latest
    needs: test
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: "v3.14.0"

      - name: Lint Helm chart
        run: helm lint ${{ env.HELM_CHART_PATH }}

      - name: Template (dry-run) Helm chart
        run: |
          helm template ${{ env.HELM_RELEASE_NAME }} ${{ env.HELM_CHART_PATH }} \
            --set image.tag=test \
            --debug

  # ──────────────────────────────────────────────
  # Job 4: Minikube Integration Test (PRs only)
  # ──────────────────────────────────────────────
  minikube-test:
    name: Minikube Integration Test
    runs-on: ubuntu-latest
    needs: [build, helm-validate]
    if: github.event_name == 'pull_request'
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Start Minikube
        uses: medyagh/setup-minikube@latest
        with:
          minikube-version: "latest"
          kubernetes-version: "v1.30.0"
          driver: docker
          cpus: 2
          memory: 4096

      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: "v3.14.0"

      - name: Build image inside Minikube
        run: |
          eval $(minikube docker-env)
          docker build -t ${{ env.IMAGE_NAME }}:test .

      - name: Deploy to Minikube via Helm
        run: |
          helm install ${{ env.HELM_RELEASE_NAME }}-test ${{ env.HELM_CHART_PATH }} \
            --set image.repository=${{ env.IMAGE_NAME }} \
            --set image.tag=test \
            --set image.pullPolicy=Never \
            --set replicaCount=1 \
            --wait --timeout=120s

      - name: Verify deployment is running
        run: |
          kubectl get pods -l app.kubernetes.io/instance=${{ env.HELM_RELEASE_NAME }}-test
          kubectl wait --for=condition=ready pod \
            -l app.kubernetes.io/instance=${{ env.HELM_RELEASE_NAME }}-test \
            --timeout=90s

      - name: Run smoke tests
        run: |
          SERVICE_URL=$(minikube service ${{ env.HELM_RELEASE_NAME }}-test --url)
          echo "Service URL: $SERVICE_URL"
          curl -sf "$SERVICE_URL/health" || exit 1

      - name: Collect logs on failure
        if: failure()
        run: |
          echo "=== Pod Status ==="
          kubectl get pods -l app.kubernetes.io/instance=${{ env.HELM_RELEASE_NAME }}-test
          echo "=== Pod Logs ==="
          kubectl logs -l app.kubernetes.io/instance=${{ env.HELM_RELEASE_NAME }}-test --tail=100
          echo "=== Events ==="
          kubectl get events --sort-by=.metadata.creationTimestamp | tail -20

      - name: Cleanup
        if: always()
        run: helm uninstall ${{ env.HELM_RELEASE_NAME }}-test --ignore-not-found

  # ──────────────────────────────────────────────
  # Job 5: Deploy to Staging
  # ──────────────────────────────────────────────
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, helm-validate]
    if: github.ref == 'refs/heads/develop' && github.event_name == 'push'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: "v3.14.0"

      - name: Configure kubeconfig
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBE_CONFIG_STAGING }}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Deploy Helm chart to Staging
        run: |
          helm upgrade --install ${{ env.HELM_RELEASE_NAME }} ${{ env.HELM_CHART_PATH }} \
            --namespace ${{ env.KUBE_NAMESPACE }} \
            --create-namespace \
            --set image.repository=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }} \
            --set image.tag=${{ needs.build.outputs.image-tag }} \
            -f ${{ env.HELM_CHART_PATH }}/values-staging.yaml \
            --wait --timeout=300s \
            --atomic

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/${{ env.HELM_RELEASE_NAME }} \
            -n ${{ env.KUBE_NAMESPACE }} --timeout=120s

  # ──────────────────────────────────────────────
  # Job 6: Deploy to Production
  # ──────────────────────────────────────────────
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: [build, helm-validate]
    if: >
      (github.ref == 'refs/heads/main' && github.event_name == 'push') ||
      (github.event_name == 'workflow_dispatch' && github.event.inputs.environment == 'production')
    environment:
      name: production
      url: https://app.example.com
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Helm
        uses: azure/setup-helm@v4
        with:
          version: "v3.14.0"

      - name: Configure kubeconfig
        run: |
          mkdir -p $HOME/.kube
          echo "${{ secrets.KUBE_CONFIG_PRODUCTION }}" | base64 -d > $HOME/.kube/config
          chmod 600 $HOME/.kube/config

      - name: Deploy Helm chart to Production
        run: |
          helm upgrade --install ${{ env.HELM_RELEASE_NAME }} ${{ env.HELM_CHART_PATH }} \
            --namespace ${{ env.KUBE_NAMESPACE }} \
            --create-namespace \
            --set image.repository=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }} \
            --set image.tag=${{ needs.build.outputs.image-tag }} \
            -f ${{ env.HELM_CHART_PATH }}/values-production.yaml \
            --wait --timeout=300s \
            --atomic

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/${{ env.HELM_RELEASE_NAME }} \
            -n ${{ env.KUBE_NAMESPACE }} --timeout=120s

      - name: Post-deployment health check
        run: |
          sleep 10
          kubectl exec -n ${{ env.KUBE_NAMESPACE }} \
            deploy/${{ env.HELM_RELEASE_NAME }} -- \
            curl -sf http://localhost:8000/health || exit 1
```

### 2. GHCR (GitHub Container Registry) Variant

When using GHCR instead of Docker Hub, replace the login step:

```yaml
      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
```

And set the env:

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
```

### 3. ACR (Azure Container Registry) Variant

```yaml
      - name: Log in to Azure Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.ACR_LOGIN_SERVER }}
          username: ${{ secrets.ACR_USERNAME }}
          password: ${{ secrets.ACR_PASSWORD }}
```

### 4. ECR (AWS Elastic Container Registry) Variant

```yaml
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ secrets.AWS_REGION }}

      - name: Log in to Amazon ECR
        uses: aws-actions/amazon-ecr-login@v2
```

### 5. Node.js / Next.js Frontend Test Job Variant

Replace the test job for frontend services:

```yaml
  test:
    name: Lint & Test
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci
        working-directory: frontend

      - name: Lint
        run: npm run lint
        working-directory: frontend

      - name: Run tests
        run: npm test -- --ci --coverage
        working-directory: frontend

      - name: Build
        run: npm run build
        working-directory: frontend
```

## Required GitHub Secrets

Configure these in **Settings > Secrets and variables > Actions**:

| Secret | Description | Required For |
|--------|-------------|--------------|
| `DOCKER_USERNAME` | Docker Hub username | Docker Hub registry |
| `DOCKER_PASSWORD` | Docker Hub access token | Docker Hub registry |
| `KUBE_CONFIG_STAGING` | Base64-encoded kubeconfig for staging cluster | Staging deploy |
| `KUBE_CONFIG_PRODUCTION` | Base64-encoded kubeconfig for production cluster | Production deploy |
| `TEST_DATABASE_URL` | Database URL for test suite | Test job |

**For GHCR:** No extra secrets needed (`GITHUB_TOKEN` is automatic).

**For ACR (Azure):**
| Secret | Description |
|--------|-------------|
| `ACR_LOGIN_SERVER` | e.g. `myregistry.azurecr.io` |
| `ACR_USERNAME` | Service principal app ID |
| `ACR_PASSWORD` | Service principal password |

**For ECR (AWS):**
| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | IAM access key |
| `AWS_SECRET_ACCESS_KEY` | IAM secret key |
| `AWS_REGION` | e.g. `us-east-1` |

## Example Usage

### FastAPI Backend Service

```
Service Name: backend-api
Registry: ghcr.io
Helm Chart Path: ./charts/backend-api
Release Name: backend-api
Namespace: app
Environments: staging (develop branch), production (main branch)
```

### Next.js Frontend Service

```
Service Name: frontend-web
Registry: ghcr.io
Helm Chart Path: ./charts/frontend-web
Release Name: frontend-web
Namespace: app
Test Framework: Node.js / Jest
```

### Minikube Local Testing

```bash
# Encode your kubeconfig for secrets
cat ~/.kube/config | base64 -w 0

# Test the workflow locally with act (https://github.com/nektos/act)
act push --secret-file .secrets
```

## Security & Best Practices Included

- **Secrets Management**
  - All credentials stored in GitHub Secrets
  - No hardcoded tokens or passwords in workflow
  - Kubeconfig passed as base64-encoded secret
  - Minimal permissions via `permissions` block

- **Build Reliability**
  - Docker layer caching via GitHub Actions cache (`type=gha`)
  - Dependency caching for pip/npm
  - Concurrency control prevents duplicate deploys
  - `cancel-in-progress` stops stale runs

- **Deployment Safety**
  - `--atomic` flag rolls back failed Helm deploys automatically
  - `--wait` ensures pods are ready before marking success
  - GitHub Environments with protection rules for production
  - Helm lint and dry-run validation before every deploy
  - Minikube smoke tests on pull requests

- **Observability**
  - Test result artifacts uploaded for inspection
  - Failure logs collected from Kubernetes on Minikube test failure
  - Deployment rollout status verified post-deploy
  - Post-deployment health check on production

- **Pipeline Design**
  - Multi-stage jobs with explicit dependencies
  - PRs only run tests + Minikube (no deploy)
  - Develop branch deploys to staging
  - Main branch deploys to production
  - Manual dispatch for ad-hoc production deployments

## Customization Examples

### Add Slack Notification on Failure

```yaml
      - name: Notify Slack on failure
        if: failure()
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_URL }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "Deployment failed for ${{ env.HELM_RELEASE_NAME }} on ${{ github.ref_name }}"
            }
```

### Add Matrix Strategy for Multi-Service Builds

```yaml
  build:
    strategy:
      matrix:
        service:
          - { name: backend-api, context: ./backend, dockerfile: ./backend/Dockerfile }
          - { name: frontend-web, context: ./frontend, dockerfile: ./frontend/Dockerfile }
    steps:
      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: ${{ matrix.service.context }}
          file: ${{ matrix.service.dockerfile }}
          push: true
          tags: ${{ env.REGISTRY }}/${{ matrix.service.name }}:${{ github.sha }}
```

### Add Database Migration Step Before Deploy

```yaml
      - name: Run database migrations
        run: |
          kubectl run migration-${{ github.sha }} \
            --image=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.image-tag }} \
            --restart=Never \
            --namespace=${{ env.KUBE_NAMESPACE }} \
            --command -- python -m alembic upgrade head
          kubectl wait --for=condition=complete job/migration-${{ github.sha }} \
            --timeout=120s -n ${{ env.KUBE_NAMESPACE }}
```

### Add Trivy Image Vulnerability Scan

```yaml
      - name: Scan Docker image for vulnerabilities
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ needs.build.outputs.image-tag }}
          format: "sarif"
          output: "trivy-results.sarif"
          severity: "CRITICAL,HIGH"

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: "trivy-results.sarif"
```

## Final Message from Skill

Your GitHub Actions CI/CD workflow is ready!

**Next Steps:**
1. Copy `.github/workflows/deploy.yml` to your repository
2. Replace `{{ placeholder }}` values in the `env:` block with your actual values
3. Configure required GitHub Secrets in your repository settings
4. Set up GitHub Environments (`staging`, `production`) with protection rules
5. Push to `develop` or `main` to trigger the pipeline

**Pro Tips:**
- Use GitHub Environments with required reviewers for production deploys
- Enable branch protection rules to require passing CI before merge
- Use `act` (https://github.com/nektos/act) to test workflows locally
- Add Trivy or Snyk scanning for container vulnerability checks
- Create separate `values-staging.yaml` and `values-production.yaml` for Helm
- Use GHCR (`ghcr.io`) for zero-config registry with GitHub Actions

Happy shipping!
