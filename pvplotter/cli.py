"""CLI interface for pvplotter project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
TODO: Error handling when CSV content wrong
TODO: Documentation update
TODO: Quit option in plot_clean
"""
import os.path

from pvplotter import base
from pvplotter.base import PVdata
import typer

DEFAULT_FTMPL = "Weekly_*.csv"
app = typer.Typer()
pvdata = PVdata()
state = {"ftmpl": DEFAULT_FTMPL, "pvdata": pvdata}


@app.command()
def interactive():
    if state["ftmpl"] == DEFAULT_FTMPL:
        state["ftmpl"] = typer.prompt("Specify reports directory.")
    load()
    cmd = typer.prompt("Specify plot command.")
    if cmd == "detection":
        plot_detection()
    elif cmd == "clear":
        plot_clear()
    elif cmd == "all-clear":
        plot_all_clear()
    elif cmd == "matching":
        plot_matching(day="2021-08-15")
    else:
        typer.echo(f"Unknown cmd: {cmd}")


# @app.command()
def load():
    ftmpl = os.path.expanduser(state["ftmpl"])
    typer.echo(f"Loading reports from: {ftmpl}")
    state["pvdata"] = PVdata(ftmpl)
    while state["pvdata"].num_reports == 0 and state["ftmpl"] not in [
        "q",
        "Q",
    ]:
        typer.echo(f"No reports found using template: {state['ftmpl']}!")
        state["ftmpl"] = typer.prompt("Specify reports path template")
        ftmpl = os.path.expanduser(state["ftmpl"])
        typer.echo(f"Loading reports from: {ftmpl}")
        state["pvdata"] = PVdata(ftmpl)
    if state["ftmpl"] in ["q", "Q"]:
        typer.echo("No reports found!")
        raise typer.Exit()
    typer.echo(f"{state['pvdata']}")


@app.command()
def plot_detection():
    if state["pvdata"].num_reports == 0:
        typer.echo("No reports found!")
        raise typer.Exit()
    base.plotDetection(state["pvdata"])


@app.command()
def plot_matching(day: str):
    if state["pvdata"].num_reports == 0:  # type: ignore
        load()
    base.plotMatchingDates(day, state["pvdata"])  # type: ignore


@app.command()
def plot_clear():
    if state["pvdata"].num_reports == 0:
        load()
    base.plotClear(state["pvdata"])


@app.command()
def plot_all_clear():
    if state["pvdata"].num_reports == 0:
        load()
    base.plotAllClear(state["pvdata"])


@app.callback()
def main(ftmpl: str = DEFAULT_FTMPL):
    """
    Manage users in the awesome CLI app.
    """
    if ftmpl != DEFAULT_FTMPL:
        state["ftmpl"] = ftmpl
    load()
