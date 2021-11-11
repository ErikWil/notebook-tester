from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import nbformat
from typing import Optional
import typer
import zlib

from notebooktester import ERRORS, __app_name__, __version__, NOTEBOOK_NOT_FOUND, NOTEBOOK_JSON_ERROR, IO_ERROR, INIT_ALLREADY_DONE

app = typer.Typer()


def get_notebook(filename:str, notebook_version:int=4, action='verify'):
    try:
        with open(filename, 'r') as f:
            try:
                return nbformat.read(f, as_version=notebook_version)
            except:
                raise typer.Exit(NOTEBOOK_JSON_ERROR)
    except:
        raise typer.Exit(NOTEBOOK_NOT_FOUND)

def getresult(cell):
    for output in  cell['outputs']:
        result_type = output['output_type']
        if result_type in ('display_data', 'execute_result'):
            value = output['data']
        elif result_type == 'error':
            value = [output['ename'], output['evalue']]
        else:
            print(f"Unknown result type {result_type}")
            continue
        yield {'type':result_type, 'value':value}

def get_directive(cell):
    if source := cell.get('source'):
        source = source.lstrip()
        if source.startswith('#test-case:'):
            directive, code = source.split(maxsplit=1)
            return directive.split(':',1)[1], code

def crc(cell):
    return zlib.crc32(cell['source'].encode('utf-8'))

@app.command()
def init(notebookfile: str, trim_test_directive:bool=False, force:bool=False):
    nb = get_notebook(notebookfile)
    for cell in nb['cells']:
        if code_info := get_directive(cell):
            if cell['metadata'].get('test-case') and not force:
                raise typer.Exit(INIT_ALLREADY_DONE)
            test_name, code = code_info
            cell_result = list(getresult(cell))

            cell['metadata']['test-case'] = dict(name=test_name, result=cell_result, crc=crc(cell))

            if trim_test_directive:
                cell['source']=code
    try:
        with open(notebookfile, "w") as f:
            nbformat.write(nb,f)
    except:
        raise typer.Exit(IO_ERROR)

@app.command()
def test(notebookfile: str, kernel_name:str='python3', notebook_version:int=4, timeout:int=600, report_result:bool=True, report_file:str=None):
    with open(notebookfile) as f:
        nb = nbformat.read(f, as_version=notebook_version)
        exec_proc = ExecutePreprocessor(timeout=timeout, allow_errors=True)

        run_meta = dict(metadata=dict(path='.'))
        try:
            result = exec_proc.preprocess(nb, run_meta)[0]
            for cell in result['cells']:
                if cell['cell_type'] == 'code':
                    metadata = cell['metadata'].get('test-case')
                    if metadata:
                        if crc(cell) != metadata['crc']:
                            print('Warning: cell has been changed since INIT')
                        actual = list(getresult(cell))
                        expected = metadata['result']
                        if actual != expected:
                            print(f"{metadata['name']} result mismatch {actual}, {expected}")
                        else:
                            print("report exeuction time here")

        except CellExecutionError:
            raise typer.Exit()


def _ver_cb(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", "-v", help="Show the application's version and exit.", callback=_ver_cb, is_eager=True, )
        ) -> None:
    return