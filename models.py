from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel

import datetime


class Month(BaseModel):
    month: str
    logBookHeaderID: str
    isWarning: bool
    countData: int
    monthInt: int
    isCurrentMonth: bool
    strm: str
    notice: str
    validationMC: bool
    year: Any


class Months(BaseModel):
    data: Optional[List[Month]] = None


class LogBook(BaseModel):
    id: str
    logBookHeaderID: str
    date: str
    clockIn: str
    clockOut: str
    activity: str
    description: str
    acceptanceID: int
    acceptance: str
    status: Optional[str]
    commentSS: Any
    commentFS: Any
    flagjulyactive: bool


class LogBooks(BaseModel):
    data: Optional[List[LogBook]] = None
    filledReject: Optional[int] = None
    filledEntry: Optional[int] = None
    filledSubmit: Optional[int] = None
    filledEmpty: Optional[int] = None
    filledAppSS: Optional[int] = None
    filledAppFS: Optional[int] = None
    filledAll: Optional[int] = None
    filledRejectFS: Optional[int] = None
    filledEntryFS: Optional[int] = None
    curmonth: Optional[str] = None
    filled: Optional[int] = None
    aid: Optional[int] = None
    fscount: Optional[bool] = None
    fssbtcount: Optional[bool] = None
    sbtcount: Optional[bool] = None
    appcount: Optional[bool] = None
    fsRjtSbmt: Optional[bool] = None
    cnd: Optional[str] = None
    feedb: Optional[Any] = None
    flagjulyactive: Optional[bool] = None
    validateincompletelogbook: Optional[int] = None
    validateincompletePreviouslogbook: Optional[bool] = None
    trackId: Optional[str] = None
    sbtcountMC: Optional[bool] = None
