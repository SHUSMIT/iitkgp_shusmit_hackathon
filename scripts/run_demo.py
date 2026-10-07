from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    print('\n>', ' '.join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)

run([sys.executable, '-m', 'src.cli', 'analyze', '--input', 'data/sample_news.csv', '--output', 'runtime/demo_signals.csv', '--fallback-only'])
run([sys.executable, '-m', 'src.cli', 'stress-test', '--signals', 'runtime/demo_signals.csv', '--output', 'runtime/demo_stress.csv'])
print('\nDemo artifacts: runtime/demo_signals.csv and runtime/demo_stress.csv')
print('For the UI: streamlit run src/ui/dashboard.py')
