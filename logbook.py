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

def wait_loading(driver):
    # wait for pop up to be visible
    print("waiting overlay to close")
    WebDriverWait(driver, TIMEOUT).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, ".fancybox-overlay"))
    )


def read_logbook_adira(filename):
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

    fill_nan = {
        "Working Hour",
        "Duty On Hour",
        "Duty On Minute",
        "Duty Off Hour",
        "Duty Off Minute",
    }
    for col in fill_nan:
        df[col] = pandas.to_numeric(df[col], errors="coerce").fillna(0)

    convert = {
        "Duty On Hour": int,
        "Duty On Minute": int,
        "Duty Off Hour": int,
        "Duty Off Minute": int,
    }

    df = df.astype(convert)

    return df


def fill_clock(row, driver):
    clock_in = WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                "#logBookEditPopup > div > div > div.item-body > div > div:nth-child(2) > span > span",
            )
        )
    )
    driver.execute_script("arguments[0].click();", clock_in)

    hour = Select(
        driver.find_element(
            By.CSS_SELECTOR, ".ui_tpicker_hour_slider > select:nth-child(1)"
        )
    )
    hour.select_by_value("{}".format(row["Duty On Hour"]))

    minute = Select(
        driver.find_element(
            By.CSS_SELECTOR, ".ui_tpicker_minute_slider > select:nth-child(1)"
        )
    )
    minute.select_by_value("{}".format(row["Duty On Minute"]))

    done = WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                "#ui-datepicker-div > div.ui-datepicker-buttonpane.ui-widget-content > button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all",
            )
        )
    )
    driver.execute_script("arguments[0].click();", done)

    clock_out = WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                "#logBookEditPopup > div > div > div.item-body > div > div:nth-child(4) > span > span",
            )
        )
    )
    driver.execute_script("arguments[0].click();", clock_out)

    hour = Select(
        driver.find_element(
            By.CSS_SELECTOR, ".ui_tpicker_hour_slider > select:nth-child(1)"
        )
    )
    hour.select_by_value("{}".format(row["Duty Off Hour"]))

    minute = Select(
        driver.find_element(
            By.CSS_SELECTOR, ".ui_tpicker_minute_slider > select:nth-child(1)"
        )
    )
    minute.select_by_value("{}".format(row["Duty Off Minute"]))

    done = WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                "#ui-datepicker-div > div.ui-datepicker-buttonpane.ui-widget-content > button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all",
            )
        )
    )
    driver.execute_script("arguments[0].click();", done)


def fill_logbook(email, password, filename):
    opt = Options()
    opt.add_argument("--headless")
    opt.add_argument("--disable-gpu")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=opt)

    print("USER: " + email)

    print("opening enrichment website")
    driver.get("https://enrichment.apps.binus.ac.id/Login/Student/Login")

    print("logging in")
    WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "login_Username"))
    ).send_keys(email)
    WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "login_Password"))
    ).send_keys(password)
    WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, "btnLogin"))
    ).click()

    wait_loading(driver)

    print("visiting activity enrichment")
    WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.button:nth-child(2)"))
    ).click()

    wait_loading(driver)

    print("open logbook tab")
    WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "#btnLogBook > span:nth-child(1)"))
    ).click()

    print("waiting overlay to close")
    WebDriverWait(driver, TIMEOUT).until(
        EC.invisibility_of_element_located((By.CSS_SELECTOR, ".fancybox-overlay"))
    )

    print("parsing table from website")
    adira = read_logbook_adira(filename)

    print("DATA USED: " + adira)

    for index, row in adira.iterrows():
        print("Searching for {}".format(row["DATE"]))
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

                # isSaturday = False
                # if date.strftime("%A") == "Saturday":
                #     isSaturday = True

                if str(row["DATE"]) == str(date):
                    print("Found {}".format(row["DATE"]))

                    isFilled = tr.find_element(
                        By.CSS_SELECTOR, "td:nth-child(6) > div:nth-child(1)"
                    ).text.strip()

                    if isFilled != "-":
                        off = tr.find_element(
                            By.CSS_SELECTOR, "td:nth-child(5) > div:nth-child(1)"
                        ).text.strip()
                        if off != "OFF":
                            print("already filled")
                            break

                    isOff = False
                    if row["Activities"] == "off":
                        print("off")
                        isOff = True

                    entry = WebDriverWait(tr, TIMEOUT).until(
                        EC.visibility_of_element_located(
                            (By.CSS_SELECTOR, ".dt-Action .button")
                        )
                    )
                    driver.execute_script("arguments[0].click();", entry)

                    if not isOff:
                        fill_clock(row, driver)

                        WebDriverWait(driver, TIMEOUT).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "#editActivity")
                            )
                        ).clear().send_keys(row["Notes"])

                        WebDriverWait(driver, TIMEOUT).until(
                            EC.visibility_of_element_located(
                                (By.CSS_SELECTOR, "#editDescription")
                            )
                        ).clear().send_keys(row["Activities"])
                    else:
                        off = WebDriverWait(driver, TIMEOUT).until(
                            EC.visibility_of_element_located(
                                (
                                    By.CSS_SELECTOR,
                                    "#logBookEditPopup > div > div > div.row.text-right > a-encoded:nth-child(1)",
                                )
                            )
                        )
                        driver.execute_script("arguments[0].click();", off)

                    submit = WebDriverWait(driver, TIMEOUT).until(
                        EC.visibility_of_element_located(
                            (
                                By.CSS_SELECTOR,
                                "#logBookEditPopup > div > div > div.row.text-right > a-encoded:nth-child(2)",
                            )
                        )
                    )
                    driver.execute_script("arguments[0].click();", submit)

                    WebDriverWait(driver, TIMEOUT).until(EC.alert_is_present())
                    driver.switch_to.alert.accept()

                    wait_loading(driver)

                    isFound = True
                    break

    driver.close()
