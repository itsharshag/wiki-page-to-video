import re
import os
import math
import timeit
import textwrap
from datetime import datetime
from collections import OrderedDict

import pyttsx3
from gtts import gTTS
import soundfile as sf
from moviepy.editor import *

import requests
import urllib.request
from bs4 import BeautifulSoup

from utils import *
from audio import *

HEADING_FONT = "Montserrat-SemiBold"
PARAGRAPH_FONT = "Montserrat-Regular"
# OVERLAY_IMAGE = os.path.join("Resources", "blackTransparentOverlay.png")


class WikipediaVideoGenerator:
    soup = None

    clipsList = []
    imagesUsed = []
    orderedDict = OrderedDict()

    mainImageFilename = ""
    currMainHeading = ""
    currSubHeading = ""

    imageClipCount = 0
    audioClipCount = 0

    wrapper = textwrap.TextWrapper(width=58)
    logoClip = ImageClip("Resources/vidWikiLogo.png").set_pos((1125, 635))
    colorPallete = [convertHexToRGB(color) for color in ["#05668d", "#028090", "#00a896", "#02c39a"]]

    def __init__(self, wikipediaLink):
        self.wikipediaLink = wikipediaLink

    def splitParagraphIntoLines(self, ph):
        ph = cleanString(ph)
        ph = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', ph)
        ph = [line for line in ph if line]
        return ph

    def parseIntroduction(self):
        introduction = []
        p = self.soup.find_all('p')

        for l in p:
            if len(l.find_parents('table')) > 0:
                continue
            else:
                p = l
                break

        while p.next_sibling:

            if(p.name == None):
                p = p.next_sibling
                continue

            if p.name == "p" and p.get('class') == None:
                introduction += [self.splitParagraphIntoLines(p.text)]

            if p.name == "div" and ('toc' in p.get('class')):
                break

            p = p.next_sibling

        return introduction

    def createProjectFolders(self, filename):
        basePath = os.path.join("Productions", filename)
        if not os.path.exists(basePath):
            os.makedirs(os.path.join(basePath, "images"))
            os.makedirs(os.path.join(basePath, "audioClips"))

    def calculateClipDuration(self, clipName: str):
        f = sf.SoundFile(clipName)
        return math.ceil(len(f)/f.samplerate)

    def generateFileName(self, wikipediaLink):
        fileName = re.search(r"(/[a-zA-Z0-9-_()]+?)[.]*$", wikipediaLink)
        try:
            fileName = fileName.group(1)[1:]
            return fileName
        except:
            now = datetime.now().strftime("%H-%M-%S")
            return ("Video_" + now)

    # Functions to divide paragraphs into appropriate sized chunks for proper presentation

    def giveNumbers(self, number: int):
        lst = []
        while number > 0:
            if number <= 5:
                lst.append(number)
                number = 0
            elif number == 6:
                lst.append(3)
                lst.append(3)
                number = 0
            elif number == 7:
                lst.append(4)
                lst.append(3)
                number = 0
            elif number > 7:
                lst.append(5)
                number -= 5
        return lst

    def organizeParagraphs(self, data: str):
        newData = []
        for splittedPh in data:
            lst = self.giveNumbers(len(splittedPh))
            pos = 0
            for number in lst:
                newData += [' '.join(splittedPh[pos:pos+number])]
                pos += number
        return newData

    def organizeImages(self, paragraphsCount: int, images):
        organizedImages = []
        try:
            lenImages = len(images)
            lst = [paragraphsCount // lenImages + (1 if x < paragraphsCount %
                                                   lenImages else 0) for x in range(lenImages)]
            for i in range(len(lst)):
                organizedImages += [images[i]] * lst[i]
        except:
            pass
        return organizedImages

    def fetchAndStoreImage(self, url: str, filename: str):
        self.imagesUsed.append(url)
        imageExtension = parseImageExtension(url)
        imageName = "image" + str(self.imageClipCount) + "." + imageExtension
        filePath = os.path.join("Productions", filename, "images", imageName)

        urllib.request.urlretrieve(url, filePath)

        self.imageClipCount += 1

        return filePath

    def generateAndStoreAudioFile(self, text: str, filename: str):
        filePath = os.path.join("Productions", filename, "audioClips", "clip" + str(self.audioClipCount) + ".wav")

        cleanedText = removeBracketsText(text)
        print(text, cleanedText)
        isSuccess = TTS(PyTTSX3()).generate(cleanedText, filePath)
        if not isSuccess:
            print("Error in generating audio file")

        self.audioClipCount += 1

        return filePath

    def cleanWikipediaImageURL(self, url: str):
        url = "http:" + url[:url.rfind('/')]
        url = url.replace("/thumb", '')
        return url

    def scrapeWikipediaPage(self, wikipediaLink: str, pageName: str):
        response = requests.get(wikipediaLink)
        self.soup = BeautifulSoup(response.text, "lxml")

        self.orderedDict["Introduction"] = OrderedDict()
        self.orderedDict["Introduction"]["text"] = self.parseIntroduction()
        h = self.soup.find_all('h2')
        curr = h[1]

        try:
            infobox = self.soup.find_all("table", {"class": "infobox"})[0]
            infoboxImageURL = self.cleanWikipediaImageURL((infobox.find_all("img")[0]).get("src"))
            self.mainImageFilename = self.fetchAndStoreImage(infoboxImageURL, pageName)
            self.orderedDict["Introduction"]["image"] = [self.mainImageFilename]
        except:
            self.orderedDict["Introduction"]["image"] = []
            print("No infobox")

        currMainHeading = cleanHeading(curr.text)

        self.orderedDict[currMainHeading] = OrderedDict()

        currSubHeading = "Introduction"
        self.orderedDict[currMainHeading][currSubHeading] = OrderedDict()
        self.orderedDict[currMainHeading][currSubHeading]["text"] = []
        self.orderedDict[currMainHeading][currSubHeading]["images"] = []

        while curr.next_sibling:
            curr = curr.next_sibling

            name = curr.name
            if(name == None):
                continue

            currClass = curr.get('class')

            if currClass != None:
                if('thumb' in currClass):
                    try:
                        containedImageURL = self.cleanWikipediaImageURL((curr.find_all("img")[0]).get("src"))
                        imageFileName = self.fetchAndStoreImage(containedImageURL, pageName)
                        self.orderedDict[currMainHeading][currSubHeading]["images"].append(imageFileName)
                    except Exception as e:
                        print(e, "No image inside thumb div found.")

            if(name == "h2"):
                currMainHeading = cleanHeading(curr.text)
                self.orderedDict[currMainHeading] = OrderedDict()
                currSubHeading = "Introduction"
                self.orderedDict[currMainHeading][currSubHeading] = OrderedDict()
                self.orderedDict[currMainHeading][currSubHeading]["text"] = []
                self.orderedDict[currMainHeading][currSubHeading]["images"] = []
            elif(name == "h3"):
                currSubHeading = cleanHeading(curr.text)
                self.orderedDict[currMainHeading][currSubHeading] = OrderedDict()
                self.orderedDict[currMainHeading][currSubHeading]["text"] = []
                self.orderedDict[currMainHeading][currSubHeading]["images"] = []
            elif(name == "p"):
                self.orderedDict[currMainHeading][currSubHeading]["text"] += [self.splitParagraphIntoLines(curr.text)]

    def makeSlideClip(self, bodyText, headClip, bgClip, filename, images):
        for counter in range(len(bodyText)):
            paragraph = bodyText[counter]

            wrappedParagraph = self.wrapper.fill(text=paragraph)
            textClip = TextClip(wrappedParagraph, fontsize=22, font=PARAGRAPH_FONT, color='white',
                                method="label", align="West").set_pos((40, 150))

            audioFileCompletePath = self.generateAndStoreAudioFile(paragraph.replace("\n", " "), filename)
            audioFileDuration = AudioUtils.calculateDuration(audioFileCompletePath)

            try:
                if audioFileDuration != None and audioFileDuration > 0:
                    headClip.set_duration(audioFileDuration)
                    bgClip.set_duration(audioFileDuration)
                    textClip.set_duration(audioFileDuration)
                    self.logoClip.set_duration(audioFileDuration)

                    if len(images) > 0:
                        imageClip = ImageClip(images[counter]).set_pos((800, 40)).resize(width=380)
                        compositeClip = CompositeVideoClip(
                            [bgClip, headClip, textClip, imageClip, self.logoClip],
                            size=(1280, 720)).set_duration(audioFileDuration)
                    else:
                        compositeClip = CompositeVideoClip(
                            [bgClip, headClip, textClip, self.logoClip],
                            size=(1280, 720)).set_duration(audioFileDuration)

                    compositeClip.audio = AudioFileClip(audioFileCompletePath)
                    self.clipsList.append(compositeClip)

                    print("Successfully created slide clip")
            except Exception as e:
                print("Issue with makeSlideClip: ", e)

    def createVideoCoverClip(self, filename: str):
        try:
            videoTitle = filename.replace("_", " ")
            videoTitle = videoTitle.upper()

            audioFileCompletePath = self.generateAndStoreAudioFile(videoTitle, filename)
            audioFileDuration = self.calculateClipDuration(audioFileCompletePath)

            wrapperForHeading = textwrap.TextWrapper(width=10)
            videoTitle = wrapperForHeading.fill(text=videoTitle)

            sideBox = ImageClip("Resources/sideBox.png").set_duration(3)
            self.logoClip = self.logoClip.set_opacity(0.5)

            coverHeadingClip = TextClip(videoTitle, fontsize=72, font="Barlow-Black", color='white', method="label")
            xPos = (528 - coverHeadingClip.w) / 2
            coverHeadingClip = coverHeadingClip.set_pos((xPos, "center"))
            coverImage = ImageClip(self.mainImageFilename).set_pos((528, 0)).set_duration(3)

            width = 1280 - 528

            if coverImage.w / coverImage.h <= (width / 720):
                coverImage = coverImage.resize(width=width)
            else:
                coverImage = coverImage.resize(height=720)

            coverClip = CompositeVideoClip([coverImage, sideBox, coverHeadingClip, self.logoClip],
                                           size=(1280, 720)).set_duration(3)
            coverClip.audio = AudioFileClip(audioFileCompletePath)
            self.clipsList.append(coverClip)
        except Exception as e:
            print("Could not create cover clip for", filename)
            print("Error:", e)

    def createAttributionsClip(self):
        subHeadingCounter = 0
        duration = 4
        colorTuple = self.colorPallete[subHeadingCounter % 4]
        bgClip = ColorClip(size=(1280, 720), color=colorTuple)

        xPos = 40
        color = "white"
        method = "label"
        align = "West"

        content = [
            {
                "name": "MEDIA ATTRIBUTIONS",
                "font": HEADING_FONT,
                "fontSize": 32,
                "pos": (xPos, 40)
            },
            {
                "name": "Text:",
                "font": HEADING_FONT,
                "fontSize": 28,
                "pos": (xPos, 150)
            },
            {
                "name": self.wikipediaLink,
                "font": PARAGRAPH_FONT,
                "fontSize": 20,
                "pos": (xPos, 185)
            },
            {
                "name": "Images:",
                "font": HEADING_FONT,
                "fontSize": 28,
                "pos": (xPos, 215)
            }
        ]

        clips = []
        for item in content:
            txt_clip = TextClip(item["name"], fontsize=item["fontSize"], font=item["font"], color=color,
                                method=method, align=align).set_pos(item["pos"]).set_duration(duration)
            clips.append(txt_clip)

        for index in range(len(self.imagesUsed)):
            self.imagesUsed[index] = str(index + 1) + ". " + self.imagesUsed[index]

        imagesLinkText = "\n".join(self.imagesUsed)
        imagesClip = TextClip(imagesLinkText, fontsize=20, font=PARAGRAPH_FONT, color='white',
                              method="label", align="West").set_pos((40, 250)).set_duration(duration)

        attributionsClip = CompositeVideoClip([bgClip, clips[0], clips[1],
                                               clips[2], clips[3], imagesClip], size=(1280, 720)).set_duration(duration)

        return attributionsClip

    def produceVideo(self):
        self.audioClipCount = 0
        subheadingCounter = 0
        filename = self.generateFileName(self.wikipediaLink)

        self.createProjectFolders(filename)
        self.scrapeWikipediaPage(self.wikipediaLink, filename)
        self.createVideoCoverClip(filename)

        for sectionHeading, sectionContent in self.orderedDict.items():
            if sectionHeading in ["See also", "Notes", "References"]:
                break

            color = self.colorPallete[subheadingCounter % 4]
            bgClip = ColorClip(size=(1280, 720), color=color)

            audioFileCompletePath = self.generateAndStoreAudioFile(sectionHeading, filename)
            audioFileDuration = self.calculateClipDuration(audioFileCompletePath)

            wrapperForSectionHeading = textwrap.TextWrapper(width=20)
            sectionHeadingText = wrapperForSectionHeading.fill(text=sectionHeading.upper())
            sectionHeadingClip = TextClip(sectionHeadingText, font=HEADING_FONT, fontsize=72,
                                          color='white', method="label").set_pos(("center", "center")).set_duration(audioFileDuration)

            self.logoClip.set_duration(audioFileDuration)
            sectionHeadingComposeClip = CompositeVideoClip(
                [bgClip, self.logoClip, sectionHeadingClip],
                size=(1280, 720)).set_duration(audioFileDuration)
            sectionHeadingComposeClip.audio = AudioFileClip(audioFileCompletePath)

            self.clipsList.append(sectionHeadingComposeClip)

            try:
                for a, f in sectionContent.items():
                    subheadingWrapper = textwrap.TextWrapper(width=35)
                    finalSubheading = " / ".join([sectionHeading, a]).upper()
                    finalSubheading = subheadingWrapper.fill(text=finalSubheading)
                    headClip = TextClip(finalSubheading, fontsize=32, font=HEADING_FONT,
                                        color='white', method="label", align="West").set_pos((40, 40))
                    subheadingCounter += 1

                    b = self.organizeParagraphs(f["text"])
                    imgs = self.organizeImages(len(b), f["images"])

                    self.makeSlideClip(b, headClip, bgClip, filename, imgs)

            except Exception as e:
                headClip = TextClip("INTRODUCTION", fontsize=32, font=HEADING_FONT,
                                    color='white', method="label", align="West").set_pos((40, 40))

                vText = self.organizeParagraphs(sectionContent["text"])
                imgs = self.organizeImages(len(vText), sectionContent["image"])
                self.makeSlideClip(vText, headClip, bgClip, filename, imgs)

                print("Error from here: ", e)

        attributionsClip = self.createAttributionsClip()
        self.clipsList.append(attributionsClip)

        concatenatedClipPath = os.path.join("Productions", filename, filename + ".mp4")
        concatenatedClip = concatenate(self.clipsList, method="compose")
        concatenatedClip.write_videofile(concatenatedClipPath, fps=1, preset="ultrafast")


start = timeit.default_timer()

WikipediaVideoGenerator("https://en.wikipedia.org/wiki/Nico_Ditch").produceVideo()

stop = timeit.default_timer()
print('Time taken (in seconds): ', stop - start)
