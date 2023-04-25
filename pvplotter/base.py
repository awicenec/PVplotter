import os
from glob import glob
from typing import Union

import numpy as np
import pandas as pd
import typer
import datetime
from matplotlib.pylab import plt
from pandas.tseries.offsets import DateOffset

# from pvplotter.cli import state

NAME = "PVplotter"


def _check_figure(state: dict):
    fig = state["figure"]
    if fig == "":
        typer.echo("Initializing figure")
        plt.ion()
        fig = plt.figure(0)
        state["figure"] = fig
    else:
        fig.clf()
    return fig


class PVdata:
    def __init__(self, ftmpl: str = "Weekly_*.csv"):
        self.clearDays = pd.Series(dtype="datetime64[ns]")
        self.sumWh_clear = None
        self.n_days = None
        self.cloudCoverage = None
        self.cloudFilter = None
        self.dateInd: list = []
        self.slope2 = None
        self.slope = None
        self.df = pd.DataFrame()
        self.ftmpl = ftmpl
        self.sumWh = None
        self.num_reports: int = self._check_reports()
        if self.num_reports > 0:
            self.df_setter()
            self.slope_setter()
            self.sumWh_setter()
            self.cloud_setter()

    def __str__(self):
        rep = f"Number of days in reports: {self.n_days}\n"
        if self.num_reports > 0:
            rep += f"Number of clear days: {len(self.clearDays)}\n"
            rep += f"Dimmest day: {self.sumWh.idxmin()}\n"
            rep += f"Brightest day: {self.sumWh.idxmax()}\n"
        return rep

    def _check_reports(self) -> int:
        return len(glob(os.path.expanduser(self.ftmpl)))

    def df_setter(self):
        fils = glob(os.path.expanduser(self.ftmpl))
        df_list = [pd.read_csv(f, header=0, skiprows=1) for f in fils]
        if len(fils) == 0:
            return
        self.df = pd.concat(df_list)
        if len(self.df.columns) == 6:
            self.df.drop(columns=self.df.columns[5], inplace=True)
        self.df["DateTime"] = pd.to_datetime(
            self.df[self.df.columns[0]], format="%d.%m.%Y %H:%M"
        )
        self.df.set_index("DateTime", inplace=True)
        self.dateInd = np.unique(self.df.index.date)
        return

    def slope_setter(self):
        self.slope = pd.Series(
            np.gradient(self.df["[Wh]"]), self.df.index, name="slope"
        )
        self.slope2 = pd.Series(
            np.gradient(self.slope), self.slope.index, name="slope2"
        )

    def sumWh_setter(self):
        self.n_days = len(self.dateInd)
        self.sumWh = pd.Series(
            [self.df["[Wh]"][str(d)].sum() for d in self.dateInd],
            self.dateInd,
            name="sumWh",
        )

    def cloud_setter(self):
        factor = 35 / self.sumWh.max()
        filter_scale = self.sumWh * factor
        filter_scale_full = pd.Series(
            [filter_scale[d] for d in self.df.index.date], self.df.index
        )
        self.cloudFilter = np.where(np.abs(self.slope) > filter_scale_full)
        self.cloudCoverage = pd.Series(
            [
                len(np.where(np.abs(self.slope[str(d)]) > filter_scale[d])[0])
                for d in self.dateInd
            ],
            self.dateInd,
            name="coverage",
        )
        if self.cloudCoverage is not None:
            dcc = self.cloudCoverage.loc[self.cloudCoverage.le(5)]
            self.sumWh_clear = self.sumWh[dcc.index]
            self.clearDays = dcc
            self.clearDays.index = dcc.index + DateOffset(hours=12)


def plotClear(
    state: dict,
    date: Union[np.datetime64, None] = None,
) -> plt:
    pvdata = state["pvdata"]
    _ = _check_figure(state)
    dataFrame = pvdata.df
    if date is None:
        dates = pvdata.clearDays.index
    else:
        dates = [date]
    for d in dates:
        dataFrame["[Wh]"][str(d.date())].plot(
            title=str(d.date()), ylabel="[Wh]"
        )
    return state


def plotDate(state: dict, day: Union[str, None]):
    if day is None:
        return state
    state = plotMatchingDates(state, day, mflag=False)
    return state


def plotMatchingDates(
    state: dict,
    day: Union[str, None],
    mflag: bool = True,
):
    """
    Takes in a day string and optional matching bool and state dictionary.
    Plots data for selected day or range of days if matching=True and matching
    day(s) are found in the state dictionary.

    Args:
        state (Union[dict, None], optional): A dictionary containing data
                    for multiple days. Keys are formatted as 'YYYY-MM-DD'.
        day (Union[str, None]): A string indicating a day formatted as
                    'YYYY-MM-DD'. If None, today's date is used.

        mflag (bool, optional): A boolean indicating whether to search
                    for matching days in state dictionary (if provided).
                    If False, the function only plots data for the specified
                    day(s).


    Returns:
        None

    """
    if day is None:
        return state
    pvdata = state["pvdata"]
    dataFrame = pvdata.df
    _ = _check_figure(state)
    if isinstance(day, str):
        day = dataFrame.loc[day].index[0].date()
    d0 = dataFrame.at[str(day), "[Wh]"]
    t0 = pd.to_datetime(dataFrame.at[str(day), "[dd.MM.yyyy HH:mm]"])
    t0 = pd.Series(t0).dt.time
    df_t0 = pd.DataFrame(d0, index=t0, columns=[day])

    if mflag:
        m_date = (day + DateOffset(years=1)).date()
        if m_date > max(pvdata.dateInd):
            typer.echo(f"Warning: matching date ({m_date}) is in the future!")
            mflag = False
        elif m_date not in pvdata.dateInd:
            typer.echo(f"Matching date {m_date} not available!")
            mflag = False
        else:
            print(f"Comparing {day} with {m_date}")
        d1 = dataFrame.at[str(m_date), "[Wh]"]
        t1 = pd.to_datetime(dataFrame.at[str(m_date), "[dd.MM.yyyy HH:mm]"])
        t1 = pd.Series(t1).dt.time
        df_t1 = pd.DataFrame(d1, index=t1, columns=[m_date])
        title = "Year on year comparison (single day)"
    else:
        title = f"Energy production on {str(day)}"
    if not df_t0[day].isnull().values.all():
        ax = df_t0[day].plot(
            label=str(day),
            ylabel="Energy production [Wh]",
            legend=True,
            title=title,
        )
    else:
        typer.echo(f"Date {day} contains only NaN values")
    if mflag:
        if not df_t1[m_date].isnull().values.all():
            df_t1.plot(label=str(m_date), ax=ax)
        else:
            typer.echo(f"Date {m_date} contains only NaN values")

    return state


def plotDetection(state: dict):
    pvdata = state["pvdata"]
    dataFrame = pvdata.df
    _ = _check_figure(state)
    dataFrame["[Wh]"].plot()
    dataFrame.iloc[pvdata.cloudFilter]["[Wh]"].plot(style="r+")
    (pvdata.clearDays**0).plot(style="g^")
    plt.vlines(
        x=pvdata.clearDays.index,
        ymin=0,
        ymax=dataFrame["[Wh]"].max() + 50,
        color="y",
        linestyle="dashed",
    )
    plt.ylabel("[Wh]")
    return state


def plotAllClear(state: dict):
    pvdata = state["pvdata"]
    _ = _check_figure(state)
    dataFrame = pvdata.df
    t0 = dataFrame.index.min()
    for d in pvdata.clearDays.index:
        df_t0 = dataFrame["[Wh]"][str(d.date())]
        t_offset = (df_t0.index[0] - t0).days
        df_t0.index = df_t0.index - DateOffset(days=t_offset)
        df_t0.plot()
    plt.ylabel("[Wh]")
    return state
