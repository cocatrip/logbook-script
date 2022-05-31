import requests
from bs4 import BeautifulSoup
from models import Months, LogBooks
import pandas
import datetime


def convert_time(hour, minute):
    hour = str(hour)
    minute = str(minute)
    time = "{}:{}".format(hour, minute)
    return str(
        datetime.datetime.strptime(time, "%H:%M").strftime("%I:%M %p")).lower()


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
        parse_dates=["Date"],
        infer_datetime_format=True,
    )

    clean_col = {
        "Date",
        "Duty On Hour",
        "Duty On Minute",
        "Duty Off Hour",
        "Duty Off Minute",
    }
    for col in clean_col:
        df = df.drop(df.index[df[col].isnull()])

    convert = {
        "Duty On Hour": int,
        "Duty On Minute": int,
        "Duty Off Hour": int,
        "Duty Off Minute": int,
    }

    df = df.astype(convert)

    return df


def fill_logbook(email, password, destination):
    df = read_logbook_adira(destination)

    session = requests.session()

    url = "https://enrichment.apps.binus.ac.id"

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

    soup = BeautifulSoup(response.text, "html.parser")

    strm = soup.find("option")["value"]

    response = session.post(
        url + "/Dashboard/Student/IndexStudentDashboard",
        data={"Strm": strm, })

    soup = BeautifulSoup(response.text, "html.parser")

    activity_enrichment = url + soup.find_all("a",
                                              {"class": "button"})[1]["href"]

    response = session.get(activity_enrichment)

    url = "https://activity-enrichment.apps.binus.ac.id"

    response = session.get(url + "/LogBook/GetMonths")

    months = Months(data=response.json()["data"])

    logbook_header_id = ""
    for data in months.data:
        if data.isWarning is True:
            logbook_header_id = data.logBookHeaderID
            break
        elif data.isCurrentMonth is True:
            logbook_header_id = data.logBookHeaderID
            break

    response = session.post(url + "/LogBook/GetLogBook", data={
        "logBookHeaderID": logbook_header_id
    })

    logbooks = LogBooks(data=response.json()["data"])

    # print(df)

    print("Filling all saturday as off")
    yield("Filling all saturday as off")
    for data in logbooks.data:
        date = datetime.datetime.strptime(
            data.date, "%Y-%m-%dT%H:%M:%S")
        if date.strftime("%w") == "6":
            id_form = data.id
            logbook_header_id_form = data.logBookHeaderID
            date_form = data.date
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

    for i in range(0, len(df)):
        id_form = None
        logbook_header_id_form = None
        date_form = None
        activity_form = None
        clockin_form = None
        clockout_form = None
        description_form = None
        for data in logbooks.data:
            date = datetime.datetime.strptime(
                data.date, "%Y-%m-%dT%H:%M:%S")
            if df["Date"][i] == date:
                print("Filling {}".format(data.date))
                yield("Filling {}".format(data.date))
                if df["Notes"][i].lower() in ("wfo", "wfh"):
                    clock_in = convert_time(
                        df["Duty On Hour"][i],
                        df["Duty On Minute"][i])
                    clock_out = convert_time(
                        df["Duty Off Hour"][i],
                        df["Duty Off Minute"][i])

                    id_form = data.id
                    logbook_header_id_form = data.logBookHeaderID
                    date_form = data.date
                    activity_form = df["Notes"][i]
                    clockin_form = clock_in
                    clockout_form = clock_out
                    description_form = df["Activities"][i]
                elif df["Notes"][i].lower() == "off":
                    id_form = data.id
                    logbook_header_id_form = data.logBookHeaderID
                    date_form = data.date
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
