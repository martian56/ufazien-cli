/**
 * ZIP file creation utilities.
 */

// @ts-ignore - archiver doesn't have type definitions
import archiver from 'archiver';
import fs from 'fs-extra';
import path from 'path';
import { shouldExcludeFile } from './utils.js';

export async function createZip(projectDir: string, outputPath?: string): Promise<string> {
  const projectPath = path.resolve(projectDir);
  const ufazienignorePath = path.join(projectPath, '.ufazienignore');

  if (!outputPath) {
    outputPath = path.join(projectPath, `temp-${Date.now()}.zip`);
  }

  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(outputPath!);
    const archive = archiver('zip', {
      zlib: { level: 9 },
    });

    output.on('close', () => {
      resolve(outputPath!);
    });

    archive.on('error', (err: Error) => {
      reject(err);
    });

    archive.pipe(output);

    // Walk directory and add files
    function walkDir(dir: string, baseDir: string): void {
      const files = fs.readdirSync(dir);

      for (const file of files) {
        const filePath = path.join(dir, file);
        const relativePath = path.relative(baseDir, filePath);

        // Skip the zip file itself
        if (filePath === outputPath) {
          continue;
        }

        // Check if should be excluded
        if (shouldExcludeFile(filePath, ufazienignorePath)) {
          continue;
        }

        const stat = fs.statSync(filePath);
        if (stat.isDirectory()) {
          walkDir(filePath, baseDir);
        } else {
          archive.file(filePath, { name: relativePath });
        }
      }
    }

    walkDir(projectPath, projectPath);
    archive.finalize();
  });
}

