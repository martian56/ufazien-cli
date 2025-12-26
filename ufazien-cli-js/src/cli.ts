#!/usr/bin/env node

/**
 * Ufazien CLI - Main entry point
 */

import { Command } from 'commander';
import chalk from 'chalk';
import inquirer from 'inquirer';
import fs from 'fs-extra';
import path from 'path';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { UfazienAPIClient, Database } from './client.js';
import {
  findWebsiteConfig,
  saveWebsiteConfig,
  generateRandomAlphabetic,
  sanitizeDatabaseName,
} from './utils.js';
import {
  createConfigFile,
  createEnvFile,
  createGitignore,
  createUfazienignore,
  createPhpProjectStructure,
  createStaticProjectStructure,
  createBuildProjectStructure,
  DatabaseCredentials,
} from './project.js';
import { createZip, createZipFromFolder } from './zip.js';

// Get version from package.json
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const packageJsonPath = join(__dirname, '../package.json');
const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));

const program = new Command();

program
  .name('ufazienjs')
  .description('🚀 Ufazien CLI - Deploy web applications on Ufazien platform')
  .version(packageJson.version);

function requireAuth(client: UfazienAPIClient): void {
  if (!client.accessToken) {
      console.error(chalk.red('✗ Error: Not logged in.'));
      console.log('Please run', chalk.cyan('ufazienjs login'), 'first.');
    process.exit(1);
  }
}


program
  .command('login')
  .description('Login to your Ufazien account')
  .option('-e, --email <email>', 'Email address')
  .option('-p, --password <password>', 'Password (not recommended)')
  .action(async (options) => {
    console.log(chalk.cyan.bold('\n🔐 Login to Ufazien\n'));

    let email = options.email;
    let password = options.password;

    if (!email) {
      const answer = await inquirer.prompt([
        {
          type: 'input',
          name: 'email',
          message: 'Email:',
          validate: (input) => (input ? true : 'Email is required'),
        },
      ]);
      email = answer.email;
    }

    if (!password) {
      const answer = await inquirer.prompt([
        {
          type: 'password',
          name: 'password',
          message: 'Password:',
          mask: '*',
          validate: (input) => (input ? true : 'Password is required'),
        },
      ]);
      password = answer.password;
    }

    if (!email || !password) {
      console.error(chalk.red('✗ Error: Email and password are required.'));
      process.exit(1);
    }

    try {
      process.stdout.write(chalk.green('Logging in...'));
      const client = new UfazienAPIClient();
      const user = await client.login(email, password);
      console.log(chalk.green('\n✓ Login successful!'));
      console.log(
        `Welcome, ${chalk.bold(`${user.first_name || ''} ${user.last_name || ''}`.trim())} (${user.email})`
      );
    } catch (error: any) {
      console.log('');
      console.error(chalk.red(`✗ Login failed: ${error.message}`));
      process.exit(1);
    }
  });

program
  .command('logout')
  .description('Logout from your Ufazien account')
  .action(async () => {
    console.log(chalk.cyan.bold('\n🚪 Logout from Ufazien\n'));

    try {
      process.stdout.write(chalk.yellow('Logging out...'));
      const client = new UfazienAPIClient();
      await client.logout();
      console.log(chalk.green('\n✓ Logged out successfully'));
    } catch (error: any) {
      console.log('');
      console.warn(chalk.yellow(`⚠ Warning: ${error.message}`));
    }
  });

program
  .command('create')
  .description('Create a new website project')
  .option('-n, --name <name>', 'Website name')
  .option('-s, --subdomain <subdomain>', 'Subdomain')
  .option('-t, --type <type>', 'Website type (static or php)')
  .option('-d, --database', 'Create database (PHP only)')
  .action(async (options) => {
    console.log(chalk.cyan.bold('\n✨ Create New Website\n'));

    const client = new UfazienAPIClient();
    requireAuth(client);

    const projectDir = process.cwd();
    console.log(`Project directory: ${chalk.dim(projectDir)}\n`);

    const existingConfig = findWebsiteConfig(projectDir);
    if (existingConfig) {
      console.warn(chalk.yellow('⚠ Warning: .ufazien.json already exists in this directory.'));
      const answer = await inquirer.prompt([
        {
          type: 'confirm',
          name: 'continue',
          message: 'Do you want to create a new website?',
          default: false,
        },
      ]);
      if (!answer.continue) {
        console.log(chalk.dim('Cancelled.'));
        return;
      }
    }

    // Get website name
    let name = options.name;
    if (!name) {
      const answer = await inquirer.prompt([
        {
          type: 'input',
          name: 'name',
          message: 'Website name:',
          validate: (input) => (input ? true : 'Website name is required'),
        },
      ]);
      name = answer.name;
    }

    // Get subdomain
    let subdomain = options.subdomain;
    if (!subdomain) {
      const answer = await inquirer.prompt([
        {
          type: 'input',
          name: 'subdomain',
          message: 'Subdomain (choose a unique one):',
          validate: (input) => {
            if (!input) return 'Subdomain is required';
            if (!/^[a-z0-9-]+$/.test(input)) {
              return 'Subdomain can only contain lowercase letters, numbers, and hyphens';
            }
            return true;
          },
        },
      ]);
      subdomain = answer.subdomain;
    }

    // Get website type
    let websiteType = options.type;
    if (!websiteType) {
      const answer = await inquirer.prompt([
        {
          type: 'list',
          name: 'type',
          message: 'Choose website type:',
          choices: [
            { name: 'Static (HTML/CSS/JavaScript)', value: 'static' },
            { name: 'PHP', value: 'php' },
            { name: 'Build (Vite/React/etc. - deploy dist/build folder)', value: 'build' },
          ],
        },
      ]);
      websiteType = answer.type;
    } else if (!['static', 'php', 'build'].includes(websiteType)) {
      console.error(chalk.red("✗ Error: Website type must be 'static', 'php', or 'build'."));
      process.exit(1);
    }

    let needsDatabase = false;
    let buildFolder: string | undefined = undefined;
    if (websiteType === 'php') {
      if (options.database) {
        needsDatabase = true;
      } else {
        const answer = await inquirer.prompt([
          {
            type: 'confirm',
            name: 'database',
            message: 'Do you want a database?',
            default: true,
          },
        ]);
        needsDatabase = answer.database;
      }
    } else if (websiteType === 'build') {
      const answer = await inquirer.prompt([
        {
          type: 'input',
          name: 'buildFolder',
          message: 'What is your build folder named?',
          default: 'dist',
        },
      ]);
      buildFolder = answer.buildFolder || 'dist';
    }

    const descAnswer = await inquirer.prompt([
      {
        type: 'input',
        name: 'description',
        message: 'Description (optional):',
        default: '',
      },
    ]);
    const description = descAnswer.description || undefined;

    // Create website (build projects use 'static' type on the backend)
    const apiWebsiteType = websiteType === 'build' ? 'static' : websiteType;
    try {
      process.stdout.write(chalk.green('Creating website...'));
      const website = await client.createWebsite(
        name,
        subdomain,
        apiWebsiteType,
        description
      );
      console.log(chalk.green('\n✓ Website created:'), website.name);
      console.log(`  URL: ${chalk.cyan(`https://${website.domain.name}`)}`);
      console.log(`  Website ID: ${chalk.dim(website.id)}`);

      // Create database if needed
      let database: Database | null = null;
      if (needsDatabase) {
        process.stdout.write(chalk.green('\nCreating database...'));
        try {
          const randomChars = generateRandomAlphabetic(6);
          const rawDbName = `${subdomain}_${randomChars}_db`;
          const dbName = sanitizeDatabaseName(rawDbName);
          database = await client.createDatabase(dbName, 'mysql', `Database for ${name}`);
          console.log(chalk.green('\n✓ Database created:'), database.name);
          console.log(`  Status: ${database.status}`);

          // Wait for database provisioning
          if (database.status !== 'active') {
            console.log(chalk.dim('\nWaiting for database provisioning...'));
            const maxWait = 60;
            let waitTime = 0;
            const pollInterval = 2000;

            while (waitTime < maxWait * 1000) {
              await new Promise((resolve) => setTimeout(resolve, pollInterval));
              waitTime += pollInterval;

              try {
                database = await client.getDatabase(database.id);
                const status = database.status;

                if (status === 'active') {
                  console.log(chalk.green('  ✓ Database is ready!'));
                  break;
                } else if (status === 'error') {
                  const errorMsg = database.error_message || 'Unknown error';
                  console.error(chalk.red(`  ✗ Database provisioning failed: ${errorMsg}`));
                  database = null;
                  break;
                } else {
                  process.stdout.write(chalk.dim(`  ... Still provisioning (status: ${status})\r`));
                }
              } catch (error: any) {
                console.warn(chalk.yellow(`  ⚠ Error checking database status: ${error.message}`));
                break;
              }
            }

            if (waitTime >= maxWait * 1000) {
              console.log(chalk.yellow('\n  ⚠ Timeout waiting for database provisioning.'));
              console.log(chalk.dim('  It may still be processing. Check status later.'));
            }
          }

          if (database && database.status === 'active') {
            try {
              database = await client.getDatabase(database.id);
            } catch (error: any) {
              console.warn(chalk.yellow(`  ⚠ Warning: Could not fetch database credentials: ${error.message}`));
            }
          }

          if (database) {
            console.log(`  Host: ${database.host || 'N/A'}`);
            console.log(`  Port: ${database.port || 'N/A'}`);
            if (database.username && database.password) {
              console.log(`  Username: ${database.username}`);
              console.log(`  Password: ${database.password}`);
            }
          }
        } catch (error: any) {
          console.log('');
          console.error(chalk.red(`✗ Error creating database: ${error.message}`));
          console.log(chalk.dim('You can create a database later from the web dashboard.'));
        }
      }

      // Create project structure
      process.stdout.write(chalk.green('\nCreating project structure...'));
      if (websiteType === 'php') {
        const hasDb = database !== null && database.status === 'active';
        createPhpProjectStructure(projectDir, name, hasDb);

        if (database) {
          const username = database.username || '';
          const password = database.password || '';
          if (username && password) {
            createEnvFile(projectDir, {
              name: database.name,
              host: database.host || 'mysql.ufazien.com',
              port: database.port || 3306,
              username,
              password,
            });
            createConfigFile(projectDir, {
              name: database.name,
              host: database.host || 'mysql.ufazien.com',
              port: database.port || 3306,
              username,
              password,
            });
            console.log(chalk.green('\n✓ Created .env file with database credentials'));
            console.log(chalk.green('✓ Created config.php'));
          } else {
            console.log(chalk.yellow('\n⚠ Skipping .env file creation - database credentials not yet available'));
            console.log(chalk.dim('Please create .env manually with database credentials once provisioning completes.'));
            createConfigFile(projectDir, {
              name: database.name,
              host: database.host || 'mysql.ufazien.com',
              port: database.port || 3306,
              username: '',
              password: '',
            });
          }
        }
      } else if (websiteType === 'build') {
        createBuildProjectStructure(projectDir, name);
      } else {
        createStaticProjectStructure(projectDir, name);
      }

      createGitignore(projectDir);
      // .ufazienignore not needed for build projects (we zip only the build folder)
      if (websiteType !== 'build') {
        createUfazienignore(projectDir);
      }
      
      if (websiteType === 'build') {
        console.log(chalk.green('✓ Created project files:'));
        console.log('  • README.md (deployment instructions)');
        console.log('  • .gitignore');
        console.log('  • .ufazien.json');
        console.log(chalk.yellow(`\nℹ Build Project Setup:`));
        console.log(`  1. Build your project (creates ${buildFolder} folder)`);
        console.log(`  2. Run ${chalk.cyan('ufazienjs deploy')} to deploy the ${buildFolder} folder`);
      } else {
        console.log(chalk.green('✓ Created project structure'));
      }

      // Save config
      const config: any = {
        website_id: website.id,
        website_name: website.name,
        subdomain,
        website_type: websiteType,
        domain: website.domain.name,
        database_id: database?.id,
      };
      if (buildFolder) {
        config.build_folder = buildFolder;
      }
      saveWebsiteConfig(projectDir, config);

      // Success message
      console.log(chalk.green.bold('\n✓ Website setup complete!'));
      console.log(chalk.bold('\nNext steps:'));
      console.log('  1. Add your website files to this directory');
      console.log(`  2. Run ${chalk.cyan('ufazienjs deploy')} to deploy your website`);
    } catch (error: any) {
      console.log('');
      console.error(chalk.red(`✗ Error creating website: ${error.message}`));
      process.exit(1);
    }
  });

program
  .command('deploy')
  .description('Deploy your website')
  .action(async () => {
    console.log(chalk.cyan.bold('\n🚀 Deploy Website\n'));

    const client = new UfazienAPIClient();
    requireAuth(client);

    const projectDir = process.cwd();
    const config = findWebsiteConfig(projectDir);

    if (!config) {
      console.error(chalk.red('✗ Error: .ufazien.json not found in current directory.'));
      console.log('Please run', chalk.cyan('ufazienjs create'), 'first or navigate to a project directory.');
      process.exit(1);
    }

    const websiteId = config.website_id;
    if (!websiteId) {
      console.error(chalk.red('✗ Error: website_id not found in .ufazien.json'));
      process.exit(1);
    }

    console.log(`Website: ${chalk.bold(config.website_name || 'Unknown')}`);
    console.log(`Website ID: ${chalk.dim(websiteId)}\n`);

    // Check if this is a build project
    const websiteType = config.website_type || '';
    const buildFolder = config.build_folder;

    // Create ZIP
    try {
      process.stdout.write(chalk.green('Creating ZIP archive...'));
      let zipPath: string;
      if (websiteType === 'build' && buildFolder) {
        console.log(chalk.dim(`\nDeploying build folder: ${buildFolder}`));
        zipPath = await createZipFromFolder(projectDir, buildFolder);
      } else {
        zipPath = await createZip(projectDir);
      }
      console.log(chalk.green('\n✓ Created ZIP archive'));

      // Upload files
      process.stdout.write(chalk.green('Uploading files...'));
      await client.uploadZip(websiteId, zipPath);
      console.log(chalk.green('\n✓ Files uploaded successfully'));

      // Clean up ZIP
      try {
        fs.removeSync(zipPath);
      } catch (error) {
        // Ignore cleanup errors
      }

      // Trigger deployment
      process.stdout.write(chalk.green('Triggering deployment...'));
      const deployment = await client.deployWebsite(websiteId);
      console.log(chalk.green('\n✓ Deployment triggered successfully'));
      console.log(`  Status: ${deployment.status || 'queued'}`);
    } catch (error: any) {
      console.log('');
      if (error.message.includes('ZIP')) {
        console.error(chalk.red(`✗ Error creating ZIP file: ${error.message}`));
      } else if (error.message.includes('upload')) {
        console.error(chalk.red(`✗ Error uploading files: ${error.message}`));
      } else {
        console.warn(chalk.yellow(`⚠ Warning: Could not trigger deployment: ${error.message}`));
        console.log(chalk.dim('Files have been uploaded. Deployment may start automatically.'));
      }
      process.exit(1);
    }

    console.log(chalk.green.bold('\n✓ Deployment complete!'));
    console.log(`Your website should be available at: ${chalk.cyan(`https://${config.domain || ''}`)}`);
  });

program
  .command('status')
  .description('Check your login status and profile')
  .action(async () => {
    console.log(chalk.cyan.bold('\n👤 Account Status\n'));

    const client = new UfazienAPIClient();

    if (!client.accessToken) {
      console.warn(chalk.yellow('⚠ Not logged in'));
      console.log('Run', chalk.cyan('ufazienjs login'), 'to authenticate.');
      return;
    }

    try {
      process.stdout.write(chalk.green('Fetching profile...'));
      const profile = await client.getProfile();
      console.log(chalk.green('\n✓ Logged in\n'));

      console.log(`Email: ${profile.email || 'N/A'}`);
      const fullName = `${profile.first_name || ''} ${profile.last_name || ''}`.trim();
      console.log(`Name: ${fullName || 'N/A'}`);
    } catch (error: any) {
      console.log('');
      console.error(chalk.red(`✗ Error fetching profile: ${error.message}`));
    }
  });

program.parse();

