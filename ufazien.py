#!/usr/bin/env python3
"""
Ufazien CLI Tool
Command-line interface for deploying web applications on Ufazien platform.
"""

import os
import sys
import json
import zipfile
import tempfile
import shutil
import uuid
import time
import urllib.request
import urllib.parse
import urllib.error
import getpass
from pathlib import Path


class UfazienAPIClient:

    def __init__(self, base_url=None, config_dir=None):
 
        self.base_url = base_url or "https://api.ufazien.com/api"
        if not self.base_url.endswith('/api'):
            if self.base_url.endswith('/'):
                self.base_url = self.base_url.rstrip('/') + '/api'
            else:
                self.base_url = self.base_url + '/api'
        
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            home = Path.home()
            self.config_dir = home / '.ufazien'
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.tokens_file = self.config_dir / 'tokens.json'
        
        self.access_token = None
        self.refresh_token = None
        self._load_tokens()
    
    def _load_tokens(self):
        if self.tokens_file.exists():
            try:
                with open(self.tokens_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
            except (json.JSONDecodeError, IOError):
                pass
    
    def _save_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        try:
            with open(self.tokens_file, 'w') as f:
                json.dump({
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, f)
            os.chmod(self.tokens_file, 0o600)
        except IOError as e:
            print(f"Warning: Could not save tokens: {e}", file=sys.stderr)
    
    def _clear_tokens(self):
        self.access_token = None
        self.refresh_token = None
        if self.tokens_file.exists():
            try:
                self.tokens_file.unlink()
            except IOError:
                pass
    
    def _make_request(self, method, endpoint, data=None, files=None, headers=None):

        url = f"{self.base_url}{endpoint}"
        
        request_headers = {}
        if headers:
            request_headers.update(headers)
        
        if self.access_token:
            request_headers['Authorization'] = f'Bearer {self.access_token}'
        
        req_data = None
        
        if files:
            boundary = '----WebKitFormBoundary' + str(uuid.uuid4()).replace('-', '')
            request_headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
            
            body_parts = []
            
            if data:
                for key, value in data.items():
                    body_parts.append(f'--{boundary}\r\n'.encode('utf-8'))
                    body_parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode('utf-8'))
                    body_parts.append(str(value).encode('utf-8'))
                    body_parts.append(b'\r\n')
            
            for key, file_path in files.items():
                body_parts.append(f'--{boundary}\r\n'.encode('utf-8'))
                
                if isinstance(file_path, str):
                    filename = os.path.basename(file_path)
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                else:
                    filename = getattr(file_path, 'name', 'file')
                    file_content = file_path.read()
                
                body_parts.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode('utf-8'))
                body_parts.append(b'Content-Type: application/octet-stream\r\n\r\n')
                body_parts.append(file_content)
                body_parts.append(b'\r\n')
            
            body_parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
            req_data = b''.join(body_parts)
            
        elif data:
            request_headers['Content-Type'] = 'application/json'
            req_data = json.dumps(data).encode('utf-8')
        
        req = urllib.request.Request(url, data=req_data, headers=request_headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as response:
                response_data = response.read()
                
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return json.loads(response_data.decode('utf-8'))
                else:
                    return response_data
                    
        except urllib.error.HTTPError as e:
            error_data = {}
            try:
                error_body = e.read()
                if error_body:
                    error_data = json.loads(error_body.decode('utf-8'))
            except (json.JSONDecodeError, AttributeError):
                pass
            
            if e.code == 401 and self.refresh_token and endpoint != '/auth/token/refresh/':
                if self._refresh_access_token():
                    return self._make_request(method, endpoint, data, files, headers)
                else:
                    self._clear_tokens()
                    raise Exception("Authentication failed. Please login again using 'python ufazien.py login'")
            
            error_msg = error_data.get('detail', error_data.get('message', f'HTTP {e.code}: {e.reason}'))
            if isinstance(error_msg, dict):
                error_msg = json.dumps(error_msg, indent=2)
            raise Exception(error_msg)
        
        except urllib.error.URLError as e:
            raise Exception(f"Connection error: {e.reason}")
    
    def _refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            return False
        
        try:
            url = f"{self.base_url}/auth/token/refresh/"
            data = json.dumps({'refresh': self.refresh_token}).encode('utf-8')
            
            req = urllib.request.Request(
                url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                new_access_token = response_data.get('access')
                
                if new_access_token:
                    self._save_tokens(new_access_token, self.refresh_token)
                    return True
            
            return False
            
        except Exception:
            return False
    
    def login(self, email, password):
        """
        Login and store tokens.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            User data dict
        """
        response = self._make_request('POST', '/auth/login/', {
            'email': email,
            'password': password
        })
        
        if 'access' in response and 'refresh' in response:
            self._save_tokens(response['access'], response['refresh'])
        
        return response.get('user', {})
    
    def logout(self):
        """Logout and clear tokens."""
        try:
            if self.access_token:
                self._make_request('POST', '/auth/logout/')
        except Exception:
            pass 
        finally:
            self._clear_tokens()
    
    def get_profile(self):
        """Get current user profile."""
        return self._make_request('GET', '/auth/user/')
    
    
    def create_website(self, name, subdomain, website_type, description=None, environment_variables=None, domain_id=None):
        """
        Create a new website.
        
        Args:
            name: Website name
            subdomain: Subdomain (without .ufazien.com)
            website_type: 'static' or 'php'
            description: Optional description
            environment_variables: Optional dict of environment variables
            domain_id: Optional existing domain ID
        
        Returns:
            Created website data
        """
        data = {
            'name': name,
            'website_type': website_type,
        }
        
        if description:
            data['description'] = description
        
        if environment_variables:
            data['environment_variables'] = environment_variables
        
        if domain_id:
            data['domain_id'] = domain_id
        else:
            domain_data = {
                'name': f'{subdomain}.ufazien.com',
                'domain_type': 'subdomain'
            }
            domain = self._make_request('POST', '/hosting/domains/', domain_data)
            data['domain_id'] = domain['id']
        
        return self._make_request('POST', '/hosting/websites/', data)
    
    def create_database(self, name, db_type='mysql', description=None):
        """
        Create a new database.
        
        Args:
            name: Database name
            db_type: 'mysql' or 'postgresql'
            description: Optional description
        
        Returns:
            Created database data with credentials
        """
        data = {
            'name': name,
            'db_type': db_type,
        }
        
        if description:
            data['description'] = description
        
        return self._make_request('POST', '/hosting/databases/', data)
    
    def upload_zip(self, website_id, zip_file_path):
        """
        Upload and extract a ZIP file to a website.
        
        Args:
            website_id: Website ID
            zip_file_path: Path to ZIP file
        
        Returns:
            Upload response
        """
        return self._make_request(
            'POST',
            f'/hosting/websites/{website_id}/upload_zip/',
            files={'zip_file': zip_file_path}
        )
    
    def get_websites(self):
        """Get list of user's websites."""
        return self._make_request('GET', '/hosting/websites/')
    
    def get_website(self, website_id):
        """Get website details."""
        return self._make_request('GET', f'/hosting/websites/{website_id}/')
    
    def deploy_website(self, website_id):
        """Trigger a website deployment."""
        return self._make_request('POST', f'/hosting/websites/{website_id}/deploy/')
    
    def get_available_domains(self):
        """Get list of available domains."""
        return self._make_request('GET', '/hosting/domains/available/')
    
    def get_database(self, database_id):
        """Get database details."""
        return self._make_request('GET', f'/hosting/databases/{database_id}/')



def get_input(prompt, default=None, required=True):
    """Get user input with optional default value."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    while True:
        value = input(prompt).strip()
        if value:
            return value
        elif default:
            return default
        elif not required:
            return None
        else:
            print("This field is required. Please enter a value.")


def get_yes_no(prompt, default=False):
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ('y', 'yes')


def create_config_file(project_dir, db_creds):
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
    
    print(f"✓ Created config.php")


def create_env_file(project_dir, db_creds):
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
    
    print(f"✓ Created .env file with database credentials")


def create_gitignore(project_dir):
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
        print(f"✓ Created .gitignore")
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
            print(f"✓ Updated .gitignore")


def create_ufazienignore(project_dir):
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
"""
    
    ufazienignore_path = Path(project_dir) / '.ufazienignore'
    with open(ufazienignore_path, 'w') as f:
        f.write(ufazienignore_content)
    
    print(f"✓ Created .ufazienignore")


def should_exclude_file(file_path, ufazienignore_path):
    """Check if a file should be excluded based on .ufazienignore."""
    if not ufazienignore_path.exists():
        return False
    
    with open(ufazienignore_path, 'r') as f:
        ignore_patterns = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
    
    file_str = str(file_path)
    for pattern in ignore_patterns:
        if pattern in file_str or file_str.endswith(pattern):
            return True
        if pattern.endswith('/') and file_str.startswith(pattern):
            return True
    
    return False


def create_zip(project_dir, output_path=None):
    """Create a ZIP file of the project, excluding files in .ufazienignore."""
    project_path = Path(project_dir).resolve()
    ufazienignore_path = project_path / '.ufazienignore'
    
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.zip')
    
    print(f"Creating ZIP archive from {project_path}...")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not should_exclude_file(
                Path(root) / d, ufazienignore_path
            )]
            
            for file in files:
                file_path = Path(root) / file
                
                if should_exclude_file(file_path, ufazienignore_path):
                    continue
                
                if file_path.suffix == '.zip' and file_path.name == Path(output_path).name:
                    continue
                
                try:
                    arcname = file_path.relative_to(project_path)
                    zipf.write(file_path, arcname)
                except ValueError:
                    continue
    
    print(f"✓ Created ZIP archive: {output_path}")
    return output_path


def find_website_config(project_dir):
    """Find .ufazien.json config file in project directory."""
    config_path = Path(project_dir) / '.ufazien.json'
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None


def save_website_config(project_dir, config):
    """Save website configuration to .ufazien.json."""
    config_path = Path(project_dir) / '.ufazien.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Add to .gitignore if not present
    gitignore_path = Path(project_dir) / '.gitignore'
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            content = f.read()
        if '.ufazien.json' not in content:
            with open(gitignore_path, 'a') as f:
                f.write('\n.ufazien.json\n')


def create_php_project_structure(project_dir, website_name, has_database=False):
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
    print(f"✓ Created index.php")
    
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
    
    // Example: How to use the database
    echo '<div class="db-examples">';
    echo '<h3>Database Usage Examples</h3>';
    echo '<div class="code-example">';
    echo '<h4>1. Using the global $conn variable:</h4>';
    echo '<pre><code>$stmt = $conn->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([1]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);</code></pre>';
    echo '</div>';
    
    echo '<div class="code-example">';
    echo '<h4>2. Using get_connection() function:</h4>';
    echo '<pre><code>$pdo = get_connection();
$stmt = $pdo->query("SELECT COUNT(*) FROM users");
$count = $stmt->fetchColumn();</code></pre>';
    echo '</div>';
    
    echo '<div class="code-example">';
    echo '<h4>3. Inserting data:</h4>';
    echo '<pre><code>$stmt = $conn->prepare("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)");
$stmt->execute([$username, $email, $password_hash]);</code></pre>';
    echo '</div>';
    
    echo '<div class="code-example">';
    echo '<h4>4. Fetching multiple rows:</h4>';
    echo '<pre><code>$stmt = $conn->query("SELECT * FROM users");
$users = $stmt->fetchAll(PDO::FETCH_ASSOC);
foreach ($users as $user) {
    echo $user[\\'username\\'] . "\\n";
}</code></pre>';
    echo '</div>';
    
    echo '<p class="note"><strong>Tip:</strong> Edit <code>database.php</code> to add more tables and initialize your database schema.</p>';
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
    print(f"✓ Created src/index.php")
    
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

/* Database Status Styles */
.db-status {
    padding: 1rem;
    border-radius: 6px;
    margin: 1.5rem 0;
}

.db-success {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.db-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
}

.db-status h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.2rem;
}

.db-status p {
    margin: 0;
}

/* Database Examples Styles */
.db-examples {
    margin: 2rem 0;
    padding: 1.5rem;
    background: #f8f9fa;
    border-radius: 6px;
    border-left: 4px solid #667eea;
}

.db-examples h3 {
    color: #667eea;
    margin-bottom: 1.5rem;
}

.code-example {
    margin: 1.5rem 0;
    padding: 1rem;
    background: white;
    border-radius: 4px;
    border: 1px solid #e0e0e0;
}

.code-example h4 {
    color: #333;
    margin-bottom: 0.75rem;
    font-size: 1rem;
}

.code-example pre {
    background: #2d2d2d;
    color: #f8f8f2;
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    margin: 0;
}

.code-example code {
    background: transparent;
    color: inherit;
    padding: 0;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    line-height: 1.5;
}

.note {
    margin-top: 1.5rem;
    padding: 1rem;
    background: #fff3cd;
    border: 1px solid #ffc107;
    border-radius: 4px;
    color: #856404;
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
    print(f"✓ Created src/css/style.css")
    
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
    print(f"✓ Created src/js/main.js")
    
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

/**
 * Initialize database tables
 * This function creates the initial tables for your application.
 * Add more table creation statements as needed.
 */
function init_database() {
    $pdo = get_connection();
    if (!$pdo) {
        throw new Exception("Cannot connect to database");
    }
    
    try {
        // Example: Create a users table
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        ");
        
        // Add more tables here as needed
        // Example:
        // $pdo->exec("
        //     CREATE TABLE IF NOT EXISTS posts (
        //         id INT AUTO_INCREMENT PRIMARY KEY,
        //         title VARCHAR(255) NOT NULL,
        //         content TEXT,
        //         user_id INT,
        //         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        //         FOREIGN KEY (user_id) REFERENCES users(id)
        //     ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        // ");
        
        return true;
    } catch (PDOException $e) {
        error_log("Database initialization error: " . $e->getMessage());
        throw $e;
    }
}

// Auto-initialize database on first load (comment out if you want manual control)
// Uncomment the line below to automatically create tables when this file is included
// init_database();

// Make connection available globally
$conn = get_connection();
?>
"""
        
        database_path = project_path / 'database.php'
        with open(database_path, 'w', encoding='utf-8') as f:
            f.write(database_php_content)
        print(f"✓ Created database.php")
    
    print(f"✓ Created PHP project structure")


def create_static_project_structure(project_dir, website_name):
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
    print(f"✓ Created index.html")
    
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
    print(f"✓ Created src/css/style.css")
    
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
    print(f"✓ Created src/js/main.js")
    
    print(f"✓ Created static website project structure")


# Command handlers

def cmd_create(client):
    """Handle 'create' command."""
    print("\n=== Create New Website ===\n")
    
    project_dir = os.getcwd()
    print(f"Project directory: {project_dir}\n")
    
    existing_config = find_website_config(project_dir)
    if existing_config:
        print("⚠ Warning: .ufazien.json already exists in this directory.")
        if not get_yes_no("Do you want to create a new website?", default=False):
            print("Cancelled.")
            return
    
    name = get_input("Website name")
    subdomain = get_input("Subdomain (choose a unique one)", required=True)
    
    if not all(c.isalnum() or c == '-' for c in subdomain):
        print("Error: Subdomain can only contain letters, numbers, and hyphens.")
        return
    
    print("\nWebsite type:")
    print("1. Static (HTML/CSS/JavaScript)")
    print("2. PHP")
    website_type_choice = get_input("Choose website type (1 or 2)", required=True)
    
    if website_type_choice == '1':
        website_type = 'static'
        needs_database = False
    elif website_type_choice == '2':
        website_type = 'php'
        needs_database = get_yes_no("Do you want a database?", default=True)
    else:
        print("Invalid choice.")
        return
    
    description = get_input("Description (optional)", required=False)
    
    print("\nCreating website...")
    try:
        website = client.create_website(
            name=name,
            subdomain=subdomain,
            website_type=website_type,
            description=description
        )
        print(f"✓ Website created: {website['name']}")
        print(f"  URL: https://{website['domain']['name']}")
        print(f"  Website ID: {website['id']}")
    except Exception as e:
        print(f"✗ Error creating website: {e}")
        return
    
    database = None
    if needs_database:
        print("\nCreating database...")
        try:
            db_name = f"{subdomain}_db"
            database = client.create_database(
                name=db_name,
                db_type='mysql',
                description=f"Database for {name}"
            )
            print(f"✓ Database created: {database['name']}")
            print(f"  Status: {database.get('status', 'creating')}")
            
            if database.get('status') != 'active':
                print("  Waiting for database provisioning...")
                max_wait = 60 
                wait_time = 0
                poll_interval = 2 
                
                while wait_time < max_wait:
                    time.sleep(poll_interval)
                    wait_time += poll_interval
                    
                    try:
                        database = client.get_database(database['id'])
                        status = database.get('status', 'creating')
                        
                        if status == 'active':
                            print(f"  ✓ Database is ready!")
                            break
                        elif status == 'error':
                            error_msg = database.get('error_message', 'Unknown error')
                            print(f"  ✗ Database provisioning failed: {error_msg}")
                            database = None
                            break
                        else:
                            print(f"  ... Still provisioning (status: {status})")
                    except Exception as e:
                        print(f"  ⚠ Error checking database status: {e}")
                        break
                
                if wait_time >= max_wait:
                    print(f"  ⚠ Timeout waiting for database provisioning. It may still be processing.")
                    print(f"     You can check the status later and update .env manually.")
            
            if database and database.get('status') == 'active':
                try:
                    database = client.get_database(database['id'])
                except Exception as e:
                    print(f"  ⚠ Warning: Could not fetch database credentials: {e}")
            
            if database:
                print(f"  Host: {database.get('host', 'N/A')}")
                print(f"  Port: {database.get('port', 'N/A')}")
                username = database.get('username', '')
                password = database.get('password', '')
                if username and password:
                    print(f"  Username: {username}")
                    print(f"  Password: {password}")
                else:
                    print(f"  ⚠ Warning: Database credentials not yet available")
                    print(f"     The database is still being provisioned. Please update .env manually later.")
            
        except Exception as e:
            print(f"✗ Error creating database: {e}")
            print("  You can create a database later from the web dashboard.")
    
    print("\nCreating project structure...")
    
    if website_type == 'php':
        has_db = database is not None and database.get('status') == 'active'
        create_php_project_structure(project_dir, name, has_database=has_db)
        
        if database:
            username = database.get('username', '')
            password = database.get('password', '')
            
            if username and password:
                create_env_file(project_dir, {
                    'host': database.get('host', 'mysql.ufazien.com'),
                    'port': database.get('port', 3306),
                    'name': database.get('name', ''),
                    'username': username,
                    'password': password
                })
                create_config_file(project_dir, database)
            else:
                print("  ⚠ Skipping .env file creation - database credentials not yet available")
                print("     Please create .env manually with database credentials once provisioning completes.")
                create_config_file(project_dir, {
                    'host': database.get('host', 'mysql.ufazien.com'),
                    'port': database.get('port', 3306),
                    'name': database.get('name', ''),
                    'username': '',
                    'password': ''
                })
    else:
        create_static_project_structure(project_dir, name)
    
    create_gitignore(project_dir)
    create_ufazienignore(project_dir)
    
    config = {
        'website_id': website['id'],
        'website_name': website['name'],
        'subdomain': subdomain,
        'website_type': website_type,
        'domain': website['domain']['name'],
        'database_id': database['id'] if database else None
    }
    save_website_config(project_dir, config)
    
    print("\n✓ Website setup complete!")
    print(f"\nNext steps:")
    print(f"  1. Add your website files to this directory")
    print(f"  2. Run 'python ufazien.py deploy' to deploy your website")


def cmd_deploy(client):
    """Handle 'deploy' command."""
    print("\n=== Deploy Website ===\n")
    
    project_dir = os.getcwd()
    
    config = find_website_config(project_dir)
    if not config:
        print("✗ Error: .ufazien.json not found in current directory.")
        print("  Please run 'python ufazien.py create' first or navigate to a project directory.")
        return
    
    website_id = config.get('website_id')
    if not website_id:
        print("✗ Error: website_id not found in .ufazien.json")
        return
    
    print(f"Website: {config.get('website_name', 'Unknown')}")
    print(f"Website ID: {website_id}\n")
    
    try:
        zip_path = create_zip(project_dir)
    except Exception as e:
        print(f"✗ Error creating ZIP file: {e}")
        return
    
    print(f"\nUploading files...")
    try:
        response = client.upload_zip(website_id, zip_path)
        print("✓ Files uploaded successfully")
    except Exception as e:
        print(f"✗ Error uploading files: {e}")
        try:
            os.remove(zip_path)
        except:
            pass
        return
    
    try:
        os.remove(zip_path)
    except:
        pass
    
    print("\nTriggering deployment...")
    try:
        deployment = client.deploy_website(website_id)
        print("✓ Deployment triggered successfully")
        print(f"  Status: {deployment.get('status', 'queued')}")
    except Exception as e:
        print(f"⚠ Warning: Could not trigger deployment: {e}")
        print("  Files have been uploaded. Deployment may start automatically.")
    
    print("\n✓ Deployment complete!")
    print(f"  Your website should be available at: https://{config.get('domain', '')}")


def cmd_login(client):
    """Handle 'login' command."""
    print("\n=== Login to Ufazien ===\n")
    
    email = get_input("Email", required=True)
    password = getpass.getpass("Password: ")
    
    if not password:
        print("✗ Error: Password is required.")
        sys.exit(1)
    
    print("\nLogging in...")
    try:
        user = client.login(email, password)
        print(f"✓ Login successful!")
        print(f"  Welcome, {user.get('first_name', '')} {user.get('last_name', '')} ({user.get('email', '')})")
    except Exception as e:
        print(f"✗ Login failed: {e}")
        sys.exit(1)


def cmd_logout(client):
    """Handle 'logout' command."""
    print("\nLogging out...")
    client.logout()
    print("✓ Logged out successfully")


def main():
    """Main entry point for the CLI tool."""
    if len(sys.argv) < 2:
        print("Ufazien CLI Tool")
        print("\nUsage: python ufazien.py <command>")
        print("\nCommands:")
        print("  login    - Login to your Ufazien account")
        print("  logout   - Logout from your Ufazien account")
        print("  create   - Create a new website project")
        print("  deploy   - Deploy your website")
        print("\nExamples:")
        print("  python ufazien.py login")
        print("  python ufazien.py create")
        print("  python ufazien.py deploy")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    client = UfazienAPIClient()
    
    if command == 'login':
        cmd_login(client)
    elif command == 'logout':
        cmd_logout(client)
    elif command == 'create':
        if not client.access_token:
            print("✗ Error: Not logged in. Please run 'python ufazien.py login' first.")
            sys.exit(1)
        cmd_create(client)
    elif command == 'deploy':
        if not client.access_token:
            print("✗ Error: Not logged in. Please run 'python ufazien.py login' first.")
            sys.exit(1)
        cmd_deploy(client)
    else:
        print(f"✗ Unknown command: {command}")
        print("Run 'python ufazien.py' without arguments to see available commands.")
        sys.exit(1)


if __name__ == '__main__':
    main()
