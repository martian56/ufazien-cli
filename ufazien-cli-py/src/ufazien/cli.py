"""
Ufazien CLI - Main entry point using Typer and Rich.
"""

import os
import time
import getpass
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

from ufazien.client import UfazienAPIClient
from ufazien.utils import (
    create_zip,
    create_zip_from_folder,
    find_website_config,
    generate_random_alphabetic,
    save_website_config,
    subdomain_sanitize
)
from ufazien.project import (
    create_config_file,
    create_env_file,
    create_gitignore,
    create_ufazienignore,
    create_php_project_structure,
    create_static_project_structure,
    create_build_project_structure,
)

app = typer.Typer(
    name="ufazien",
    help="🚀 Ufazien CLI - Deploy web applications on Ufazien platform",
    add_completion=False,
)
console = Console()


def require_auth(client: UfazienAPIClient) -> None:
    """Check if user is authenticated, exit if not."""
    if not client.access_token:
        console.print("[red]✗ Error: Not logged in.[/red]")
        console.print("Please run [cyan]ufazien login[/cyan] first.")
        raise typer.Exit(1)


@app.command()
def login(
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Email address"),
    password: Optional[str] = typer.Option(None, "--password", "-p", help="Password (not recommended)"),
) -> None:
    """Login to your Ufazien account."""
    console.print(Panel.fit("[bold cyan]🔐 Login to Ufazien[/bold cyan]", border_style="cyan"))

    if not email:
        email = Prompt.ask("Email")
    if not password:
        password = getpass.getpass("Password: ")

    if not email or not password:
        console.print("[red]✗ Error: Email and password are required.[/red]")
        raise typer.Exit(1)

    with console.status("[bold green]Logging in...", spinner="dots"):
        try:
            client = UfazienAPIClient()
            user = client.login(email, password)
            console.print("[green]✓ Login successful![/green]")
            console.print(f"Welcome, [bold]{user.get('first_name', '')} {user.get('last_name', '')}[/bold] ({user.get('email', '')})")
        except Exception as e:
            console.print(f"[red]✗ Login failed: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def logout() -> None:
    """Logout from your Ufazien account."""
    console.print(Panel.fit("[bold cyan]🚪 Logout from Ufazien[/bold cyan]", border_style="cyan"))

    with console.status("[bold yellow]Logging out...", spinner="dots"):
        try:
            client = UfazienAPIClient()
            client.logout()
            console.print("[green]✓ Logged out successfully[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ Warning: {e}[/yellow]")


@app.command()
def create(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Website name"),
    subdomain: Optional[str] = typer.Option(None, "--subdomain", "-s", help="Subdomain"),
    website_type: Optional[str] = typer.Option(None, "--type", "-t", help="Website type (static or php)"),
    database: bool = typer.Option(False, "--database", "-d", help="Create database (PHP only)"),
) -> None:
    """Create a new website project."""
    console.print(Panel.fit("[bold cyan]✨ Create New Website[/bold cyan]", border_style="cyan"))

    client = UfazienAPIClient()
    require_auth(client)

    project_dir = os.getcwd()
    console.print(f"Project directory: [dim]{project_dir}[/dim]\n")

    existing_config = find_website_config(project_dir)
    if existing_config:
        console.print("[yellow]⚠ Warning: .ufazien.json already exists in this directory.[/yellow]")
        if not Confirm.ask("Do you want to create a new website?", default=False):
            console.print("[dim]Cancelled.[/dim]")
            return

    # Get website name
    if not name:
        name = Prompt.ask("Website name")
    if not name:
        console.print("[red]✗ Error: Website name is required.[/red]")
        raise typer.Exit(1)

    # Get subdomain
    if not subdomain:
        subdomain = Prompt.ask("Subdomain (choose a unique one)")
    if not subdomain:
        console.print("[red]✗ Error: Subdomain is required.[/red]")
        raise typer.Exit(1)

    if not all(c.isalnum() or c == '-' for c in subdomain):
        console.print("[red]✗ Error: Subdomain can only contain letters, numbers, and hyphens.[/red]")
        raise typer.Exit(1)

    # Get website type
    if not website_type:
        console.print("\n[bold]Website type:[/bold]")
        console.print("1. Static (HTML/CSS/JavaScript)")
        console.print("2. PHP")
        console.print("3. Build (Vite/React/etc. - deploy dist/build folder)")
        choice = Prompt.ask("Choose website type", choices=["1", "2", "3"], default="1")
        if choice == '1':
            website_type = 'static'
        elif choice == '2':
            website_type = 'php'
        else:
            website_type = 'build'
    else:
        if website_type not in ['static', 'php', 'build']:
            console.print("[red]✗ Error: Website type must be 'static', 'php', or 'build'.[/red]")
            raise typer.Exit(1)

    needs_database = False
    build_folder = None
    if website_type == 'php':
        if database:
            needs_database = True
        else:
            needs_database = Confirm.ask("Do you want a database?", default=True)
    elif website_type == 'build':
        build_folder = Prompt.ask("What is your build folder named?", default="dist")
        if not build_folder:
            build_folder = "dist"

    description = Prompt.ask("Description (optional)", default="", show_default=False)

    # Create website (build projects use 'static' type on the backend)
    api_website_type = 'static' if website_type == 'build' else website_type
    with console.status("[bold green]Creating website...", spinner="dots"):
        try:
            website = client.create_website(
                name=name,
                subdomain=subdomain,
                website_type=api_website_type,
                description=description if description else None
            )
            console.print(f"[green]✓ Website created:[/green] {website['name']}")
            console.print(f"  URL: [cyan]https://{website['domain']['name']}[/cyan]")
            console.print(f"  Website ID: [dim]{website['id']}[/dim]")
        except Exception as e:
            console.print(f"[red]✗ Error creating website: {e}[/red]")
            raise typer.Exit(1)

    # Create database if needed
    database_obj = None
    if needs_database:
        with console.status("[bold green]Creating database...", spinner="dots"):
            try:
                db_name_from_subdomain = subdomain_sanitize(subdomain)
                random_chars = generate_random_alphabetic(6)
                db_name = f"{db_name_from_subdomain}_{random_chars}_db"
                database_obj = client.create_database(
                    name=db_name,
                    db_type='mysql',
                    description=f"Database for {name}"
                )
                console.print(f"[green]✓ Database created:[/green] {database_obj['name']}")
                console.print(f"  Status: {database_obj.get('status', 'creating')}")

                # Wait for database provisioning
                if database_obj.get('status') != 'active':
                    console.print("[dim]Waiting for database provisioning...[/dim]")
                    max_wait = 60
                    wait_time = 0
                    poll_interval = 2

                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=console,
                    ) as progress:
                        task = progress.add_task("Provisioning database...", total=None)
                        while wait_time < max_wait:
                            time.sleep(poll_interval)
                            wait_time += poll_interval

                            try:
                                database_obj = client.get_database(database_obj['id'])
                                status = database_obj.get('status', 'creating')

                                if status == 'active':
                                    progress.update(task, description="[green]Database is ready![/green]")
                                    break
                                elif status == 'error':
                                    error_msg = database_obj.get('error_message', 'Unknown error')
                                    console.print(f"[red]✗ Database provisioning failed: {error_msg}[/red]")
                                    database_obj = None
                                    break
                            except Exception as e:
                                console.print(f"[yellow]⚠ Error checking database status: {e}[/yellow]")
                                break

                    if wait_time >= max_wait:
                        console.print("[yellow]⚠ Timeout waiting for database provisioning.[/yellow]")
                        console.print("[dim]It may still be processing. Check status later.[/dim]")

                if database_obj and database_obj.get('status') == 'active':
                    try:
                        database_obj = client.get_database(database_obj['id'])
                    except Exception as e:
                        console.print(f"[yellow]⚠ Warning: Could not fetch database credentials: {e}[/yellow]")

                if database_obj:
                    table = Table(show_header=False, box=None, padding=(0, 2))
                    table.add_row("Host:", database_obj.get('host', 'N/A'))
                    table.add_row("Port:", str(database_obj.get('port', 'N/A')))
                    username = database_obj.get('username', '')
                    password = database_obj.get('password', '')
                    if username and password:
                        table.add_row("Username:", username)
                        table.add_row("Password:", password)
                    console.print(table)

            except Exception as e:
                console.print(f"[red]✗ Error creating database: {e}[/red]")
                console.print("[dim]You can create a database later from the web dashboard.[/dim]")

    # Create project structure
    with console.status("[bold green]Creating project structure...", spinner="dots"):
        if website_type == 'php':
            has_db = database_obj is not None and database_obj.get('status') == 'active'
            create_php_project_structure(project_dir, name, has_database=has_db)

            if database_obj:
                username = database_obj.get('username', '')
                password = database_obj.get('password', '')
                if username and password:
                    create_env_file(project_dir, {
                        'host': database_obj.get('host', 'mysql.ufazien.com'),
                        'port': database_obj.get('port', 3306),
                        'name': database_obj.get('name', ''),
                        'username': username,
                        'password': password
                    })
                    create_config_file(project_dir, database_obj)
                    console.print("[green]✓ Created .env file with database credentials[/green]")
                    console.print("[green]✓ Created config.php[/green]")
                else:
                    console.print("[yellow]⚠ Skipping .env file creation - database credentials not yet available[/yellow]")
                    console.print("[dim]Please create .env manually with database credentials once provisioning completes.[/dim]")
                    create_config_file(project_dir, {
                        'host': database_obj.get('host', 'mysql.ufazien.com'),
                        'port': database_obj.get('port', 3306),
                        'name': database_obj.get('name', ''),
                        'username': '',
                        'password': ''
                    })
        elif website_type == 'build':
            create_build_project_structure(project_dir, name)
        else:
            create_static_project_structure(project_dir, name)

        create_gitignore(project_dir)
        # .ufazienignore not needed for build projects (we zip only the build folder)
        if website_type != 'build':
            create_ufazienignore(project_dir)
        
        if website_type == 'build':
            console.print("[green]✓ Created project files:[/green]")
            console.print("  • README.md (deployment instructions)")
            console.print("  • .gitignore")
            console.print("  • .ufazien.json")
            console.print(f"\n[yellow]ℹ Build Project Setup:[/yellow]")
            console.print(f"  1. Build your project (creates {build_folder} folder)")
            console.print(f"  2. Run [cyan]ufazien deploy[/cyan] to deploy the {build_folder} folder")
        else:
            console.print("[green]✓ Created project structure[/green]")

    # Save config
    config = {
        'website_id': website['id'],
        'website_name': website['name'],
        'subdomain': subdomain,
        'website_type': website_type,
        'domain': website['domain']['name'],
        'database_id': database_obj['id'] if database_obj else None
    }
    if build_folder:
        config['build_folder'] = build_folder
    save_website_config(project_dir, config)

    # Success message
    console.print("\n[bold green]✓ Website setup complete![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Add your website files to this directory")
    console.print("  2. Run [cyan]ufazien deploy[/cyan] to deploy your website")


@app.command()
def deploy() -> None:
    """Deploy your website."""
    console.print(Panel.fit("[bold cyan]🚀 Deploy Website[/bold cyan]", border_style="cyan"))

    client = UfazienAPIClient()
    require_auth(client)

    project_dir = os.getcwd()
    config = find_website_config(project_dir)

    if not config:
        console.print("[red]✗ Error: .ufazien.json not found in current directory.[/red]")
        console.print("Please run [cyan]ufazien create[/cyan] first or navigate to a project directory.")
        raise typer.Exit(1)

    website_id = config.get('website_id')
    if not website_id:
        console.print("[red]✗ Error: website_id not found in .ufazien.json[/red]")
        raise typer.Exit(1)

    console.print(f"Website: [bold]{config.get('website_name', 'Unknown')}[/bold]")
    console.print(f"Website ID: [dim]{website_id}[/dim]\n")

    # Check if this is a build project
    website_type = config.get('website_type', '')
    build_folder = config.get('build_folder')
    
    # Create ZIP
    with console.status("[bold green]Creating ZIP archive...", spinner="dots"):
        try:
            if website_type == 'build' and build_folder:
                console.print(f"[dim]Deploying build folder: {build_folder}[/dim]")
                zip_path = create_zip_from_folder(project_dir, build_folder)
            else:
                zip_path = create_zip(project_dir)
            console.print(f"[green]✓ Created ZIP archive[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error creating ZIP file: {e}[/red]")
            raise typer.Exit(1)

    # Upload files
    with console.status("[bold green]Uploading files...", spinner="dots"):
        try:
            response = client.upload_zip(website_id, zip_path)
            console.print("[green]✓ Files uploaded successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error uploading files: {e}[/red]")
            try:
                os.remove(zip_path)
            except Exception:
                pass
            raise typer.Exit(1)

    # Clean up ZIP
    try:
        os.remove(zip_path)
    except Exception:
        pass

    # Trigger deployment
    with console.status("[bold green]Triggering deployment...", spinner="dots"):
        try:
            deployment = client.deploy_website(website_id)
            console.print("[green]✓ Deployment triggered successfully[/green]")
            console.print(f"  Status: {deployment.get('status', 'queued')}")
        except Exception as e:
            console.print(f"[yellow]⚠ Warning: Could not trigger deployment: {e}[/yellow]")
            console.print("[dim]Files have been uploaded. Deployment may start automatically.[/dim]")

    console.print(f"\n[bold green]✓ Deployment complete![/bold green]")
    console.print(f"Your website should be available at: [cyan]https://{config.get('domain', '')}[/cyan]")


@app.command()
def status() -> None:
    """Check your login status and profile."""
    console.print(Panel.fit("[bold cyan]👤 Account Status[/bold cyan]", border_style="cyan"))

    client = UfazienAPIClient()

    if not client.access_token:
        console.print("[yellow]⚠ Not logged in[/yellow]")
        console.print("Run [cyan]ufazien login[/cyan] to authenticate.")
        return

    with console.status("[bold green]Fetching profile...", spinner="dots"):
        try:
            profile = client.get_profile()
            console.print("[green]✓ Logged in[/green]\n")

            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_row("Email:", profile.get('email', 'N/A'))
            table.add_row("Name:", f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip() or 'N/A')
            console.print(table)
        except Exception as e:
            console.print(f"[red]✗ Error fetching profile: {e}[/red]")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()

