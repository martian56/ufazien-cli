# Ufazien CLI

🚀 Command-line interface for deploying web applications on the Ufazien platform.

This repository contains **two official CLI packages** for the Ufazien platform:

- **Python Package** (`ufazien-cli-py`) - Install via PyPI
- **JavaScript/TypeScript Package** (`ufazien-cli-js`) - Install via npm

Both packages provide the same functionality
---

## 📦 Installation

### Python Package (Recommended for Python users)

```bash
pip install ufazien-cli
```

After installation, use the `ufazien` command:

```bash
ufazien --help
```

**Features:**
- ✨ Beautiful terminal UI powered by [Rich](https://github.com/Textualize/rich)
- 🎯 Modern CLI framework using [Typer](https://github.com/tiangolo/typer)
- 📦 Available on [PyPI](https://pypi.org/project/ufazien-cli/)

### JavaScript/TypeScript Package (Recommended for Node.js users)

```bash
npm install -g ufazien-cli
```

After installation, use the `ufazienjs` command:

```bash
ufazienjs --help
```

**Features:**
- ✨ Beautiful terminal UI with colors and prompts
- 🎯 Modern CLI framework using Commander.js
- 📦 Available on [npm](https://www.npmjs.com/package/ufazien-cli)
- 🔷 Built with TypeScript

---

## 🚀 Quick Start

### 1. Login

**Python:**
```bash
ufazien login
```

**JavaScript:**
```bash
ufazienjs login
```

You'll be prompted for your email and password

### 2. Create a Website

Navigate to your project directory and run:

**Python:**
```bash
ufazien create
```

**JavaScript:**
```bash
ufazienjs create
```

The CLI will guide you through:
- Website name and subdomain
- Website type (Static or PHP)
- Database creation (for PHP projects)
- Project structure generation

### 3. Deploy Your Website

From your project directory:

**Python:**
```bash
ufazien deploy
```

**JavaScript:**
```bash
ufazienjs deploy
```

This will:
1. Create a ZIP archive (excluding files in `.ufazienignore`)
2. Upload files to your website
3. Trigger deployment

### 4. Check Status

**Python:**
```bash
ufazien status
```

**JavaScript:**
```bash
ufazienjs status
```

### 5. Logout

**Python:**
```bash
ufazien logout
```

**JavaScript:**
```bash
ufazienjs logout
```

---

## 📋 Available Commands

| Command | Description |
|---------|-------------|
| `login` | Login to your Ufazien account |
| `logout` | Logout from your account |
| `create` | Create a new website project |
| `deploy` | Deploy your website |
| `status` | Check login status and profile |

---

## 🆘 Support

For issues and questions:
- **GitHub Issues**: [https://github.com/martian56/ufazien-cli/issues](https://github.com/martian56/ufazien-cli/issues)
- **Ufazien Support**: [https://ufazien.com/support](https://ufazien.com/support)

---

## 📄 License

MIT License

---

## 🔗 Links

- **Homepage**: [https://ufazien.com](https://ufazien.com)
- **Python Package**: [https://pypi.org/project/ufazien-cli/](https://pypi.org/project/ufazien-cli/)
- **npm Package**: [https://www.npmjs.com/package/ufazien-cli](https://www.npmjs.com/package/ufazien-cli)
- **Repository**: [https://github.com/martian56/ufazien-cli](https://github.com/martian56/ufazien-cli)
