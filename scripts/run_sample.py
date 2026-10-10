from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print('\n>', ' '.join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

run([sys.executable, '-m', 'src.cli', 'analyze', '--input', 'data/sample_news.csv', '--output', 'runtime/sample_signals.csv', '--lexical-only'])
run([sys.executable, '-m', 'src.cli', 'stress-test', '--signals', 'runtime/sample_signals.csv', '--output', 'runtime/sample_stress.csv'])
print('\nOutput files: runtime/sample_signals.csv and runtime/sample_stress.csv')
print('For the UI: streamlit run src/ui/dashboard.py')
