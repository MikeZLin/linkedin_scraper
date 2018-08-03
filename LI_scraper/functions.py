import re
from time import sleep
from random import randint
def time_divide(string):
    duration = re.search("\((.*?)\)", string)

    if duration != None:
        duration = duration.group(0)
        string = string.replace(duration, "").strip()
    else:
        duration = "()"

    times = string.split("–")
    return (times[0].strip(), times[1].strip(), duration[1:-1])
def replace_symbols(text):
    text = text.replace("–",'-')
    text = text.replace("\u2019","'")
    text = text.replace('´',"'")
    text = text.replace('\u2022',' - ')
    return text
    
def get_pause(input):
    #print('Sleeping')
    #sleep(randint(0,500)/1000.0)
    return input

