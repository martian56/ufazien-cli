<h1 align="center">Ufazien CLI</h1>

<p align="center">
  Deploy static sites, PHP apps, and build-output projects to the <a href="https://ufazien.com">Ufazien</a> platform from your terminal — in either Python or Node.
</p>

<p align="center">
  <a href="https://pypi.org/project/ufazien-cli/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/ufazien-cli?label=pypi&logo=pypi&logoColor=white&color=3775A9"></a>
  <a href="https://www.npmjs.com/package/ufazien-cli"><img alt="npm version" src="https://img.shields.io/npm/v/ufazien-cli?label=npm&logo=npm&logoColor=white&color=CB3837"></a>
  <a href="https://pypi.org/project/ufazien-cli/"><img alt="PyPI downloads" src="https://img.shields.io/pypi/dm/ufazien-cli?label=pypi%20downloads&color=3775A9"></a>
  <a href="https://www.npmjs.com/package/ufazien-cli"><img alt="npm downloads" src="https://img.shields.io/npm/dm/ufazien-cli?label=npm%20downloads&color=CB3837"></a>
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
  <a href="https://github.com/martian56/ufazien-cli/stargazers"><img alt="GitHub stars" src="https://img.shields.io/github/stars/martian56/ufazien-cli?style=flat&logo=github"></a>
  <a href="https://github.com/martian56/ufazien-cli/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/martian56/ufazien-cli/test_npm_package.yml?label=npm%20tests&logo=github"></a>
  <a href="https://github.com/martian56/ufazien-cli/actions"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/martian56/ufazien-cli/test_python_pkg.yml?label=python%20tests&logo=github"></a>
</p>

---

## Overview

This repository ships two officially-supported CLIs that talk to the same Ufazien deployment API:

| Package | Install | Command | Registry |
| ------- | ------- | ------- | -------- |
| `ufazien-cli` (Python) | `pip install ufazien-cli` | `ufazien` | [PyPI](https://pypi.org/project/ufazien-cli/) |
| `ufazien-cli` (Node)   | `npm install -g ufazien-cli` | `ufazienjs` | [npm](https://www.npmjs.com/package/ufazien-cli) |

Pick the one that fits your stack — both expose the same commands and behaviour.

---

## Quick start

```bash
# 1. install (pick one)
pip install ufazien-cli       # → `ufazien`
npm install -g ufazien-cli    # → `ufazienjs`

# 2. authenticate
ufazien login                 # or: ufazienjs login

# 3. scaffold a project in the current directory
ufazien create                # or: ufazienjs create

# 4. ship it
ufazien deploy                # or: ufazienjs deploy
```

`create` walks you through the website name, subdomain, project type (`static`, `php`, or `build`), and — for PHP projects — provisions a database. `deploy` zips your project (respecting `.ufazienignore`) and uploads it to your site.

---

## Project types

| Type | What it deploys | Typical use |
| ---- | --------------- | ----------- |
| **static** | The project root, minus paths in `.ufazienignore`. | Plain HTML/CSS/JS sites. |
| **php**    | The project root, minus paths in `.ufazienignore`, plus an `.env` if you provisioned a database. | PHP apps (with optional managed MySQL). |
| **build**  | The contents of your configured build folder (e.g. `dist/`, `build/`). | Vite, React, Vue, Svelte, and other framework builds. |

### `.ufazienignore`

A gitignore-style exclude list for the deploy zip. Generated automatically for `static` and `php` projects. Supports:

- `dir/` — exclude a directory anywhere in the tree
- `*.ext` — exclude files by extension
- `name` or `path/to/file` — exclude by basename or relative path

---

## Commands

| Command | Description |
| ------- | ----------- |
| `login`  | Authenticate against the Ufazien API and persist a session token. |
| `logout` | Clear the local session. |
| `status` | Show the signed-in account and current session info. |
| `create` | Interactively scaffold a new website project + register it on Ufazien. |
| `deploy` | Package the current project and push it to your site. |

Run `--help` on any command for flags.

---

## Local development

```bash
git clone https://github.com/martian56/ufazien-cli.git
cd ufazien-cli
```

**Python package** (`ufazien-cli-py/`):

```bash
cd ufazien-cli-py
python -m venv venv && source venv/bin/activate   # (Windows: venv\Scripts\activate)
pip install -e ".[dev]"
ufazien --help
```

**Node package** (`ufazien-cli-js/`):

```bash
cd ufazien-cli-js
npm install
npm run build
node dist/cli.js --help
# or, for live reload during development:
npm run dev -- --help
```

Each package has its own README with package-specific details.

---

## Built with

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Typer](https://img.shields.io/badge/Typer-009485?style=for-the-badge&logo=typer&logoColor=white)](https://typer.tiangolo.com/)
[![Rich](https://img.shields.io/badge/Rich-FAE742?style=for-the-badge&logo=python&logoColor=black)](https://github.com/Textualize/rich)
[![Requests](https://img.shields.io/badge/Requests-005571?style=for-the-badge&logo=python&logoColor=white)](https://requests.readthedocs.io/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Node.js](https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=node.js&logoColor=white)](https://nodejs.org/)
[![Commander](https://img.shields.io/badge/Commander.js-1F425F?style=for-the-badge&logo=node.js&logoColor=white)](https://github.com/tj/commander.js)
[![Inquirer](https://img.shields.io/badge/Inquirer-3B82F6?style=for-the-badge&logo=node.js&logoColor=white)](https://github.com/SBoudrias/Inquirer.js)
[![Chalk](https://img.shields.io/badge/Chalk-2E2E2E?style=for-the-badge&logo=npm&logoColor=white)](https://github.com/chalk/chalk)
[![Axios](https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white)](https://axios-http.com/)

---

## Contributing

Issues and pull requests are welcome. If you're filing a bug, please include:

- which package you're using (`ufazien-cli` Python or Node) and its version
- the command you ran and the output you got
- your OS

For larger changes, open an issue first to discuss the approach.

---

## Repo activity

<!--
  Generate the embed URL at https://repobeats.axiom.co (sign in with GitHub,
  pick this repo, copy the SVG embed URL) and replace the placeholder below.
-->
![Alt](https://repobeats.axiom.co/api/embed/f0acaf6fbb77570c1c638b0389de620c9da92da9.svg "Repobeats analytics image")

## Contributors

<a href="https://github.com/martian56/ufazien-cli/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=martian56/ufazien-cli" alt="Contributors"/>
</a>

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=martian56/ufazien-cli&type=Date)](https://www.star-history.com/#martian56/ufazien-cli&Date)

---

## Links

- Homepage — [ufazien.com](https://ufazien.com)
- Documentation — [howtohoston.ufazien.com](https://howtohoston.ufazien.com)
- PyPI — [pypi.org/project/ufazien-cli](https://pypi.org/project/ufazien-cli/)
- npm — [npmjs.com/package/ufazien-cli](https://www.npmjs.com/package/ufazien-cli)
- Issues — [github.com/martian56/ufazien-cli/issues](https://github.com/martian56/ufazien-cli/issues)

## License

Released under the MIT License.
