from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium import webdriver
from datetime import datetime
import pandas

TIMEOUT = 60


def status(message):
    print(message)
    return message


def wait_until_clickable(driver: webdriver, selector: By, element: str):
    return WebDriverWait(
        driver, TIMEOUT).until(
        EC.element_to_be_clickable((selector, element))).click()


def wait_until_visible(driver: webdriver, selector: By, element: str):
    return WebDriverWait(
        driver, TIMEOUT).until(
        EC.visibility_of_element_located((selector, element)))


def wait_until_invisible(driver: webdriver, selector: By, element: str):
    return WebDriverWait(
        driver, TIMEOUT).until(
        EC.invisibility_of_element_located((selector, element)))


def loading(driver: webdriver):
    print("Loading")
    wait_until_invisible(driver, By.CSS_SELECTOR, ".fancybox-overlay")


def read_logbook_adira(filename):
    print("Reading csv file")
    df = pandas.read_csv(
        filename,
        header=6,
        names=[
            "Day",
            "DATE",
            "Working Hour",
            "Duty On Hour",
            "Duty On Minute",
            "Duty Off Hour",
            "Duty Off Minute",
            "Notes",
            "Activities",
        ],
        parse_dates=["DATE"],
        infer_datetime_format=True,
    )

    clean_col = {
        "DATE",
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


def fill_clock(driver, row):
    print("Filling clock in and out")
    clock_in = wait_until_visible(
        driver, By.CSS_SELECTOR,
        ("#logBookEditPopup > div > div > div.item-body > div > "
            "div:nth-child(2) > span > span"))
    driver.execute_script("arguments[0].click();", clock_in)

    hour = Select(driver.find_element(
        By.CSS_SELECTOR,
        ".ui_tpicker_hour_slider > select:nth-child(1)"))
    hour.select_by_value("{}".format(row["Duty On Hour"]))

    minute = Select(
        driver.find_element(
            By.CSS_SELECTOR,
            ".ui_tpicker_minute_slider > select:nth-child(1)"))
    minute.select_by_value("{}".format(row["Duty On Minute"]))

    done = wait_until_visible(
        driver, By.CSS_SELECTOR,
        ("#ui-datepicker-div > "
            "div.ui-datepicker-buttonpane.ui-widget-content > "
            "button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all"))
    driver.execute_script("arguments[0].click();", done)

    clock_out = wait_until_visible(
        driver, By.CSS_SELECTOR,
        ("#logBookEditPopup > div > div > div.item-body > div > "
            "div:nth-child(4) > span > span"))
    driver.execute_script("arguments[0].click();", clock_out)

    hour = Select(driver.find_element(
        By.CSS_SELECTOR,
        ".ui_tpicker_hour_slider > select:nth-child(1)"))
    hour.select_by_value("{}".format(row["Duty Off Hour"]))

    minute = Select(
        driver.find_element(
            By.CSS_SELECTOR,
            ".ui_tpicker_minute_slider > select:nth-child(1)"))
    minute.select_by_value("{}".format(row["Duty Off Minute"]))

    done = wait_until_visible(
        driver, By.CSS_SELECTOR,
        ("#ui-datepicker-div > "
            "div.ui-datepicker-buttonpane.ui-widget-content > "
            "button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all"))
    driver.execute_script("arguments[0].click();", done)


def fill_logbook(email, password, filename):
    opt = Options()
    opt.add_argument("--headless")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opt)

    yield status("Opening enrichment")
    driver.get("https://enrichment.apps.binus.ac.id/Login/Student/Login")

    yield status("Logging in to enrichment")
    wait_until_visible(driver, By.ID, "login_Username").send_keys(email)
    wait_until_visible(driver, By.ID, "login_Password").send_keys(password)
    wait_until_visible(driver, By.ID, "btnLogin").click()

    loading(driver)

    yield status("Opening activity enrichment")
    wait_until_clickable(driver, By.CSS_SELECTOR, "a.button:nth-child(2)")

    loading(driver)

    yield status("Opening logbook tab")
    wait_until_clickable(driver, By.CSS_SELECTOR,
                         "#btnLogBook > span:nth-child(1)")

    loading(driver)

    yield status("Parsing logbook table")
    adira = read_logbook_adira(filename)

    print("Data:")
    print(adira)

    for index, row in adira.iterrows():
        yield status("Searching for {}".format(row["DATE"]))
        isFound = False
        isGtToday = False

        try:
            table = driver.find_element(By.ID, "logBookTable")
        except StaleElementReferenceException:
            WebDriverWait(driver, TIMEOUT).until(EC.staleness_of(table))

        for tr in table.find_elements(By.XPATH, ".//tr"):
            if isFound or isGtToday:
                break

            for td in tr.find_elements(By.XPATH, ".//td[1]"):
                date = datetime.strptime(td.text, "%a, %d %b %Y")
                if date > datetime.today():
                    print("{} belom harinya".format(date))
                    isGtToday = True
                    break

                if str(row["DATE"]) == str(date):
                    print("Found {}".format(row["DATE"]))

                    isOff = False
                    if row["Notes"] == "off":
                        print("off")
                        isOff = True

                    entry = WebDriverWait(tr, TIMEOUT).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, ".dt-Action .button")
                        )
                    )
                    driver.execute_script("arguments[0].click();", entry)

                    if not isOff:
                        fill_clock(driver, row)

                        notes = WebDriverWait(driver, TIMEOUT).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "#editActivity")
                            )
                        )
                        notes.clear()
                        notes.send_keys(row["Notes"])

                        activities = WebDriverWait(driver, TIMEOUT).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "#editDescription")
                            )
                        )
                        activities.clear()
                        activities.send_keys(row["Activities"])
                    else:
                        off = WebDriverWait(
                            driver, TIMEOUT).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR,
                                 "#logBookEditPopup > div > div > div.row.text-right > a-encoded:nth-child(1)",)))
                        driver.execute_script("arguments[0].click();", off)

                    submit = WebDriverWait(
                        driver, TIMEOUT).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR,
                             "#logBookEditPopup > div > div > div.row.text-right > a-encoded:nth-child(2)",)))
                    driver.execute_script("arguments[0].click();", submit)

                    WebDriverWait(driver, TIMEOUT).until(EC.alert_is_present())
                    driver.switch_to.alert.accept()

                    loading(driver)

                    isFound = True
                    break

    driver.close()
