const fs = require('fs');
const path = require('path');

const outDir = path.resolve(__dirname, '..', 'out');
const staticDir = path.resolve(__dirname, '..', '..', 'sales_api', 'static');

if (!fs.existsSync(outDir)) {
  console.error("Error: out/ directory does not exist. Run 'npm run build' first.");
  process.exit(1);
}

// Backup original index.html if index.old.html does not exist yet
const origIndex = path.join(staticDir, 'index.html');
const backupIndex = path.join(staticDir, 'index.old.html');
if (fs.existsSync(origIndex) && !fs.existsSync(backupIndex)) {
  fs.copyFileSync(origIndex, backupIndex);
  console.log(`Backed up original index.html to index.old.html`);
}

function copyRecursiveSync(src, dest) {
  const exists = fs.existsSync(src);
  const stats = exists && fs.statSync(src);
  const isDirectory = exists && stats.isDirectory();
  if (isDirectory) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }
    fs.readdirSync(src).forEach((childItemName) => {
      copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

console.log(`Syncing Next.js build from ${outDir} to ${staticDir}...`);
copyRecursiveSync(outDir, staticDir);
console.log(`Successfully synced frontend build to sales_api/static!`);
