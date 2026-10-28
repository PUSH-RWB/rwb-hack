"""Execute the EDA notebook and export a standalone HTML report."""
from pathlib import Path
import json
import os
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'model' / '.cache'
for variable, directory in {
    'MPLCONFIGDIR': CACHE / 'matplotlib',
    'IPYTHONDIR': CACHE / 'ipython',
    'JUPYTER_RUNTIME_DIR': CACHE / 'runtime',
}.items():
    directory.mkdir(parents=True, exist_ok=True)
    os.environ[variable] = str(directory)
jupyter_dir = CACHE / 'jupyter'
kernel_dir = jupyter_dir / 'kernels' / 'capibara-eda'
kernel_dir.mkdir(parents=True, exist_ok=True)
(kernel_dir / 'kernel.json').write_text(json.dumps({
    'argv': [sys.executable, '-B', '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
    'display_name': 'Capibara EDA', 'language': 'python',
}), encoding='utf-8')
os.environ['JUPYTER_PATH'] = str(jupyter_dir) + (os.pathsep + os.environ['JUPYTER_PATH'] if os.environ.get('JUPYTER_PATH') else '')

import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter

notebook_path = ROOT / 'model' / 'notebooks' / '01_eda.ipynb'
notebook = nbformat.read(notebook_path, as_version=4)
started = time.perf_counter()
print('Executing notebook with', sys.executable, flush=True)
client = NotebookClient(notebook, timeout=240, kernel_name='capibara-eda',
                        resources={'metadata': {'path': str(ROOT)}}, allow_errors=False)
client.execute()
nbformat.validate(notebook)
nbformat.write(notebook, notebook_path)
exporter = HTMLExporter(template_name='lab', exclude_input=True,
                        exclude_input_prompt=True, exclude_output_prompt=True)
body, resources = exporter.from_notebook_node(notebook)
body = body.replace('</head>', '''<style>
body {background:#F4F6FA!important;color:#263247}
.jp-Notebook {max-width:1220px;margin:28px auto;padding:38px!important;background:white;border-radius:16px}
.jp-RenderedHTMLCommon h1 {font-size:34px;color:#5634AB}
.jp-RenderedHTMLCommon h2 {margin-top:40px;border-bottom:1px solid #E5E9F0;padding-bottom:12px}
.jp-OutputArea-output {overflow-x:auto}
@media print {body{background:white!important}.jp-Notebook{margin:0;padding:0!important}h2{break-after:avoid}img{break-inside:avoid}}
</style></head>''')
html_path = ROOT / 'model' / 'reports' / '01_eda.html'
html_path.write_text(body, encoding='utf-8')
code_cells = [cell for cell in notebook.cells if cell.cell_type == 'code']
errors = [out for cell in code_cells for out in cell.get('outputs', []) if out.output_type == 'error']
inline_images = sum('image/png' in out.get('data', {}) for cell in code_cells for out in cell.get('outputs', []))
if inline_images < 9:
    raise RuntimeError(f'Expected 9 embedded figures, got {inline_images}')
if errors or any(cell.execution_count is None for cell in code_cells):
    raise RuntimeError('Notebook execution is incomplete')
summary = {'code_cells': len(code_cells), 'errors': len(errors),
           'embedded_figures': inline_images,
           'png_figures': len(list((ROOT / 'model' / 'reports' / 'figures').glob('*.png'))),
           'seconds': round(time.perf_counter() - started, 2),
           'notebook': 'model/notebooks/01_eda.ipynb', 'html': 'model/reports/01_eda.html'}
(ROOT / 'model' / 'reports' / 'execution_summary.json').write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
