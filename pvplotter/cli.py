"""CLI interface for pvplotter project.

Be creative! do whatever you want!

- Install click or typer and create a CLI app
- Use builtin argparse
- Start a web application
- Import things from your .base module
"""
import os.path
from glob import glob
import typer
from pvplotter import base
from base import PVdata

app = typer.Typer()

state = {"ftmpl": "*.csv", "pvdata": PVdata(ftmpl="*.csv")}


@app.command()
def interactive():
    if state["ftmpl"] == "":
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
        plot_matching()
    else:
        typer.echo(f"Unknown cmd: {cmd}")


# @app.command()
def load():
    ftmpl = os.path.expanduser(state["ftmpl"])
    typer.echo(f"Loading reports from: {ftmpl}")
    if len(glob(ftmpl)) == 0:
        print("No report file found!")
        typer.Exit()
    state["pvdata"] = base.PVdata(ftmpl)
    typer.echo(f"{state['pvdata']}")


@app.command()
def plot_detection():
    if state["pvdata"] is None:
        load()
    base.plotDetection(state["pvdata"])


@app.command()
def plot_matching(day: str):
    if state["pvdata"].num_reports == 0:
        load()
    base.plotMatchingDates(state["pvdata"], day)


@app.command()
def plot_clear():
    if state["pvdata"] is None:
        load()
    base.plotClear(state["pvdata"])


@app.command()
def plot_all_clear():
    if state["pvdata"] is None:
        load()
    base.plotAllClear(state["pvdata"])


@app.callback()
def main(ftmpl: str = "*.csv"):
    """
    Manage users in the awesome CLI app.
    """
    if ftmpl != "*.csv":
        state["ftmpl"] = ftmpl
    else:
        state["ftmpl"] = typer.prompt("Specify reports path template")
    load()
