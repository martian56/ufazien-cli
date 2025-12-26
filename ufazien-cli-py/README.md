# Ufazien CLI

🚀 A Command-line interface for deploying web applications on the Ufazien platform.

## Features

- ✨ Beautiful terminal UI powered by [Rich](https://github.com/Textualize/rich)
- 🎯 Modern CLI framework using [Typer](https://github.com/tiangolo/typer)
- 🔐 Secure authentication with token management
- 📦 Easy project creation and deployment
- 🗄️ Database provisioning support
- 📝 Automatic project structure generation

## Installation

### From Source

```bash
git clone https://github.com/martian56/ufazien-cli.git
cd ufazien-cli-py

# Install in development mode
pip install -e .

# Or install in production mode
pip install .
```

### From PyPI

```bash
pip install ufazien-cli
```

## Usage

### Login

Authenticate with your Ufazien account:

```bash
ufazien login
```

You'll be prompted for your email and password.

### Create a New Website

Create a new website project in the current directory:

```bash
ufazien create
```

The CLI will guide you through:
- Website name and subdomain
- Website type (Static, PHP, or Build)
- Database creation (for PHP projects)
- Build folder name (for Build projects)
- Project structure generation

### Deploy Your Website

Deploy your website to Ufazien:

```bash
ufazien deploy
```

This will:
1. Create a ZIP archive of your project (excluding files in `.ufazienignore`, or from build folder for Build projects)
2. Upload the files to your website
3. Trigger the deployment

### Check Status

Check your login status and profile:

```bash
ufazien status
```

### Logout

Logout from your account:

```bash
ufazien logout
```

## Commands

| Command | Description |
|---------|-------------|
| `login` | Login to your Ufazien account |
| `logout` | Logout from your account |
| `create` | Create a new website project |
| `deploy` | Deploy your website |
| `status` | Check login status and profile |

