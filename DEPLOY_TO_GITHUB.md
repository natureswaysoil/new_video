# Deploy to GitHub: natureswaysoil/new_video

## Method 1: Automated Script (Easiest)

```bash
# Make script executable
chmod +x deploy_to_github.sh

# Run the deployment script
./deploy_to_github.sh
```

The script will:
- Clone your repository (if it exists)
- Copy all files
- Commit and push changes

---

## Method 2: Manual Deployment

### Step 1: Make sure repository exists on GitHub

Go to: https://github.com/natureswaysoil/new_video

If it doesn't exist:
1. Go to https://github.com/new
2. Repository name: `new_video`
3. Make it Private (recommended) or Public
4. DON'T initialize with README (we already have one)
5. Click "Create repository"

### Step 2: Clone the repository

```bash
# Navigate to where you want to work
cd ~

# Clone your repository
git clone https://github.com/natureswaysoil/new_video.git
cd new_video
```

### Step 3: Copy the files

```bash
# Copy all files from outputs directory
cp /mnt/user-data/outputs/*.py .
cp /mnt/user-data/outputs/*.md .
cp /mnt/user-data/outputs/*.txt .
cp /mnt/user-data/outputs/.env.example .
cp /mnt/user-data/outputs/.gitignore .
cp /mnt/user-data/outputs/Dockerfile .
cp /mnt/user-data/outputs/docker-compose.yml .
cp /mnt/user-data/outputs/video-automation.service .

# Create directories
mkdir -p videos logs
```

### Step 4: Commit and push

```bash
# Check what will be committed
git status

# Add all files
git add .

# Commit
git commit -m "Add video automation system

- Complete automation for YouTube, Instagram, Pinterest, Twitter
- OpenAI script generation
- HeyGen video creation
- Google Sheets integration
- Comprehensive documentation
- Docker support"

# Push to GitHub
git push origin main
# If that fails, try: git push origin master
```

### Step 5: Verify

Visit: https://github.com/natureswaysoil/new_video

You should see all your files!

---

## Method 3: Using GitHub Desktop (Windows/Mac)

1. Download GitHub Desktop: https://desktop.github.com/
2. Clone repository: `File` → `Clone Repository` → `natureswaysoil/new_video`
3. Copy all files from the outputs folder to the cloned directory
4. In GitHub Desktop:
   - Check all files
   - Enter commit message: "Add video automation system"
   - Click "Commit to main"
   - Click "Push origin"

---

## Method 4: Using GitHub CLI

```bash
# Install GitHub CLI (if not installed)
# See: https://cli.github.com/

# Authenticate
gh auth login

# Create repo if it doesn't exist
gh repo create natureswaysoil/new_video --private

# Clone and navigate
gh repo clone natureswaysoil/new_video
cd new_video

# Copy files
cp /mnt/user-data/outputs/*.{py,md,txt} .
cp /mnt/user-data/outputs/.* .
cp /mnt/user-data/outputs/Dockerfile .
cp /mnt/user-data/outputs/docker-compose.yml .
cp /mnt/user-data/outputs/video-automation.service .

# Commit and push
git add .
git commit -m "Add video automation system"
git push origin main
```

---

## Troubleshooting

### "Repository not found"

The repository might not exist yet:
1. Go to https://github.com/new
2. Create repository named `new_video`
3. Try again

### "Authentication failed"

You need a Personal Access Token:
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`
4. Generate and copy token
5. Use token as password when pushing

### "Permission denied"

Make sure you have write access to `natureswaysoil/new_video`:
- You must be the owner, or
- Be added as a collaborator

### "Main branch doesn't exist"

Some repos use `master` instead of `main`:
```bash
git push origin master
```

Or rename your branch:
```bash
git branch -M main
git push -u origin main
```

---

## Verification Checklist

After pushing, verify these files are on GitHub:

Core Files:
- [ ] video_automation.py
- [ ] scheduler.py
- [ ] test_setup.py
- [ ] setup_secrets.py
- [ ] requirements.txt

Documentation:
- [ ] README.md
- [ ] QUICKSTART.md
- [ ] OVERVIEW.md
- [ ] CUSTOMIZATION.md
- [ ] TROUBLESHOOTING.md

Configuration:
- [ ] .env.example
- [ ] .gitignore
- [ ] Dockerfile
- [ ] docker-compose.yml
- [ ] video-automation.service

---

## Next Steps After Pushing

### On Your Production Server:

```bash
# Clone the repository
git clone https://github.com/natureswaysoil/new_video.git
cd new_video

# Install dependencies
pip install -r requirements.txt

# Set up environment
export GCP_PROJECT_ID="your-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Set up credentials
python setup_secrets.py

# Test setup
python test_setup.py

# Run first automation
python video_automation.py
```

### Keep Your Repo Updated

When you make changes locally:

```bash
cd new_video
git add .
git commit -m "Description of changes"
git push origin main
```

Pull updates on production server:

```bash
cd new_video
git pull origin main
# Restart services if running
```

---

## Security Reminders

✅ **DO commit:**
- All .py files
- Documentation
- Configuration templates (.env.example)
- Dockerfile and docker-compose.yml

❌ **DON'T commit:**
- Actual API keys or secrets
- Service account JSON files
- .env file (with real values)
- automation_state.json (has your data)
- Log files
- Video files

The `.gitignore` file prevents these from being committed accidentally.

---

## Repository Structure on GitHub

```
natureswaysoil/new_video/
├── video_automation.py
├── scheduler.py
├── test_setup.py
├── setup_secrets.py
├── requirements.txt
├── README.md
├── QUICKSTART.md
├── OVERVIEW.md
├── CUSTOMIZATION.md
├── TROUBLESHOOTING.md
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── video-automation.service
└── (GitHub will add: LICENSE, .github/, etc.)
```

---

Need help? Check TROUBLESHOOTING.md or create an issue on GitHub!
