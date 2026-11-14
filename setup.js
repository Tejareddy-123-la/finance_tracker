const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const isWin = process.platform === 'win32';
const rootDir = __dirname;
const venvDir = path.join(rootDir, 'backend', 'venv');
const reqFile = path.join(rootDir, 'backend', 'requirements.txt');

function run(cmd, opts = {}) {
  console.log(`> ${cmd}`);
  execSync(cmd, { stdio: 'inherit', ...opts });
}

function getPythonCmd() {
  const candidates = isWin ? ['python', 'py'] : ['python3', 'python'];
  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      return cmd;
    } catch (e) {}
  }
  return isWin ? 'python' : 'python3';
}

console.log('--- Setting up Smart Personal Finance Manager ---');
const pythonCmd = getPythonCmd();

if (!fs.existsSync(venvDir)) {
  console.log(`Creating Python virtual environment in ${venvDir}...`);
  run(`${pythonCmd} -m venv "${venvDir}"`);
} else {
  console.log(`Virtual environment already exists in ${venvDir}.`);
}

const pipExe = isWin
  ? path.join(venvDir, 'Scripts', 'pip.exe')
  : path.join(venvDir, 'bin', 'pip');

console.log(`Installing Python dependencies from ${reqFile}...`);
run(`"${pipExe}" install -r "${reqFile}"`);

console.log('\n--- Setup Complete! ---');
console.log('You can now run: npm start');
console.log('App will be available at: http://127.0.0.1:8000');
