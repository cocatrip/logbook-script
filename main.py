from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium import webdriver
from dotenv import load_dotenv
from datetime import datetime
import pandas
import os


def wait_loading(driver):
    # wait for pop up to be visible
    print("waiting overlay to close")
    WebDriverWait(driver, 50).until(EC.invisibility_of_element_located((
        By.CSS_SELECTOR,
        ".fancybox-overlay"
    )))


def read_logbook_adira():
    df = pandas.read_csv(
        'data.csv',
        header=6,
        names=[
            'Day', 'DATE',
            'Working Hour',
            'Duty On Hour',
            'Duty On Minute',
            'Duty Off Hour',
            'Duty Off Minute',
            'Notes', 'Activities'
        ],
        parse_dates=['DATE'],
        infer_datetime_format=True
    )

    fill_nan = {
        'Working Hour',
        'Duty On Hour',
        'Duty On Minute',
        'Duty Off Hour',
        'Duty Off Minute',
    }
    for col in fill_nan:
        df[col] = pandas.to_numeric(df[col], errors='coerce').fillna(0)

    convert = {
        'Working Hour': int,
        'Duty On Hour': int,
        'Duty On Minute': int,
        'Duty Off Hour': int,
        'Duty Off Minute': int,
    }

    df = df.astype(convert)

    return df


def fill_clock(row, driver):
    clock_in = WebDriverWait(driver, 50).until(
        EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            "#logBookEditPopup > div > div > div.item-body > div > div:nth-child(2) > span > span"
        ))
    )
    driver.execute_script("arguments[0].click();", clock_in)

    hour = Select(driver.find_element(
        By.CSS_SELECTOR,
        '.ui_tpicker_hour_slider > select:nth-child(1)'))
    hour.select_by_value('{}'.format(row['Duty On Hour']))

    minute = Select(driver.find_element(
        By.CSS_SELECTOR,
        '.ui_tpicker_minute_slider > select:nth-child(1)'))
    minute.select_by_value('{}'.format(row['Duty On Minute']))

    done = WebDriverWait(driver, 50).until(
        EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            "#ui-datepicker-div > div.ui-datepicker-buttonpane.ui-widget-content > button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all"
        ))
    )
    driver.execute_script("arguments[0].click();", done)

    clock_out = WebDriverWait(driver, 50).until(
        EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            "#logBookEditPopup > div > div > div.item-body > div > div:nth-child(4) > span > span"
        ))
    )
    driver.execute_script("arguments[0].click();", clock_out)

    hour = Select(driver.find_element(
        By.CSS_SELECTOR,
        '.ui_tpicker_hour_slider > select:nth-child(1)'))
    hour.select_by_value('{}'.format(row['Duty On Hour']))

    minute = Select(driver.find_element(
        By.CSS_SELECTOR,
        '.ui_tpicker_minute_slider > select:nth-child(1)'))
    minute.select_by_value('{}'.format(row['Duty On Minute']))

    done = WebDriverWait(driver, 50).until(
        EC.visibility_of_element_located((
            By.CSS_SELECTOR,
            "#ui-datepicker-div > div.ui-datepicker-buttonpane.ui-widget-content > button.ui-datepicker-close.ui-state-default.ui-priority-primary.ui-corner-all"
        ))
    )
    driver.execute_script("arguments[0].click();", done)


def main():
    load_dotenv()

    email = os.getenv('EMAIL')
    password = os.getenv('PASSWORD')

    opt = Options()
    # opt.add_argument("--headless")

    driver = webdriver.Chrome(options=opt)

    print("opening enrichment website")
    driver.get("https://enrichment.apps.binus.ac.id/Login/Student/Login")

    print("logging in")
    driver.find_element(By.ID, "login_Username").send_keys(email)
    driver.find_element(By.ID, "login_Password").send_keys(password)
    driver.find_element(By.ID, "btnLogin").click()

    wait_loading(driver)

    print("visiting activity enrichment")
    WebDriverWait(driver, 50).until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "a.button:nth-child(2)"
    ))).click()

    wait_loading(driver)

    print("open logbook tab")
    WebDriverWait(driver, 50).until(EC.element_to_be_clickable((
        By.CSS_SELECTOR,
        "#btnLogBook > span:nth-child(1)"
    ))).click()

    print("waiting overlay to close")
    WebDriverWait(driver, 50).until(EC.invisibility_of_element_located((
        By.CSS_SELECTOR,
        ".fancybox-overlay"
    )))

    print("parsing table from website")
    adira = read_logbook_adira()

    for index, row in adira.iterrows():
        print("Searching for {}".format(row['DATE']))
        found = False

        try:
            table = driver.find_element(By.ID, "logBookTable")
        except StaleElementReferenceException:
            WebDriverWait(driver, 5).until(EC.staleness_of(table))

        for tr in table.find_elements(By.XPATH, ".//tr"):
            if found:
                break

            for td in tr.find_elements(By.XPATH, ".//td[1]"):
                date = datetime.strptime(td.text, '%a, %d %b %Y')
                isSaturday = False
                if date.strftime('%A') == 'Saturday':
                    isSaturday = True
                if str(row['DATE']) == str(date) or isSaturday:
                    print("Found {} == {}".format(row['DATE'], date))

                    isFilled = tr.find_element(
                        By.CSS_SELECTOR,
                        "td:nth-child(6) > div:nth-child(1)"
                    ).text.strip()

                    if isFilled != '-':
                        print("already filled")
                        break

                    isOff = False
                    if row['Working Hour'] == 0:
                        print("off")
                        isOff = True
                    elif isSaturday:
                        print("saturday")
                        isOff = True

                    entry = WebDriverWait(tr, 50).until(
                        EC.visibility_of_element_located((
                            By.CSS_SELECTOR,
                            ".dt-Action .button"
                        ))
                    )
                    driver.execute_script("arguments[0].click();", entry)

                    if not isOff:
                        fill_clock(row, driver)

                        WebDriverWait(driver, 50).until(
                            EC.visibility_of_element_located((
                                By.CSS_SELECTOR,
                                "#editActivity"
                            ))
                        ).send_keys(row['Notes'])

                        WebDriverWait(driver, 50).until(
                            EC.visibility_of_element_located((
                                By.CSS_SELECTOR,
                                "#editDescription"
                            ))
                        ).send_keys(row['Activities'])
                    else:
                        off = WebDriverWait(driver, 50).until(
                            EC.visibility_of_element_located((
                                By.CSS_SELECTOR,
                                "#logBookEditPopup > div > div > div.row.text-right > a-encoded:nth-child(1)"
                            ))
                        )
                        driver.execute_script("arguments[0].click();", off)

                    submit = WebDriverWait(driver, 50).until(
                        EC.visibility_of_element_located((
                            By.CSS_SELECTOR,
                            "#logBookEditPopup > div > div > div.row.text-right > a-encoded:nth-child(2)"
                        ))
                    )
                    driver.execute_script("arguments[0].click();", submit)

                    WebDriverWait(driver, 10).until(EC.alert_is_present())
                    driver.switch_to.alert.accept()

                    wait_loading(driver)

                    found = True
                    break

    driver.close()


if __name__ == '__main__':
    main()
