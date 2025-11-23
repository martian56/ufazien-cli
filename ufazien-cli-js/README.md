# Ufazien CLI (JavaScript/TypeScript)

🚀 A Command-line interface for deploying web applications on the Ufazien platform.

## Features

- ✨ Beautiful terminal UI with colors and prompts
- 🎯 Modern CLI framework using Commander.js
- 🔐 Secure authentication with token management
- 📦 Easy project creation and deployment
- 🗄️ Database provisioning support
- 📝 Automatic project structure generation
- 📦 Built with TypeScript

## Installation

### From npm

```bash
npm install -g ufazien-cli
```

After installation, use the `ufazienjs` command.

### From Source

```bash
# Clone the repository
git clone https://github.com/martian56/ufazien-cli.git
cd ufazien-cli-js
npm install
```

## Usage

### Login

Authenticate with your Ufazien account:

```bash
ufazienjs login
```

You'll be prompted for your email and password.

### Create a New Website

Create a new website project in the current directory:

```bash
ufazienjs create
```

The CLI will guide you through:
- Website name and subdomain
- Website type (Static or PHP)
- Database creation (for PHP projects)
- Project structure generation

### Deploy Your Website

Deploy your website to Ufazien:

```bash
ufazienjs deploy
```

This will:
1. Create a ZIP archive of your project (excluding files in `.ufazienignore`)
2. Upload the files to your website
3. Trigger the deployment

### Check Status

Check your login status and profile:

```bash
ufazienjs status
```

### Logout

Logout from your account:

```bash
ufazienjs logout
```

## Commands

| Command | Description |
|---------|-------------|
| `ufazienjs login` | Login to your Ufazien account |
| `ufazienjs logout` | Logout from your account |
| `ufazienjs create` | Create a new website project |
| `ufazienjs deploy` | Deploy your website |
| `ufazienjs status` | Check login status and profile |

