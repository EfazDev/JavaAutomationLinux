import requests
import platform
import subprocess
import os
import time

def whichPythonCommand():
    LocalMachineOS = platform.system()
    if LocalMachineOS == "Darwin" or LocalMachineOS == "Linux":
        return "python3"
    elif LocalMachineOS == "win32" or LocalMachineOS == "win64" or LocalMachineOS == "Windows":
        return "python"
    else:
        return "python3"
    
if whichPythonCommand() == "python3":
    os.system("clear")
else:
    os.system("cls")
    
print("Welcome to JavaAutomation Launcher!")
print("")
print("Launcher Made by EfazDev#0220")
print("Linux Version by EfazDev#0220")
print("Windows Version by Java#9999")
print("")
print("Looking for System Device Details...")
print("Detected: " + platform.system())
url = ""
if whichPythonCommand() == "python3":
    print("Launching macOS/Linux Version...")
    url = "https://raw.githubusercontent.com/EfazDev/JavaAutomationLinux/main/JavaAutomation.py"
else:
    print("Launching Windows Version...")
    url = "https://raw.githubusercontent.com/IlyasCodes/JavaAutomationExtension/main/JavaAutomation.py"
time.sleep(2)
print("Locating Request from URL...")
resp = requests.get(url)
if resp.status_code == 200:
    print("Finished GET Request, saving script...")
    content = resp.text
    f = open("ExtenderRunner.py", "w")
    f.write(content)
    print("Finished Writing Script")
    print("Running Script...")
    subprocess.Popen([whichPythonCommand(), 'ExtenderRunner.py'])
    print("Finished Running, ending launcher...")
    quit()
else:
    print("Server returned unknown status code. Extension not runned")