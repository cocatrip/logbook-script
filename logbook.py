import requests
from bs4 import BeautifulSoup
from models import Months, LogBooks
import pandas
import numpy
from datetime import datetime


def convert_time(hour, minute):
    hour = str(hour)
    minute = str(minute)
    time = "{}:{}".format(hour, minute)
    return str(
        datetime.strptime(time, "%H:%M").strftime("%I:%M %p")).lower()


def read_logbook_adira(filename):
    print("Reading csv file")
    df = pandas.read_csv(
        filename,
        header=6,
        names=[
            "Day",
            "Date",
            "Working Hour",
            "Duty On Hour",
            "Duty On Minute",
            "Duty Off Hour",
            "Duty Off Minute",
            "Notes",
            "Activities",
        ],
        infer_datetime_format=True,
    )

    # ilangin semua yang gada dates & notes
    clean_col = {
        "Date",
        "Notes"
    }

    for col in clean_col:
        df = df.drop(df.index[df[col].isnull()])

    df["Date"] = pandas.to_datetime(
        df["Date"], errors="coerce", format="%d/%m/%Y")

    df["Date"] = df["Date"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    fill_nan = {
        "Duty On Hour",
        "Duty On Minute",
        "Duty Off Hour",
        "Duty Off Minute",
    }
    for col in fill_nan:
        df[col] = df[col].replace(numpy.nan, 0)

    convert = {
        "Duty On Hour": int,
        "Duty On Minute": int,
        "Duty Off Hour": int,
        "Duty Off Minute": int,
    }

    df = df.astype(convert)

    return df


def find_by_date(logbook, date):
    try:
        return next(i for i in range(len(logbook)) if date == logbook[i].date)
    except StopIteration:
        raise ValueError(f"No matching record found for {date}")


def get_logbook_by_month(months, timestamp_list):
    logbook_header_id = []
    month_list = []

    for timestamp in timestamp_list:
        date = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
        mo = date.month
        if mo not in month_list:
            month_list.append(mo)

    for data in months.data:
        for mo in month_list:
            if data.monthInt == mo:
                logbook_header_id.append(data.logBookHeaderID)
                break
    return logbook_header_id


def fill_logbook(email, password, strm, destination):
    print(email)

    # read csv file
    df = read_logbook_adira(destination)
    if df.empty:
        yield("Empty Dataframe")
        return -1
    print(df[["Date", "Notes"]])

    # create new session
    session = requests.session()

    url = "https://enrichment.apps.binus.ac.id"

    # login
    response = session.get(url + "/Login/Student/Login")

    soup = BeautifulSoup(response.text, "html.parser")

    requestVerificationToken = soup.find(
        "input", {"name": "__RequestVerificationToken"})["value"]

    response = session.post(url + "/Login/Student/DoLogin", data={
        "login.Username": email,
        "login.Password": password,
        "btnLogin": "Login",
        "__RequestVerificationToken": requestVerificationToken,
    })

    # use strm for getting SSO to activity enrichment
    response = session.post(
        url + "/Dashboard/Student/IndexStudentDashboard",
        data={"Strm": strm, })

    # going to activity enrichment
    soup = BeautifulSoup(response.text, "html.parser")

    activity_enrichment = url + soup.find(
        "a", {"class": "button-orange"})["href"]

    response = session.get(activity_enrichment)

    url = "https://activity-enrichment.apps.binus.ac.id"

    # get all months and parse to class
    response = session.get(url + "/LogBook/GetMonths")

    months = Months(data=response.json()["data"])

    # detect which month should be filled and get the header id list
    logbook_header_id_list = get_logbook_by_month(
        months, df["Date"].unique().tolist())

    print(logbook_header_id_list)
    for logbook_header_id in logbook_header_id_list:
        # get all logbook and parse to class
        response = session.post(url + "/LogBook/GetLogBook", data={
            "logBookHeaderID": logbook_header_id
        })

        logbooks = LogBooks(data=response.json()["data"])

        print("Filling all saturday as off")
        yield("Filling all saturday as off")
        for data in logbooks.data:
            date = datetime.strptime(data.date, "%Y-%m-%dT%H:%M:%S")
            if date.strftime("%w") == "6":
                response = session.post(
                    url + "/LogBook/StudentSave",
                    data={"model[ID]": data.id,
                          "model[LogBookHeaderID]": data.logBookHeaderID,
                          "model[Date]": data.date,
                          "model[Activity]": "OFF",
                          "model[ClockIn]": "OFF",
                          "model[ClockOut]": "OFF",
                          "model[Description]": "OFF"})

                print(response.json()["status"])
                yield(response.json()["status"])

        df = read_logbook_adira(destination)
        for i in range(0, len(df)):
            id_form = None
            logbook_header_id_form = None
            date_form = None
            activity_form = None
            clockin_form = None
            clockout_form = None
            description_form = None

            index = None
            try:
                index = find_by_date(logbooks.data, df["Date"][i])
                print(index)
            except ValueError as err:
                print(str(err))
                continue

            logbook = logbooks.data
            print("Filling {}".format(logbook[index].date))
            yield("Filling {}".format(logbook[index].date))
            if df["Notes"][i].lower() in ("wfo", "wfh"):
                clock_in = convert_time(
                    df["Duty On Hour"][i],
                    df["Duty On Minute"][i])
                clock_out = convert_time(
                    df["Duty Off Hour"][i],
                    df["Duty Off Minute"][i])

                id_form = logbook[index].id
                logbook_header_id_form = logbook[index].logBookHeaderID
                date_form = logbook[index].date
                activity_form = df["Notes"][i]
                clockin_form = clock_in
                clockout_form = clock_out
                description_form = df["Activities"][i]
            elif df["Notes"][i].lower() == "off":
                id_form = logbook[index].id
                logbook_header_id_form = logbook[index].logBookHeaderID
                date_form = logbook[index].date
                activity_form = "OFF"
                clockin_form = "OFF"
                clockout_form = "OFF"
                description_form = "OFF"

            response = session.post(
                url + "/LogBook/StudentSave",
                data={"model[ID]": id_form,
                      "model[LogBookHeaderID]": logbook_header_id_form,
                      "model[Date]": date_form,
                      "model[Activity]": activity_form,
                      "model[ClockIn]": clockin_form,
                      "model[ClockOut]": clockout_form,
                      "model[Description]": description_form})

            print(response.json()["status"])
            yield(response.json()["status"])
