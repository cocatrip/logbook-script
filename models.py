from __future__ import annotations
from typing import Any, List, Optional
from pydantic import BaseModel


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
