/**
 * Utility functions for the Ufazien CLI.
 */

import fs from 'fs-extra';
import path from 'path';

export interface WebsiteConfig {
  website_id: string;
  website_name: string;
  subdomain: string;
  website_type: string;
  domain: string;
  database_id?: string;
}

export function findWebsiteConfig(projectDir: string): WebsiteConfig | null {
  const configPath = path.join(projectDir, '.ufazien.json');
  if (fs.existsSync(configPath)) {
    try {
      return fs.readJsonSync(configPath);
    } catch (error) {
      return null;
    }
  }
  return null;
}

export function saveWebsiteConfig(projectDir: string, config: WebsiteConfig): void {
  const configPath = path.join(projectDir, '.ufazien.json');
  fs.writeJsonSync(configPath, config, { spaces: 2 });

  // Add to .gitignore if not present
  const gitignorePath = path.join(projectDir, '.gitignore');
  if (fs.existsSync(gitignorePath)) {
    const content = fs.readFileSync(gitignorePath, 'utf-8');
    if (!content.includes('.ufazien.json')) {
      fs.appendFileSync(gitignorePath, '\n.ufazien.json\n');
    }
  }
}

export function shouldExcludeFile(filePath: string, ufazienignorePath: string): boolean {
  if (!fs.existsSync(ufazienignorePath)) {
    return false;
  }

  const ignorePatterns = fs
    .readFileSync(ufazienignorePath, 'utf-8')
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));

  for (const pattern of ignorePatterns) {
    if (filePath.includes(pattern) || filePath.endsWith(pattern)) {
      return true;
    }
    if (pattern.endsWith('/') && filePath.startsWith(pattern)) {
      return true;
    }
  }

  return false;
}

export function generateRandomAlphabetic(length: number = 6): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz';
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}

