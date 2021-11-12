from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
import nbformat
from typing import Optional
import typer
import zlib

from typer.params import Argument, Option

from notebooktester import ERRORS, __app_name__, __version__, NOTEBOOK_NOT_FOUND, NOTEBOOK_JSON_ERROR, IO_ERROR, INIT_ALLREADY_DONE, PROCESSING_FAILURE

app = typer.Typer()


def get_notebook(filename:str, notebook_version:int=4, action='verify'):
    try:
        with open(filename, 'r') as f:
            try:
                return nbformat.read(f, as_version=notebook_version)
            except:
                exit(NOTEBOOK_JSON_ERROR)
    except:
        exit(NOTEBOOK_NOT_FOUND)

def getresult(cell):
    for output in  cell.outputs:
        result_type = output.output_type
        if result_type in ('display_data', 'execute_result'):
            value = output.data
        elif result_type == 'error':
            value = [output.ename, output.evalue]
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
    return zlib.crc32(cell.source.encode('utf-8'))

def exit(code:int):
    msg = ERRORS.get(code) or f"Exit with code={code}"
    typer.echo(msg)
    raise typer.Exit(code)


@app.command()
def init(
        notebookfile: str = Argument(..., help="The notebook to be tested "),  
        trim_test_directive:bool = Option(False, help="Remove the #test-case directive from the source cell"), 
        force:bool = Option(False, help="Force an update to metadata."),
        lock_cells:bool = Option(False, help="Make the test-case cells read-only"),
        ignore_existing:bool = Option(False, help="Ignore cells that allready have been tagged for testing"),


    ):
    """
    Initialize the notebook for testing. Each cell that has the #test-case directive set will have the current
    result of the calculations recorded in the cell metadata. The current crc32 fingerprint of the source code is 
    also recorded. The notebook is modified from original, but the visible content remains the same.

    If you attempt to run INIT on a cell that allready has been initialized, the command will fail. This can be
    overridden with the --force option. In that case the metadata of the notebook will be updated.

    If the --trim_test_directive is issued, the #test-case directive in the code is removed.

    The --lock directive will add fields to the metadata that makes the test-cells read only in many
    notebook editors.
    """

    nb = get_notebook(notebookfile)
    for cell in nb.cells:
        if code_info := get_directive(cell):
            test_name, code = code_info

            if current_test := cell.metadata.get('test-case'):
                if ignore_existing:
                    typer.echo(f"test {test_name} not updated")
                    continue
                elif not force:
                    exit(INIT_ALLREADY_DONE)

            cell_result = list(getresult(cell))

            cell.metadata['test-case'] = dict(name=test_name, result=cell_result, crc=crc(cell))
            cell.metadata["editable"] = not lock_cells
            cell.metadata["deletable"] = not lock_cells

            if trim_test_directive:
                cell.source = code
    try:
        with open(notebookfile, "w") as f:
            nbformat.write(nb,f)
    except:
        exit(IO_ERROR)

@app.command()
def test(
        notebookfile: str = Argument(..., help="The notebook to be tested "), 
        kernel_name:str = Option('python3', help="The kernel jupyter will use to evaluate this notebook"),
        notebook_version:int=Option(4, help="The notebook version used"),
        timeout:int= Option(600, help="The calcuation timeout in seconds"),
        verbose:int=Option(0, help="Verbosity of the output 0..3"),
        report_file:str=Option(None, help="A file where the output should be stored. Default is to the screen"),
        strict_consistency:bool = Option(False, help="Terminate execution if any cell has been tampered with"),
        ):
    """
    Run a notebook and compare the calculated results against the stored results. Report any deviation. If the
    notebook source has been changed, there will be an warning issued.

    The notebook will not change. 
    """


    with open(notebookfile) as f:
        nb = nbformat.read(f, as_version=notebook_version)
        exec_proc = ExecutePreprocessor(timeout=timeout, allow_errors=True)

        run_meta = dict(metadata=dict(path='.'))
        try:
            result = exec_proc.preprocess(nb, run_meta)[0]
            for cell in result.cells:
                if cell.cell_type == 'code':
                    metadata = cell.metadata.get('test-case')
                    if metadata:
                        if crc(cell) != metadata.crc:
                            print('Warning: cell has been changed since INIT')
                        actual = list(getresult(cell))
                        expected = metadata.result
                        if actual != expected:
                            print(f"{metadata.name} result mismatch {actual}, {expected}")
                        else:
                            print("report exeuction time here")

        except CellExecutionError:
            exit(PROCESSING_FAILURE)


def _ver_cb(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(None, "--version", "-v", help="Show the application's version and exit.", callback=_ver_cb, is_eager=True, )
        ) -> None:
    return