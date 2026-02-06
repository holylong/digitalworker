#!/usr/bin/env node

/**
 * Cross-platform A2UI bundling script
 * Replaces scripts/bundle-a2ui.sh for Windows compatibility
 */

import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, join, relative, sep } from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = join(__dirname, "..");
const HASH_FILE = join(ROOT_DIR, "src/canvas-host/a2ui/.bundle.hash");
const OUTPUT_FILE = join(ROOT_DIR, "src/canvas-host/a2ui/a2ui.bundle.js");
const A2UI_RENDERER_DIR = join(ROOT_DIR, "vendor/a2ui/renderers/lit");
const A2UI_APP_DIR = join(ROOT_DIR, "apps/shared/OpenClawKit/Tools/CanvasA2UI");

/**
 * Compute hash of input files for cache invalidation
 */
async function computeHash() {
  const inputPaths = [
    join(ROOT_DIR, "package.json"),
    join(ROOT_DIR, "pnpm-lock.yaml"),
    A2UI_RENDERER_DIR,
    A2UI_APP_DIR,
  ];

  // Docker builds exclude vendor/apps via .dockerignore.
  if (!existsSync(A2UI_RENDERER_DIR) || !existsSync(A2UI_APP_DIR)) {
    console.log("A2UI sources missing; keeping prebuilt bundle.");
    return null;
  }

  const files = [];

  async function walk(entryPath) {
    const st = await stat(entryPath);
    if (st.isDirectory()) {
      const entries = await readdir(entryPath);
      for (const entry of entries) {
        await walk(join(entryPath, entry));
      }
      return;
    }
    files.push(entryPath);
  }

  for (const input of inputPaths) {
    await walk(input);
  }

  function normalize(p) {
    return p.split(sep).join("/");
  }

  files.sort((a, b) => normalize(a).localeCompare(normalize(b)));

  const hash = createHash("sha256");
  for (const filePath of files) {
    const fs = await import("node:fs/promises");
    const rel = normalize(relative(ROOT_DIR, filePath));
    hash.update(rel);
    hash.update("\0");
    hash.update(await fs.readFile(filePath));
    hash.update("\0");
  }

  return hash.digest("hex");
}

/**
 * Main build function
 */
async function build() {
  try {
    const currentHash = await computeHash();

    if (currentHash === null) {
      process.exit(0);
    }

    // Check if we need to rebuild
    if (existsSync(HASH_FILE) && existsSync(OUTPUT_FILE)) {
      const fs = await import("node:fs/promises");
      const previousHash = await fs.readFile(HASH_FILE, "utf8");
      if (previousHash === currentHash) {
        console.log("A2UI bundle up to date; skipping.");
        process.exit(0);
      }
    }

    // Build TypeScript
    console.log("Building A2UI TypeScript...");
    execSync('pnpm -s exec tsc -p "' + join(A2UI_RENDERER_DIR, "tsconfig.json") + '"', {
      cwd: ROOT_DIR,
      stdio: "inherit",
    });

    // Run rolldown
    console.log("Bundling with rolldown...");
    execSync('rolldown -c "' + join(A2UI_APP_DIR, "rolldown.config.mjs") + '"', {
      cwd: ROOT_DIR,
      stdio: "inherit",
    });

    // Write hash file
    await mkdir(dirname(HASH_FILE), { recursive: true });
    await writeFile(HASH_FILE, currentHash, "utf8");

    console.log("A2UI bundle built successfully.");
  } catch (error) {
    console.error("A2UI bundling failed. Re-run with: pnpm canvas:a2ui:bundle");
    console.error("If this persists, verify pnpm deps and try again.");
    process.exit(1);
  }
}

build();
