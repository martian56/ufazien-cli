"""
Project structure creation utilities.
"""

from pathlib import Path
from typing import Any, Dict, Optional


def create_config_file(project_dir: str, db_creds: Dict[str, Any]) -> None:
    """Create config.php file to load environment variables."""
    db_name = db_creds.get('name', '')
    config_content = f"""<?php
/**
 * Ufazien Configuration
 * Loads environment variables from .env file
 */

// Load environment variables from .env file
function loadEnv($path) {{
    if (!file_exists($path)) {{
        // .env file not found, use defaults or environment variables
        return;
    }}
    
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {{
        if (strpos(trim($line), '#') === 0) {{
            continue;
        }}
        
        if (strpos($line, '=') === false) {{
            continue;
        }}
        
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        
        if (!array_key_exists($name, $_ENV)) {{
            putenv("$name=$value");
            $_ENV[$name] = $value;
        }}
    }}
}}

// Load .env file - try multiple possible locations
$envPaths = [
    __DIR__ . '/.env',           // Same directory as config.php (root)
    dirname(__DIR__) . '/.env',  // Parent directory (if config.php is in subdirectory)
    getcwd() . '/.env',          // Current working directory
];

$envLoaded = false;
foreach ($envPaths as $envPath) {{
    if (file_exists($envPath)) {{
        loadEnv($envPath);
        $envLoaded = true;
        break;
    }}
}}

// Database configuration
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_USER', getenv('DB_USER') ?: 'root');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: '');
define('DB_NAME', getenv('DB_NAME') ?: '{db_name}');
define('DB_PORT', getenv('DB_PORT') ?: '3306');

// Create database connection
function getDBConnection() {{
    try {{
        $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        $conn = new PDO($dsn, DB_USER, DB_PASSWORD);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $conn->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $conn->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
        
        return $conn;
    }} catch (PDOException $e) {{
        die("Database connection error: " . $e->getMessage());
    }}
}}

// Alias for compatibility
function get_db_connection() {{
    return getDBConnection();
}}
"""

    config_path = Path(project_dir) / 'config.php'
    with open(config_path, 'w') as f:
        f.write(config_content)


def create_env_file(project_dir: str, db_creds: Dict[str, Any]) -> None:
    """Create .env file with database credentials."""
    env_content = f"""# Database Configuration
DB_HOST={db_creds['host']}
DB_PORT={db_creds['port']}
DB_NAME={db_creds['name']}
DB_USER={db_creds['username']}
DB_PASSWORD={db_creds['password']}
"""

    env_path = Path(project_dir) / '.env'
    with open(env_path, 'w') as f:
        f.write(env_content)


def create_gitignore(project_dir: str) -> None:
    """Create .gitignore file."""
    gitignore_content = """# Environment variables
.env
.ufazien.json

# Ufazien CLI
ufazien.py

# OS files
.DS_Store
Thumbs.db
desktop.ini

# IDE files
.vscode/
.idea/
*.swp
*.swo
*.sublime-project
*.sublime-workspace

# Temporary files
*.tmp
*.log
*.cache

# Build files
dist/
build/
*.min.js
*.min.css
"""

    gitignore_path = Path(project_dir) / '.gitignore'
    if not gitignore_path.exists():
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content)
    else:
        with open(gitignore_path, 'r') as f:
            content = f.read()

        additions = []
        if '.env' not in content:
            additions.append('# Environment variables\n.env')
        if '.ufazien.json' not in content:
            additions.append('.ufazien.json')
        if 'ufazien.py' not in content:
            additions.append('# Ufazien CLI\nufazien.py')

        if additions:
            with open(gitignore_path, 'a') as f:
                f.write('\n' + '\n'.join(additions) + '\n')


def create_readme_section(project_dir: str, website_type: str, website_name: str, build_folder: Optional[str] = None) -> None:
    """Create or append README.md with Ufazien deployment section."""
    project_path = Path(project_dir)
    readme_path = project_path / 'README.md'
    
    if website_type == 'build':
        # For build projects, use the existing create_build_project_structure logic
        if not readme_path.exists():
            readme_content = f"""# {website_name}

This project is configured for deployment to Ufazien Hosting.

## Build and Deploy

1. Build your project (this will create a `dist` or `build` folder):
```bash
npm run build
# or
yarn build
# or
pnpm build
```

2. Deploy to Ufazien:
```bash
ufazien deploy
```

The deployment will automatically upload the contents of your build folder.
"""
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
        else:
            # Append Ufazien deployment section to existing README
            with open(readme_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            if 'Ufazien Hosting' not in existing_content:
                ufazien_section = f"""

---

## Ufazien Deployment

This project is configured for deployment to Ufazien Hosting.

### Build and Deploy

1. Build your project (this will create a `dist` or `build` folder):
```bash
npm run build
# or
yarn build
# or
pnpm build
```

2. Deploy to Ufazien:
```bash
ufazien deploy
```

The deployment will automatically upload the contents of your build folder.
"""
                with open(readme_path, 'a', encoding='utf-8') as f:
                    f.write(ufazien_section)
    else:
        # For PHP and Static projects, append a simple deployment section
        if not readme_path.exists():
            readme_content = f"""# {website_name}

This project is configured for deployment to Ufazien Hosting.

## Deploy

Deploy your website to Ufazien:

```bash
ufazien deploy
```

Your website will be available at your configured subdomain.
"""
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
        else:
            # Append Ufazien deployment section to existing README
            with open(readme_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            if 'Ufazien Hosting' not in existing_content:
                ufazien_section = f"""

---

## Ufazien Deployment

This project is configured for deployment to Ufazien Hosting.

### Deploy

Deploy your website to Ufazien:

```bash
ufazien deploy
```

Your website will be available at your configured subdomain.
"""
                with open(readme_path, 'a', encoding='utf-8') as f:
                    f.write(ufazien_section)


def create_ufazienignore(project_dir: str) -> None:
    """Create .ufazienignore file."""
    ufazienignore_content = """# Files and directories to exclude from deployment
.git/
.gitignore
.ufazien.json
ufazien.py
*.log
*.tmp
.DS_Store
Thumbs.db
desktop.ini
.vscode/
.idea/
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
ENV/

# For build projects (Vite/React/etc.):
# Uncomment the line below and add your source folders to deploy only the build output
# src/
# public/
# package.json
# package-lock.json
# yarn.lock
# pnpm-lock.yaml
# tsconfig.json
# vite.config.js
# vite.config.ts
"""

    ufazienignore_path = Path(project_dir) / '.ufazienignore'
    with open(ufazienignore_path, 'w') as f:
        f.write(ufazienignore_content)


def create_php_project_structure(project_dir: str, website_name: str, has_database: bool = False) -> None:
    """Create PHP project structure with boilerplate code."""
    project_path = Path(project_dir)

    # Create src directory
    src_dir = project_path / 'src'
    src_dir.mkdir(exist_ok=True)

    # Create root index.php
    if has_database:
        index_php_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{website_name}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to {website_name}</h1>
        </header>
        
        <main>
            <?php
            // Load configuration (for database connection)
            require_once __DIR__ . '/config.php';
            
            // Include main application logic
            require_once __DIR__ . '/src/index.php';
            ?>
        </main>
        
        <footer>
            <p>&copy; <?php echo date('Y'); ?> {website_name}. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
"""
    else:
        index_php_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{website_name}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to {website_name}</h1>
        </header>
        
        <main>
            <?php
            // Include main application logic
            require_once __DIR__ . '/src/index.php';
            ?>
        </main>
        
        <footer>
            <p>&copy; <?php echo date('Y'); ?> {website_name}. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
"""

    index_path = project_path / 'index.php'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_php_content)

    # Create src/index.php
    if has_database:
        src_index_content = """<?php
/**
 * Main application entry point
 */

// Load database connection
require_once __DIR__ . '/../database.php';

// Your application logic here
echo '<section class="content">';
echo '<h2>Hello, World!</h2>';
echo '<p>Your PHP application is running successfully.</p>';

// Check database connection status
$conn = get_connection();
if ($conn) {
    echo '<div class="db-status db-success">';
    echo '<h3>[OK] Database Connection: Active</h3>';
    echo '<p>Your database is connected and ready to use.</p>';
    echo '</div>';
} else {
    echo '<div class="db-status db-error">';
    echo '<h3>[ERROR] Database Connection: Failed</h3>';
    echo '<p>Please check your database configuration in <code>.env</code> and <code>config.php</code>.</p>';
    echo '</div>';
}

echo '<p>Edit <code>src/index.php</code> to customize this page.</p>';
echo '</section>';
?>
"""
    else:
        src_index_content = """<?php
/**
 * Main application entry point
 */

// Your application logic here
echo '<section class="content">';
echo '<h2>Hello, World!</h2>';
echo '<p>Your PHP application is running successfully.</p>';
echo '<p>Edit <code>src/index.php</code> to customize this page.</p>';
echo '</section>';
?>
"""

    src_index_path = src_dir / 'index.php'
    with open(src_index_path, 'w', encoding='utf-8') as f:
        f.write(src_index_content)

    # Create src/css directory and style.css
    css_dir = src_dir / 'css'
    css_dir.mkdir(exist_ok=True)

    css_content = """/* Main Stylesheet */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

main {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin-bottom: 2rem;
}

.content h2 {
    color: #667eea;
    margin-bottom: 1rem;
}

.content p {
    margin-bottom: 1rem;
}

.content code {
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

footer {
    text-align: center;
    color: #666;
    padding: 1rem;
}
"""

    css_path = css_dir / 'style.css'
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

    # Create src/js directory and main.js
    js_dir = src_dir / 'js'
    js_dir.mkdir(exist_ok=True)

    js_content = """// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application loaded successfully!');
    
    // Your JavaScript code here
});
"""

    js_path = js_dir / 'main.js'
    with open(js_path, 'w', encoding='utf-8') as f:
        f.write(js_content)

    # Create database.php if database is available
    if has_database:
        database_php_content = """<?php
/**
 * Database Configuration and Setup
 * 
 * This file handles database connection and initial table creation.
 * Edit this file to add more tables as needed.
 */

// Load configuration
require_once __DIR__ . '/config.php';

// Global database connection variable
$conn = null;

/**
 * Get database connection
 * @return PDO|null Database connection or null on failure
 */
function get_connection() {
    global $conn;
    
    if ($conn !== null) {
        return $conn;
    }
    
    try {
        $conn = getDBConnection();
        return $conn;
    } catch (Exception $e) {
        error_log("Database connection error: " . $e->getMessage());
        return null;
    }
}

// Make connection available globally
$conn = get_connection();
?>
"""

        database_path = project_path / 'database.php'
        with open(database_path, 'w', encoding='utf-8') as f:
            f.write(database_php_content)


def create_static_project_structure(project_dir: str, website_name: str) -> None:
    """Create static website project structure with boilerplate code."""
    project_path = Path(project_dir)

    # Create src directory
    src_dir = project_path / 'src'
    src_dir.mkdir(exist_ok=True)

    # Create css directory
    css_dir = src_dir / 'css'
    css_dir.mkdir(exist_ok=True)

    # Create js directory
    js_dir = src_dir / 'js'
    js_dir.mkdir(exist_ok=True)

    # Create root index.html
    index_html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{website_name} - A modern web application">
    <title>{website_name}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to {website_name}</h1>
            <nav>
                <ul>
                    <li><a href="#home">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </header>
        
        <main>
            <section id="home" class="content">
                <h2>Hello, World!</h2>
                <p>Your static website is running successfully.</p>
                <p>Edit <code>index.html</code> and files in the <code>src/</code> directory to customize your website.</p>
            </section>
            
            <section id="about" class="content">
                <h2>About</h2>
                <p>This is a boilerplate static website. Customize it to your needs!</p>
            </section>
            
            <section id="contact" class="content">
                <h2>Contact</h2>
                <p>Get in touch with us!</p>
            </section>
        </main>
        
        <footer>
            <p>&copy; <span id="year"></span> {website_name}. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
"""

    index_path = project_path / 'index.html'
    with open(index_path, 'w') as f:
        f.write(index_html_content)

    # Create src/css/style.css
    css_content = """/* Main Stylesheet */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
    text-align: center;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

nav ul {
    list-style: none;
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
}

nav a {
    color: white;
    text-decoration: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    transition: background-color 0.3s;
}

nav a:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

main {
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.content {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.content h2 {
    color: #667eea;
    margin-bottom: 1rem;
}

.content p {
    margin-bottom: 1rem;
}

.content code {
    background: #f4f4f4;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
}

footer {
    text-align: center;
    color: #666;
    padding: 1rem;
    margin-top: 2rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    header h1 {
        font-size: 2rem;
    }
    
    nav ul {
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .container {
        padding: 10px;
    }
}
"""

    css_path = css_dir / 'style.css'
    with open(css_path, 'w') as f:
        f.write(css_content)

    # Create src/js/main.js
    js_content = """// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Website loaded successfully!');
    
    // Set current year in footer
    const yearElement = document.getElementById('year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
    
    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Your JavaScript code here
});
"""

    js_path = js_dir / 'main.js'
    with open(js_path, 'w') as f:
        f.write(js_content)


def create_build_project_structure(project_dir: str, website_name: str) -> None:
    """Create build project structure for Vite/React/etc. projects."""
    project_path = Path(project_dir)

    # Create README with instructions
    readme_content = f"""# {website_name}

This project is configured for deployment to Ufazien Hosting.

## Build and Deploy

1. Build your project (this will create a `dist` or `build` folder):
```bash
npm run build
# or
yarn build
# or
pnpm build
```

2. Deploy to Ufazien:
```bash
ufazien deploy
```

The deployment will automatically upload the contents of your build folder.

## Project Structure

```
{project_path.name}/
├── dist/          # Your build output (Vite default)
├── build/         # Your build output (React/Create React App default)
├── .ufazien.json  # Ufazien configuration (auto-generated)
└── README.md       # This file
```

## Notes

- Make sure your build output includes an `index.html` file
- The build folder contents will be deployed automatically
"""
    
    readme_path = project_path / 'README.md'
    if not readme_path.exists():
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
    else:
        # Append Ufazien deployment section to existing README
        with open(readme_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Check if Ufazien section already exists
        if 'Ufazien Hosting' not in existing_content:
            ufazien_section = f"""

---

## Ufazien Deployment

This project is configured for deployment to Ufazien Hosting.

### Build and Deploy

1. Build your project (this will create a `dist` or `build` folder):
```bash
npm run build
# or
yarn build
# or
pnpm build
```

2. Deploy to Ufazien:
```bash
ufazien deploy
```

The deployment will automatically upload the contents of your build folder.
"""
            with open(readme_path, 'a', encoding='utf-8') as f:
                f.write(ufazien_section)

