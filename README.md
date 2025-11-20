# Ufazien CLI

Command-line interface for working with the Ufazien hosting platform. This Python script allows you to login to your account, create website projects (static or PHP), provision databases, and deploy your files.

---

## Requirements ✅
- Python 3.6+
- Internet access
- And a cool project idea :)

---

## Setup / Install
1. Clone or download this repository.
2. Open a terminal and change to the repository folder.

Example (PowerShell):
```powershell
cd ~\websites\ufazien-cli
python -V # verify Python 3 is available
```

The CLI is a single file: `ufazien.py`. You can run it directly with Python.

---

## Quickstart / Common workflows 🚀

1. Login

```powershell
python ufazien.py login
```

You will be prompted for an email and password.

2. Create a website

Change into the project directory where you want your website files to live (the CLI will create helpful templates and files in the current directory):

```powershell
cd c:\path\to\my-project
python \path\to\ufazien-cli\ufazien.py create
```

You will be prompted for:
- Website name
- Subdomain
- Website type: static (HTML/CSS/JS) or PHP
- If you choose PHP, the CLI asks whether you want a database and, if so, it will provision one.

The `create` command will:
- Create a website and optionally a database
- Create a project boilerplate 
- Create `.gitignore` and `.ufazienignore`
- Save `.ufazien.json` with the website metadata

Once created, you can add your files and then deploy.

3. Deploy website

From the same project directory (with `.ufazien.json` created by `create`):

```powershell
python \path\to\ufazien-cli\ufazien.py deploy
```

This will:
- Create a ZIP archive of the current project, excluding the files in `.ufazienignore`
- Upload the ZIP to your Ufazien site
- Trigger a deployment via the API

4. Logout

```powershell
python ufazien.py logout
```

