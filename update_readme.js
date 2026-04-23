const fs = require('fs');
const path = 'README.md';
if (!fs.existsSync(path)) return;
let content = fs.readFileSync(path, 'utf8');
// Find all headers (except the title # header)
const lines = content.split('\n');
const tocLines = [];
let outLines = [];
let inToc = false;
// Gather headers for the TOC
for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    // Skip existing TOC
    if (line.match(/^#+\s/)) {
        const hLevel = line.match(/^(#+)\s/)[1].length;
        const text = line.replace(/^#+\s/, '').trim();
        if (text.toLowerCase() === 'table of contents') continue;
        // Generate anchor link (GitHub style)
        let anchor = text.toLowerCase()
                         .replace(/[^\w\s-]/g, '')
                         .replace(/\s+/g, '-');
        // Only include levels 2 to 4
        if (hLevel >= 2 && hLevel <= 4) {
            const indent = '  '.repeat(hLevel - 2);
            tocLines.push(`${indent}- [${text}](#${anchor})`);
        }
    }
}
// Build the new TOC
const toc = '## Table of Contents\n\n' + tocLines.join('\n') + '\n\n';
// Remove old TOC if it exists
content = content.replace(/## Table of Contents[\s\S]*?(?=\n## |\n# )/i, '');
// Insert TOC after the first H1
if (content.match(/^# [^\n]+\n/)) {
    content = content.replace(/^(# [^\n]+\n+)/, `$1${toc}`);
} else {
    content = toc + content;
}
fs.writeFileSync(path, content, 'utf8');
console.log('TOC added and README updated!');
