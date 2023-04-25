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
import typer
from rich import print as rprint
import datetime
import os.path
from typing import Union, cast, Callable, TypedDict, Iterable

import matplotlib.pyplot as plt

from pvplotter import base
from pvplotter.base import PVdata

DEFAULT_FTMPL = "Weekly_*.csv"

app = typer.Typer(no_args_is_help=True)

state = {
    "ftmpl": DEFAULT_FTMPL,
    "pvdata": PVdata(),
    "num_reports": PVdata().num_reports,
    "figure": "",
}


def _enter_date_format(day: str) -> str:
    """
    Helper function to enter a date in the required format
    Args:
        day: str: A date in the format 'YYYY-MM-DD'

    Returns:
        day: str

    """
    min_date = state["pvdata"].dateInd.min()
    max_date = state["pvdata"].dateInd.max()

    while True:
        if day == "" or isinstance(day, typer.models.ArgumentInfo):
            day = typer.prompt(
                f"Specify initial date between {str(min_date)} and {str(max_date)} (or 'q' to quit)"
            ).lower()
        if day == "q":
            return ""
        try:
            datetime.datetime.strptime(day, "%Y-%m-%d")
        except (ValueError, TypeError):
            rprint("[red]Invalid date format![/red] Try 'YYYY-MM-DD'")
            return ""
        day_date = datetime.date.fromisoformat(day)
        if day_date >= min_date and day_date <= max_date:
            return str(day)
        elif day_date < min_date or day_date > max_date:
            rprint(
                f"[red]Specified date {day_date} outside range {min_date} to {max_date}[/red]"
            )
            day = ""

        elif day_date not in state["pvdata"].dateInd:
            rprint(f"[red]Date {day} is not available![/red]")
            day = ""


def _load(ftmpl: str = DEFAULT_FTMPL):
    global state
    if ftmpl != DEFAULT_FTMPL and state["ftmpl"] == DEFAULT_FTMPL:
        state["ftmpl"] = ftmpl
    elif state["ftmpl"] != DEFAULT_FTMPL:
        ftmpl = str(state["ftmpl"])
    while state["num_reports"] == 0 and state["ftmpl"] not in [
        "q",
        "Q",
    ]:
        ftmpl = os.path.expanduser(str(state["ftmpl"]))
        rprint(f"Loading reports from: {ftmpl}")
        pvdata = PVdata(ftmpl)
        state["pvdata"] = pvdata
        state["num_reports"] = pvdata.num_reports
        if state["num_reports"] == 0:
            rprint(
                f"[red]No reports found using path: {state['ftmpl']}![/red]"
            )
            state["ftmpl"] = typer.prompt(
                "Specify reports path template or 'q' to quit"
            )
    if state["ftmpl"] in ["q", "Q"]:
        rprint("[red]No reports found![/red]")
        raise typer.Exit()


@app.command()
def load(ftmpl: str = DEFAULT_FTMPL):
    """
    Load the reports using a wildcard string.
    """
    _load(ftmpl)
    interactive(None)


@app.command()
def detection():
    """
    Show the complete dataset with indication of the clear day detection
    filter.
    """
    global state
    if state["num_reports"] == 0:
        _load()
    state = base.plotDetection(state)  # type: ignore
    interactive(None)


@app.command()
def date(
    day: str = typer.Argument(
        None,
        help="A string indicating a day formatted as 'YYYY-MM-DD'. "
        + "If None, today's date is used.",
    )
):
    """
    Show a single day by specifying a date.

    Args:
        day (Union[str, None]): A string indicating a day formatted as
                    'YYYY-MM-DD'. If None, today's date is used.

    """
    if day is None:
        day = _enter_date_format()
    matching(day, mflag=False)


@app.command()
def matching(day: str = "", mflag: bool = True):
    """
    Show one day and the same day one year later in a single plot.
    """
    global state
    if state["num_reports"] == 0:  # type: ignore
        _load()
    day = _enter_date_format(day)
    state = base.plotMatchingDates(state, day, mflag=mflag)  # type: ignore
    interactive(None)


@app.command()
def clear():
    """
    Plot clear days in a loop.
    """
    global state
    if state["num_reports"] == 0:
        _load()
    dates = state["pvdata"].clearDays.index
    rprint(f"Cycling through {len(dates)} clear days")
    for d in dates:
        rprint(f"Plotting {str(d.date())}")
        state = base.plotClear(state, date=d)
        cmd = typer.prompt(
            "Sub-commands of clear: [c]ontinue or [q]uit, default:",
            default="c",
        ).lower()
        if cmd == "q":
            plt.clf()
            interactive(None)
        else:
            plt.clf()
    interactive(None)


@app.command()
def all_clear():
    """
    Show all clear days on a single plot.
    """
    global state
    if state["num_reports"] == 0:
        _load()
    base.plotAllClear(state)
    interactive(None)


@app.callback()
def main(ftmpl: str = DEFAULT_FTMPL):
    """
    CLI app for the analysis of Fronius PV energy production reports.
    """
    global state
    state["ftmpl"] = ftmpl


class CMDclass(TypedDict):
    display: str
    abbrev: str
    function: Callable


CMDS = {}
CMDS["detection"]: CMDclass = {  # type: ignore
    "display": "[d]etection",
    "abbrev": "d",
    "function": detection,
}
CMDS["date"]: CMDclass = {  # type: ignore
    "display": "[da]te",
    "abbrev": "da",
    "function": date,
}
CMDS["matching"]: CMDclass = {  # type: ignore
    "display": "[m]atching",
    "abbrev": "m",
    "function": matching,
}
CMDS["clear"]: CMDclass = {  # type: ignore
    "display": "[c]lear",
    "abbrev": "c",
    "function": clear,
}
CMDS["all-clear"]: CMDclass = {  # type: ignore
    "display": "[a]ll-clear",
    "abbrev": "a",
    "function": all_clear,
}
CMDS["quit"]: CMDclass = {  # type: ignore
    "display": "[q]uit",
    "abbrev": "q",
    "function": lambda a: 1,
}


def interactive(cmd: Union[str, None]):
    cmds: Iterable[str] = [str(c["display"]) for c in CMDS.values()]
    if cmd is None:
        print(f"available commands: {', '.join(cmds)}.")
        cmd = typer.prompt("Specify plot command").lower()
        if cmd.lower() in ["q", "quit"]:
            raise typer.Exit()
    if state["num_reports"] == 0:
        _load()
    exec_fl = False
    while cmd != "q":
        for CMD, val in CMDS.items():
            if cmd in [CMD, val["abbrev"]]:
                plt.clf()
                cast(Callable, val["function"])()
                exec_fl = True
                plt.show()
        if not exec_fl:
            rprint(f"[red]Unknown cmd:[/red] {cmd}")
            interactive(None)
        # cmd = ""
        # cmd = typer.prompt("Additional plot command, or 'q' to quit").lower()
        plt.clf()
    raise typer.Exit()


if __name__ == "__main__":
    app()
