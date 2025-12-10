# GitHub Actions CI/CD for GCP Deployment

This directory contains GitHub Actions workflows for automated deployment to Google Cloud Platform.

## Workflow: Deploy to Google Cloud

**File**: `deploy-to-gcp.yml`

Automatically builds and deploys the video automation system to Cloud Run when code is pushed to `main` or `production` branches.

### Setup Instructions

#### 1. Create a Service Account

```bash
# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions CI/CD" \
    --project=$GCP_PROJECT_ID

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member="serviceAccount:github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"
```

#### 2. Create Service Account Key

```bash
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

**⚠️ Important**: Keep this key secure! Never commit it to the repository.

#### 3. Add GitHub Secrets

Go to your GitHub repository settings:
```
Settings → Secrets and variables → Actions → New repository secret
```

Add two secrets:

1. **GCP_PROJECT_ID**
   - Value: Your GCP project ID (e.g., `my-project-12345`)

2. **GCP_SA_KEY**
   - Value: Contents of `github-actions-key.json`
   - Open the file and copy the entire JSON content

#### 4. Delete the Local Key File

```bash
rm github-actions-key.json
```

Never leave service account keys on your local machine!

### Usage

#### Automatic Deployment

Push to main or production branch:
```bash
git push origin main
```

The workflow will automatically:
1. Build the container image
2. Push to Google Container Registry
3. Deploy to Cloud Run
4. Provide deployment summary

#### Manual Deployment

Trigger manually from GitHub:
```
Actions → Deploy to Google Cloud → Run workflow
```

### Workflow Triggers

The workflow runs on:
- **Push to `main` branch**: Deploys to staging/production
- **Push to `production` branch**: Deploys to production
- **Manual trigger**: Via GitHub Actions UI

### Viewing Deployment Status

1. Go to the **Actions** tab in your GitHub repository
2. Click on the latest workflow run
3. View deployment logs and summary

### Environment Variables

Configure in the workflow file or as secrets:
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `REGION`: Cloud Run region (default: us-central1)
- `SERVICE_NAME`: Cloud Run service name (default: video-automation)

### Security Best Practices

✅ **Do**:
- Use GitHub Secrets for credentials
- Rotate service account keys regularly
- Use least privilege permissions
- Enable branch protection rules
- Require code reviews before merge

❌ **Don't**:
- Commit service account keys to repository
- Use overly permissive IAM roles
- Store secrets in workflow files
- Deploy directly to production without testing

### Troubleshooting

#### "Permission denied" errors
- Verify service account has necessary roles
- Check if APIs are enabled in GCP

#### "Invalid credentials"
- Regenerate service account key
- Update GCP_SA_KEY secret in GitHub

#### "Service not found"
- Deploy manually first: `./deploy-gcp-all.sh`
- Verify service name matches

#### Build failures
- Check logs in Actions tab
- Verify Dockerfile syntax
- Test build locally: `docker build -t test .`

### Advanced Configuration

#### Deploy to Multiple Environments

Create separate workflows for staging and production:

**staging.yml**:
```yaml
on:
  push:
    branches: [develop]
env:
  SERVICE_NAME: video-automation-staging
```

**production.yml**:
```yaml
on:
  push:
    branches: [main]
env:
  SERVICE_NAME: video-automation-production
environment: production  # Requires approval
```

#### Add Tests Before Deploy

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: python -m pytest tests/

  deploy:
    needs: test  # Only deploy if tests pass
    # ... deployment steps
```

### Monitoring Deployments

View deployment history:
```
https://console.cloud.google.com/run/detail/us-central1/video-automation/revisions
```

View logs:
```bash
gcloud run services logs read video-automation --region=us-central1
```

### Cost Considerations

- GitHub Actions: 2,000 free minutes/month for private repos
- Cloud Build: 120 free build-minutes/day
- Cloud Run: Pay per use (scales to zero)

### Cleanup

To remove GitHub Actions service account:
```bash
gcloud iam service-accounts delete github-actions@$GCP_PROJECT_ID.iam.gserviceaccount.com
```

---

**Note**: This is optional. You can also deploy manually using `./deploy-gcp-all.sh` without setting up CI/CD.
