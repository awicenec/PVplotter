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
from typing import Union
import datetime
import re

DEFAULT_FTMPL = "Weekly_*.csv"

app = typer.Typer()
pvdata = PVdata()
state = {"ftmpl": DEFAULT_FTMPL, "pvdata": pvdata}


def _enter_date_format(day: Union[str, None] = None):
    while True:
        if day is None:
            day = typer.prompt("Specify initial date (or 'q' to quit)").lower()
        if day == "q":
            return None
        try:
            datetime.datetime.strptime(day, "%Y-%m-%d")
            return day
        except ValueError:
            typer.echo("Invalid date format! Try 'YYYY-MM-DD'")
            day = None


@app.command()
def interactive():
    load()
    typer.echo(f"available commands: {', '.join(CMDS)}.")
    cmd = typer.prompt("Specify plot command").lower()
    exec_fl = False
    while cmd != "q":
        for c_full, (c_list, c_func) in CMDS.items():
            if cmd in c_list:
                c_func()
                exec_fl = True
        if not exec_fl:
            typer.echo(f"Unknown cmd: {cmd}")
        cmd = ""
        cmd = typer.prompt("Additional plot command, or 'q' to quit").lower()


# @app.command()
def load():
    while state["pvdata"].num_reports == 0 and state["ftmpl"] not in [
        "q",
        "Q",
    ]:
        ftmpl = os.path.expanduser(state["ftmpl"])
        typer.echo(f"Loading reports from: {ftmpl}")
        state["pvdata"] = PVdata(ftmpl)
        if state["pvdata"].num_reports == 0:
            typer.echo(f"No reports found using path: {state['ftmpl']}!")
            state["ftmpl"] = typer.prompt("Specify reports path template")
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
def plot_matching(day: Union[str, None] = None):
    day = _enter_date_format()
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


CMDS = {
    "[d]etection": [["d", "detection"], plot_detection],
    "[m]atching": [["m", "matching"], plot_matching],
    "[c]lear": [["c", "clear"], plot_clear],
    "[a]ll-clear": [["a", "all-clear"], plot_all_clear]
}
