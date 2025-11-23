# Ufazien CLI

🚀 A beautiful command-line interface for deploying web applications on the Ufazien platform.

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
# Clone the repository
git clone <repository-url>
cd ufazien-cli-py

# Install in development mode
pip install -e .

# Or install in production mode
pip install .
```

### From PyPI (Coming Soon)

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
- Website type (Static or PHP)
- Database creation (for PHP projects)
- Project structure generation

### Deploy Your Website

Deploy your website to Ufazien:

```bash
ufazien deploy
```

This will:
1. Create a ZIP archive of your project (excluding files in `.ufazienignore`)
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

## Project Structure

When you create a new website, the CLI generates a project structure:

### PHP Projects

```
.
├── index.php
├── config.php
├── database.php (if database is created)
├── .env (if database is created)
├── .gitignore
├── .ufazienignore
├── .ufazien.json
└── src/
    ├── index.php
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

### Static Projects

```
.
├── index.html
├── .gitignore
├── .ufazienignore
├── .ufazien.json
└── src/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Configuration

The CLI stores configuration and tokens in `~/.ufazien/`:
- `tokens.json` - Authentication tokens (encrypted)
- `config.json` - CLI configuration

Project-specific configuration is stored in `.ufazien.json` in your project directory.

## Excluding Files from Deployment

Create a `.ufazienignore` file in your project root to exclude files and directories from deployment. The format is similar to `.gitignore`:

```
.git/
node_modules/
*.log
.env
```

## Requirements

- Python 3.8+
- Ufazien account

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/
ruff check src/
```

## License

MIT License

## Support

For issues and questions, please visit [Ufazien Support](https://ufazien.com/support).

