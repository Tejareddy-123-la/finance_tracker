const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const isWin = process.platform === 'win32';
const rootDir = __dirname;
const backendDir = path.join(rootDir, 'backend');
const venvDir = path.join(backendDir, 'venv');

const uvicornExe = isWin
  ? path.join(venvDir, 'Scripts', 'uvicorn.exe')
  : path.join(venvDir, 'bin', 'uvicorn');

if (!fs.existsSync(uvicornExe)) {
  console.log('Virtual environment or uvicorn not found. Running npm install first...');
  require('./setup.js');
}

console.log('\n--- Starting Smart Personal Finance Manager ---');
console.log('App URL : http://127.0.0.1:8000');
console.log('API Docs: http://127.0.0.1:8000/docs');
console.log('Press Ctrl+C to stop the server.\n');

const child = spawn(uvicornExe, ['main:app', '--reload'], {
  cwd: backendDir,
  stdio: 'inherit',
  shell: isWin
});

child.on('exit', (code) => {
  process.exit(code || 0);
});
