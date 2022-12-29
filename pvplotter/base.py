import os
from glob import glob
from typing import Union

import numpy as np
import pandas as pd
from matplotlib.pylab import plt
from pandas.tseries.offsets import DateOffset

NAME = "PVplotter"


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
        self.num_reports = self._check_reports()
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

    def _check_reports(self):
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


def plotClear(pvdata: PVdata):
    dataFrame = pvdata.df
    dates = pvdata.clearDays.index
    for d in dates:
        dataFrame["[Wh]"][str(d.date())].plot(
            title=str(d.date()), ylabel="[Wh]"
        )
        plt.show()


def plotMatchingDates(date: Union[str, None], pvdata: PVdata):
    """
    Plots the data from a single day and the data from the
    matching day one year later.
    """
    dataFrame = pvdata.df
    if isinstance(date, str):
        date = dataFrame.loc[date].index[0].date()
    d0 = dataFrame.at[str(date), "[Wh]"]
    t0 = pd.to_datetime(dataFrame.at[str(date), "[dd.MM.yyyy HH:mm]"])
    t0 = pd.Series(t0).dt.time
    df_t0 = pd.DataFrame(d0, index=t0, columns=[date])

    m_date = date + DateOffset(years=1)
    if m_date > pd.Timestamp(max(pvdata.dateInd)):
        print(f"Warning: matching date ({m_date.date()}) is in the future!")
    else:
        print(f"Comparing {date} with {m_date.date()}")
    new_date = (date + DateOffset(years=1)).date()
    d1 = dataFrame.at[str(new_date), "[Wh]"]
    t1 = pd.to_datetime(dataFrame.at[str(new_date), "[dd.MM.yyyy HH:mm]"])
    t1 = pd.Series(t1).dt.time
    df_t1 = pd.DataFrame(d1, index=t1, columns=["[Wh]"])
    ax = df_t0.plot(label=date)
    ax.plot(df_t1, label=str(new_date))
    plt.ylabel("[Wh]")
    plt.legend()
    plt.show()


def plotDetection(pvdata: PVdata):
    dataFrame = pvdata.df
    dataFrame["[Wh]"].plot()
    dataFrame.iloc[pvdata.cloudFilter]["[Wh]"].plot(style="r+")
    (pvdata.clearDays ** 0).plot(style="g^")
    plt.vlines(
        x=pvdata.clearDays.index,
        ymin=0,
        ymax=dataFrame["[Wh]"].max() + 50,
        color="y",
        linestyle="dashed",
    )
    plt.ylabel("[Wh]")
    plt.show()


def plotAllClear(pvplot: PVdata):
    dataFrame = pvplot.df
    t0 = dataFrame.index.min()
    for d in pvplot.clearDays.index:
        df_t0 = dataFrame["[Wh]"][str(d.date())]
        t_offset = (df_t0.index[0] - t0).days
        df_t0.index = df_t0.index - DateOffset(days=t_offset)
        df_t0.plot()
    plt.ylabel("[Wh]")
    plt.show()
