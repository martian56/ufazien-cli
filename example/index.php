<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Task Manager - Stay Organized</title>
    <link rel="stylesheet" href="src/css/style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>Tasks</h1>
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
            <p>&copy; <?php echo date('Y'); ?> Task Manager. All rights reserved.</p>
        </footer>
    </div>
    
    <script src="src/js/main.js"></script>
</body>
</html>
