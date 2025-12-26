/**
 * Project structure creation utilities.
 */

import fs from 'fs-extra';
import path from 'path';

export interface DatabaseCredentials {
  name: string;
  host: string;
  port: number;
  username: string;
  password: string;
}

export function createConfigFile(projectDir: string, dbCreds: DatabaseCredentials): void {
  const dbName = dbCreds.name || '';
  const configContent = `<?php
/**
 * Ufazien Configuration
 * Loads environment variables from .env file
 */

// Load environment variables from .env file
function loadEnv($path) {
    if (!file_exists($path)) {
        // .env file not found, use defaults or environment variables
        return;
    }
    
    $lines = file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos(trim($line), '#') === 0) {
            continue;
        }
        
        if (strpos($line, '=') === false) {
            continue;
        }
        
        list($name, $value) = explode('=', $line, 2);
        $name = trim($name);
        $value = trim($value);
        
        if (!array_key_exists($name, $_ENV)) {
            putenv("$name=$value");
            $_ENV[$name] = $value;
        }
    }
}

// Load .env file - try multiple possible locations
$envPaths = [
    __DIR__ . '/.env',           // Same directory as config.php (root)
    dirname(__DIR__) . '/.env',  // Parent directory (if config.php is in subdirectory)
    getcwd() . '/.env',          // Current working directory
];

$envLoaded = false;
foreach ($envPaths as $envPath) {
    if (file_exists($envPath)) {
        loadEnv($envPath);
        $envLoaded = true;
        break;
    }
}

// Database configuration
define('DB_HOST', getenv('DB_HOST') ?: 'localhost');
define('DB_USER', getenv('DB_USER') ?: 'root');
define('DB_PASSWORD', getenv('DB_PASSWORD') ?: '');
define('DB_NAME', getenv('DB_NAME') ?: '${dbName}');
define('DB_PORT', getenv('DB_PORT') ?: '3306');

// Create database connection
function getDBConnection() {
    try {
        $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=utf8mb4";
        $conn = new PDO($dsn, DB_USER, DB_PASSWORD);
        $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $conn->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        $conn->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
        
        return $conn;
    } catch (PDOException $e) {
        die("Database connection error: " . $e->getMessage());
    }
}

// Alias for compatibility
function get_db_connection() {
    return getDBConnection();
}
`;

  const configPath = path.join(projectDir, 'config.php');
  fs.writeFileSync(configPath, configContent);
}

export function createEnvFile(projectDir: string, dbCreds: DatabaseCredentials): void {
  const envContent = `# Database Configuration
DB_HOST=${dbCreds.host}
DB_PORT=${dbCreds.port}
DB_NAME=${dbCreds.name}
DB_USER=${dbCreds.username}
DB_PASSWORD=${dbCreds.password}
`;

  const envPath = path.join(projectDir, '.env');
  fs.writeFileSync(envPath, envContent);
}

export function createGitignore(projectDir: string): void {
  const gitignoreContent = `# Environment variables
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
`;

  const gitignorePath = path.join(projectDir, '.gitignore');
  if (!fs.existsSync(gitignorePath)) {
    fs.writeFileSync(gitignorePath, gitignoreContent);
  } else {
    const content = fs.readFileSync(gitignorePath, 'utf-8');
    const additions: string[] = [];
    if (!content.includes('.env')) {
      additions.push('# Environment variables\n.env');
    }
    if (!content.includes('.ufazien.json')) {
      additions.push('.ufazien.json');
    }
    if (!content.includes('ufazien.py')) {
      additions.push('# Ufazien CLI\nufazien.py');
    }
    if (additions.length > 0) {
      fs.appendFileSync(gitignorePath, '\n' + additions.join('\n') + '\n');
    }
  }
}

export function createUfazienignore(projectDir: string): void {
  const ufazienignoreContent = `# Files and directories to exclude from deployment
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
`;

  const ufazienignorePath = path.join(projectDir, '.ufazienignore');
  fs.writeFileSync(ufazienignorePath, ufazienignoreContent);
}

export function createPhpProjectStructure(
  projectDir: string,
  websiteName: string,
  hasDatabase: boolean = false
): void {
  const srcDir = path.join(projectDir, 'src');
  fs.ensureDirSync(srcDir);

  // Create root index.php
  const indexPhpContent = hasDatabase
    ? `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${websiteName}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to ${websiteName}</h1>
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
            <p>&copy; <?php echo date('Y'); ?> ${websiteName}. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
`
    : `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${websiteName}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to ${websiteName}</h1>
        </header>
        
        <main>
            <?php
            // Include main application logic
            require_once __DIR__ . '/src/index.php';
            ?>
        </main>
        
        <footer>
            <p>&copy; <?php echo date('Y'); ?> ${websiteName}. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
`;

  fs.writeFileSync(path.join(projectDir, 'index.php'), indexPhpContent);

  // Create src/index.php
  const srcIndexContent = hasDatabase
    ? `<?php
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
`
    : `<?php
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
`;

  fs.writeFileSync(path.join(srcDir, 'index.php'), srcIndexContent);

  // Create src/css directory and style.css
  const cssDir = path.join(srcDir, 'css');
  fs.ensureDirSync(cssDir);

  const cssContent = `/* Main Stylesheet */
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
`;

  fs.writeFileSync(path.join(cssDir, 'style.css'), cssContent);

  // Create src/js directory and main.js
  const jsDir = path.join(srcDir, 'js');
  fs.ensureDirSync(jsDir);

  const jsContent = `// Main JavaScript file
document.addEventListener('DOMContentLoaded', function() {
    console.log('Application loaded successfully!');
    
    // Your JavaScript code here
});
`;

  fs.writeFileSync(path.join(jsDir, 'main.js'), jsContent);

  // Create database.php if database is available
  if (hasDatabase) {
    const databasePhpContent = `<?php
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
`;

    fs.writeFileSync(path.join(projectDir, 'database.php'), databasePhpContent);
  }
}

export function createStaticProjectStructure(projectDir: string, websiteName: string): void {
  const srcDir = path.join(projectDir, 'src');
  fs.ensureDirSync(srcDir);

  const cssDir = path.join(srcDir, 'css');
  fs.ensureDirSync(cssDir);

  const jsDir = path.join(srcDir, 'js');
  fs.ensureDirSync(jsDir);

  // Create root index.html
  const indexHtmlContent = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="${websiteName} - A modern web application">
    <title>${websiteName}</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Welcome to ${websiteName}</h1>
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
            <p>&copy; <span id="year"></span> ${websiteName}. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
`;

  fs.writeFileSync(path.join(projectDir, 'index.html'), indexHtmlContent);

  // Create src/css/style.css
  const cssContent = `/* Main Stylesheet */
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
`;

  fs.writeFileSync(path.join(cssDir, 'style.css'), cssContent);

  // Create src/js/main.js
  const jsContent = `// Main JavaScript file
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
`;

  fs.writeFileSync(path.join(jsDir, 'main.js'), jsContent);
}

export function createBuildProjectStructure(projectDir: string, websiteName: string): void {
  // Create README with instructions
  const readmeContent = `# ${websiteName}

This project is configured for deployment to Ufazien Hosting.

## Build and Deploy

1. Build your project (this will create a \`dist\` or \`build\` folder):
\`\`\`bash
npm run build
# or
yarn build
# or
pnpm build
\`\`\`

2. Deploy to Ufazien:
\`\`\`bash
ufazienjs deploy
\`\`\`

The deployment will automatically upload the contents of your build folder.

## Project Structure

\`\`\`
${path.basename(projectDir)}/
├── dist/          # Your build output (Vite default)
├── build/         # Your build output (React/Create React App default)
├── .ufazien.json  # Ufazien configuration (auto-generated)
└── README.md       # This file
\`\`\`

## Notes

- Make sure your build output includes an \`index.html\` file
- The build folder contents will be deployed automatically
`;

  const readmePath = path.join(projectDir, 'README.md');
  if (!fs.existsSync(readmePath)) {
    fs.writeFileSync(readmePath, readmeContent);
  } else {
    // Append Ufazien deployment section to existing README
    const existingContent = fs.readFileSync(readmePath, 'utf-8');
    
    // Check if Ufazien section already exists
    if (!existingContent.includes('Ufazien Hosting')) {
      const ufazienSection = `

---

## Ufazien Deployment

This project is configured for deployment to Ufazien Hosting.

### Build and Deploy

1. Build your project (this will create a \`dist\` or \`build\` folder):
\`\`\`bash
npm run build
# or
yarn build
# or
pnpm build
\`\`\`

2. Deploy to Ufazien:
\`\`\`bash
ufazienjs deploy
\`\`\`

The deployment will automatically upload the contents of your build folder.
`;
      fs.appendFileSync(readmePath, ufazienSection);
    }
  }
}

