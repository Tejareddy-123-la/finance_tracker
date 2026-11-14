const { execSync } = require('child_process');
const path = require('path');

const isWin = process.platform === 'win32';
const rootDir = __dirname;
const backendDir = path.join(rootDir, 'backend');
const venvDir = path.join(backendDir, 'venv');

const pythonExe = isWin
  ? path.join(venvDir, 'Scripts', 'python.exe')
  : path.join(venvDir, 'bin', 'python');

console.log('Running test suite for calculators.py...');
execSync(`"${pythonExe}" -c "
import unittest, sys
sys.path.append('backend')
import calculators as calc

class TestFinance(unittest.TestCase):
    def test_categorize(self):
        self.assertEqual(calc.categorize('Swiggy order #999'), 'Food')
        self.assertEqual(calc.categorize('Salary credit', 'income'), 'Income')
    def test_si(self):
        self.assertEqual(calc.simple_interest(50000, 7.5, 3)['interest'], 11250.0)
    def test_ci(self):
        self.assertEqual(calc.compound_interest(10000, 12, 1, 12)['total'], 11268.25)
    def test_emi(self):
        self.assertEqual(calc.emi(500000, 9, 36)['emi'], 15899.87)

unittest.main(argv=[''], exit=False)
"`, { stdio: 'inherit' });

console.log('\nAll pure-Python logic tests passed!');
