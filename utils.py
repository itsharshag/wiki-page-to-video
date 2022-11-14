import re


def convertHexToRGB(hexValue):
    hexValue = hexValue[1:]
    return tuple(int(hexValue[i:i+2], 16) for i in (0, 2, 4))


def removeBracketsText(string):
    string = re.sub("\(.+?\)", "", string)
    return string


def cleanString(string):
    string = re.sub("\[[0-9]+\]", "", string)
    return string


def cleanHeading(string):
    string = re.sub("\[edit\]", "", string)
    return string


def parseImageExtension(string):
    extension = re.search("[.][a-zA-Z]+$", string).group(0)[1:]
    return extension
