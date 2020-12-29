from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from time import sleep
from FileReader import FileReader
from NameBlock import NameBlock
import re
import sys
import openpyxl as excel

INTERVAL = 6 # Seconds per cycle
WAIT = 300 # Wait for elements to show
CURRENT_NUMBER = "+62 812-9749-9150" # Insert your number here
DATADIR = "test" # To indicate which datadir WhatsApp uses

# FIle Reader object
class FileReader:

    def readTxt(filename):
        results = []
        with open(filename, "r") as f:
            data = f.read().splitlines()
            for line in data:
                results.append(line)
        return results
    
    def readExcel(filename, column):
        lst = []
        file = excel.load_workbook(filename)
        sheet = file.active
        firstCol = sheet[column]
        for cell in range(len(firstCol)):
            contact = str(firstCol[cell].value)
            # contact = "\"" + contact + "\""
            lst.append(contact)
        
        return lst

# Message object
class MessagesBlock:

    def __init__(self, name, element):
        self.name = name
        self.element = element
    
    def getMessages(self, fromLeft):
        if fromLeft: return [i.text for i in self.element.find_elements_by_xpath \
            (".//*[contains(@class, 'message-in')]//*[contains(@class, '_1VzZY')]")]
        else: return [i.text for i in self.element.find_elements_by_xpath \
            (".//*[contains(@class, 'message-out')]//*[contains(@class, '_1VzZY')]")]


def main():

    if len(sys.argv) == 1: sys.exit("Please enter arguments")

    # Setup driver and contacts
    global driver, contacts, salesDict
    driver = setupDriver()
    salesNames, salesNumbers, contacts, salesDict = setupContacts(sys.argv[1], sys.argv[2], sys.argv[3])
    ignoreList = ["tpyramid", "uea", "universe"] # For debugging / scam contacts

    # Loop to keep program on
    while True:
        # try:
        goToContact(CURRENT_NUMBER)
        sleep(INTERVAL)

        unreadNameBlocks = getAllUnreadNameBlocks(10)
        if len(unreadNameBlocks) == 0:
            continue

        for name, nameBlock in unreadNameBlocks.items():

            # Ignore list
            if any(i in name.lower() for i in ignoreList): continue

            numUnread = nameBlock.numUnread()
            if not numUnread: continue

            if any(name in i for i in salesNames): # If incoming name found in salesList
                forwardSales(name, numUnread, True, salesNames)
            else:
                forwardCustomer(name, numUnread, True, salesNames)
        # except (KeyboardInterrupt, SystemExit):
        #     raise 
        # except Exception as e:
        #     print(e)
        #     continue

    
    driver.close()

# Send a message by typing
def sendMessage(name, message):
    goToContact(name)
    
    try: WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.XPATH,"//footer//*[@contenteditable='true']")))
    except: return

    input_box = driver.find_element_by_xpath("//footer//*[@contenteditable='true']")
    input_box.send_keys(message)
    input_box.send_keys(Keys.RETURN)
    sleep(1)

# Forward messages from sales team
def forwardSales(name, numUnread, fromLeft, numberSet):

    for message in range(numUnread):

        goToContact(name)

        # Check if sales team replied properly
        repliedXPath = "(//div[contains(@data-id,'false')])[last()" + (str((-1) * message) if message else "") + "]//div[contains(@class, '_1Dook')]"
        replied = driver.find_elements_by_xpath(repliedXPath)
        if len(replied) == 0:
            sendMessage(name, "Message not sent. Please reply to a message!")
            return
        
        replied[0].click()
        sleep(1)
        messages = driver.find_elements_by_xpath('//div[contains(@data-id,"true")]')

        # Find the replied to message
        i = -1
        replyToWho = ""

        for _ in range(len(messages)):

            # Try to locate the chatbox that has a different color (meaning it was the one that is highlighted when reply message is clicked)
            x_arg = "//div[contains(@data-id,'true')][last()" + (str(i + 1) if i != -1 else "") + "][@tabindex='0']"
            replyItem = driver.find_elements_by_xpath(x_arg)

            # When located
            if len(replyItem) != 0:

                # If reply was correct
                try: 
                    pattern = re.compile(r"\[from.*\s+(.*)\]")
                    replyToWho = pattern.match(replyItem[0].find_element_by_xpath('.//*[contains(@class,"_1wlJG")]').text).group(1)
                except: 
                    sendMessage(name, "Message not sent. Please reply to the from message!")
                    return
                break
            i -= 1

        # print(replyText := messages[i + 1].find_element_by_xpath('.//*[contains(@class,"_1wlJG")]').text)

        recipientMessage = "[from " + name + " to " + replyToWho + "]"
        recipientMessage += "---" + contacts[replyToWho] + "---" if replyToWho in contacts else ""
        recipientMessage += " Replying to:"
        sendMessage(CURRENT_NUMBER, recipientMessage)
        for numbers in numberSet:
            forwardMessage(CURRENT_NUMBER, 1, 0, False, numbers)
            forwardMessage(replyToWho, 1, 0, True, numbers)
            forwardMessage(name, 1, message, fromLeft, [replyToWho])
            forwardMessage(name, 1, message, fromLeft, numbers)
        
# Forward messages from customer
def forwardCustomer(name, numUnread, fromLeft, numberSet):
    
    recipientMessage = "[from " + name + "]"
    recipientMessage += "---" + contacts[name] + "---" if name in contacts else ""
    sendMessage(CURRENT_NUMBER, recipientMessage)
    for numbers in numberSet:
        forwardMessage(CURRENT_NUMBER, 1, 0, False, numbers)
        forwardMessage(name, numUnread, 0, fromLeft, numbers)

# Forward messages
def forwardMessage(name, numUnread, index, fromLeft, numbers):

    goToContact(name)

    if fromLeft: print("Taking message from left...")
    else: print("Taking message from right...")
    x_arg = "(//div[@class='tSmQ1']/div[contains(@data-id,'" + ("false" if fromLeft else "true") + "')]/div/div/div/div)[last()" + (str((-1) * (index)) if index else "") + "]"
    print(x_arg)

    while True:
        action = ActionChains(driver)
        action.move_to_element(driver.find_element_by_xpath(x_arg)).perform()
        
        sleep(0.25)

        driver.find_element_by_xpath('//div[@data-js-context-icon="true"]').click()
        sleep(0.25)
    
        try:
            driver.find_element_by_xpath('//*[@title="Forward all"]').click()
        except:
            try:
                driver.find_element_by_xpath('//*[@title="Forward message"]').click()
                break
            except:
                videos = driver.find_elements_by_xpath('//*[contains(@class,"_3i3h7")]')
                print(len(videos))
                if len(videos):
                    videos[-1].click()
                    forwardxpath = '//div[contains(@title, "Forward")]'
                    WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.XPATH,forwardxpath)))
                    driver.find_element_by_xpath('//div[@title="Close"]').click()
                continue

    checkboxCSSSelector = "div.message-" + ("in" if fromLeft else "out") + ".focusable-list-item"
    checkbox = [element.find_element_by_xpath(".//*[@class='_2K7JO']") for element in driver.find_elements_by_css_selector(checkboxCSSSelector)]

    for i in range(numUnread - 1):
        num = -1 * (i + 2) - index
        try: checkbox[num].click()
        except: break
    
    try: driver.find_element_by_xpath('//button[@title="Forward messages"]').click()
    except:  driver.find_element_by_xpath('//button[@title="Forward message"]').click()
    input_box = driver.find_element_by_xpath('//div[@contenteditable="true"][1]')
    for number in numbers:
        number = salesDict[number] if number in salesDict else number
        input_box.clear()
        input_box.send_keys(number)
        sleep(0.5)
        input_box.send_keys(Keys.RETURN)
        sleep(0.4)
    driver.find_element_by_xpath('//div[@class="_3FwbN"]/div/div').click()
    sleep(1)

# Gets all unread name blocks, based on how many blocks that are checked
def getAllUnreadNameBlocks(blocks):
    nameSelector = driver.find_element_by_xpath("//*[@contenteditable='true']")
    nameSelector.click()

    nameBlocks = {}
    next_element = nameSelector
    for _ in range(blocks):
        next_element.send_keys(Keys.ARROW_DOWN)
        next_element = driver.switch_to_active_element()

        try: nameBlock = NameBlock(next_element)
        except NoSuchElementException: continue

        if nameBlock.unread: nameBlocks[nameBlock.name] = nameBlock
    return nameBlocks

# Go to unsaved contact (through the search phone number button)
def goToContact(number):
    nameSelector = driver.find_element_by_xpath("//*[@contenteditable='true']")
    nameSelector.send_keys(number)
    sleep(1)
    nameSelector.send_keys(Keys.ENTER)

# Sets up the driver for use
def setupDriver():

    options = Options()    
    options.add_argument("--user-data-dir=./User_Data_" + DATADIR)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3641.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)
    # driver.maximize_window()
    driver.get("https://web.whatsapp.com")

    # Wait until WhatsApp loads
    try:
        WebDriverWait(driver, WAIT).until(EC.presence_of_element_located((By.CLASS_NAME, "_1MZWu")))
    except:
        print("Unable to login.")
        exit()
    
    return driver

# Sets up the contacts
def setupContacts(salesNamesFile, salesNumbersFile, contactsExcelFile):

    fileReader = FileReader
    preliminarySalesNames = fileReader.readTxt(salesNamesFile)
    preliminarySalesNumbers = fileReader.readTxt(salesNumbersFile)
    contactNames = fileReader.readExcel(contactsExcelFile, 'A')
    contactNumbers = fileReader.readExcel(contactsExcelFile, 'B')

    contacts = {}
    for index, i in enumerate(contactNames):
        contactNames[index] = i.replace(" ", "")
        contacts[i] = contactNumbers[index]

    salesDict = {}
    for index, i in enumerate(preliminarySalesNames):
        salesDict[i] = preliminarySalesNumbers[index]

    salesNames = [preliminarySalesNames[x: x + 5] for x in range(0, len(preliminarySalesNames), 5)]
    salesNumbers = [preliminarySalesNumbers[x: x + 5] for x in range(0, len(preliminarySalesNumbers), 5)]

    print(salesNames)
    print(salesNumbers)
    print(salesDict)
    print(contactNames)
    print(contactNumbers)
    print(contacts)

    return salesNames, salesNumbers, contacts, salesDict

if __name__ == "__main__":
    main()