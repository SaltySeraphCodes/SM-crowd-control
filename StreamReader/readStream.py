import pytchat # most recent thing in the core is the updated stuff
import time
import json
import os
import sys
import copy
import requests
import threading
from winreg import *
import vdf
import json
from shutil import copyfile
# import smObjects

## This automatically finds the scrap mechanic installation
## and sets SM_Location appropriately

aReg = ConnectRegistry(None,HKEY_LOCAL_MACHINE)

aKey = OpenKey(aReg, r"SOFTWARE\WOW6432Node\Valve\Steam")

steamPathKey=str(QueryValueEx(aKey, "InstallPath"))

def formatRegKey(key):
    return key.split(',')[0].replace('\'', '').replace('\\\\', '\\').replace('(C:', 'C:')

steamPath = formatRegKey(steamPathKey)

vdfFile = os.path.join(steamPath, "steamapps", "libraryfolders.vdf")

vdfFileContent = str(vdf.load(open(vdfFile))).replace('\'', '\"')

alternateSteamLibraries = json.loads(vdfFileContent)["LibraryFolders"]

SM_Location = os.path.join(steamPath, "steamapps", "common", "Scrap Mechanic")

i = 1
while(str(i) in alternateSteamLibraries):
    path = os.path.join(alternateSteamLibraries[str(i)], "common", "Scrap Mechanic")
    if os.path.isdir(path):
        SM_Location = path
        break
    i = i + 1

###########################################################

# dir_path is the current directory
dir_path = os.path.dirname(os.path.realpath(__file__))

# commonly use sm folder locations
base = os.path.join(dir_path, "Scripts")
smBase = os.path.join(SM_Location, "Survival", "Scripts", "game")
dataBase = os.path.join(smBase, "StreamReaderData")

# commly used file locations
statOutput = os.path.join(dir_path, 'JsonData', "statOutput.txt")
gameStats = os.path.join(dataBase, "gameStats.json")

# Import settings? for now have global settings
# TODO: Money pool to allow viewers to donate to a common goal
SETTINGS = {
    'allFree': False, # make everything freee
    'sponsorFree': True, # channel sponsors get free commands
    'TheGuyMode': True, # Special mode for TheGuy920
    'fixedCost': 0, # if >0 and allFree == false, all commands will cost this price
    'interval': 1, # rate in which to check for new commands, BROKEN until fixed...
    'prefix': ['!','/','$','%'],
    'filename': os.path.join(dataBase, 'streamchat.json'),
    'videoID': "wLiGcFnUuD0",
    'commands': { # list of commands and parameters, their prices are the values
        'spawn': {
            'totebot': 0,
            'woc': 0,
            'worm': 0,
            'haybot': 0,
            'tapebot': 0,
            'redtapebot': 0,
            'farmbot': 0,
        },
        'give':{ # give items to player (automatically gives stack if possible?)
            'components': 0, # gives 10
            'glowsticks': 0,
            'ammo': 0
        },
        'kit': { # gives player specified kit
            'seed': 0,
            'food': 0,
            'starter': 0,
            'pipe': 0,
            'meme': 0,
            'bonk': 0
        },
        'aggro': 0, # aggro all nearby units to player
        'kill': 2, # kill player instantly
        'trip': 0, # Make player trip
        'slap': 0,
        'shield':0, # shield player for bried ammount of time
        'rain': 0, # spawn a bunch of explosives in the air, could be random objects?
        'raid': 0, # random raid at levels
        'blast':0,
        'heal': 0,
        'fast':0,
        'slow':0
    },
    'internalCommands':
    {
        'import':0
    },
    'single': ['raid', 'fast', 'slow','heal','shield','blast','trip','slap','aggro','rain'] # uneccesary but list of all commands
}

def outputCommandQueue(commandQue):
    # print("OUT=>", commandQue)
    with open(SETTINGS['filename'], 'w') as outfile:
        jsonMessage = json.dumps(commandQue)
        # log("Writing commands",jsonMessage)
        outfile.write(jsonMessage)

def addToQue(commands, handleCommand):
    # adds to the already existing command que

    # log(commands)
    # Check if exists first
    # log("addQWue",commands)

    if not os.path.exists(SETTINGS['filename']):
        f = open(SETTINGS['filename'], "a")
        # make blank
        f.write('[]')
        f.close()

    with open(SETTINGS['filename'], 'r') as inFile:

        currentQue = json.load(inFile)
        # log("Got Que",currentQue,"adding",commands)

        # if empty? or check len too
        if currentQue == None: 

            # Create empty list
            currentQue = []
            currentQue.extend(commands)
        else:
            currentQue.extend(commands)

        # determines if the command should be handled or not
        # unless this is being run from/after an internal command
        # has executed, leave as default (True)
        if handleCommand == True:
            # TODO: get callback on success?
            commandHandler(currentQue)
        elif handleCommand == False:
            # print("Sending Queue=>", currentQue)
            outputCommandQueue(currentQue)

def commandHandler(commandQue):

    # command handler will take 2 copies of the queue
    commandList = copy.copy(commandQue)

    # if the command type exsists in internalCommands, it will be removed from the final execution
    # and will be executed internally instead
    for command in copy.copy(commandQue):
        if command['type'] in SETTINGS['internalCommands']:
            commandList.remove(command)
            handleInternalCommand(command)

    # if the command queue is not empty, update it
    # after command has been handled, add it to the
    # queue again, but do not handle it
    if(len(commandList) > 0):
        addToQue(commandList, False)


def handleInternalCommand(command):
    # internal command handler

    # yea, only got import as of now...
    if command['type'] == "import":
        try:
            # init fileId
            fileId = command['params']
            # if the command parameters are a list (ie. not a string)
            if not isinstance(command['params'], str):
                fileId = command['params'][0]

            # init blueprint.json file path and description file path
            jsonFile = os.path.join(dir_path,"downloads",fileId,"blueprint.json").replace("\\\\", "\\")
            descFile = os.path.join(dir_path,"downloads",fileId,"description.json").replace("\\\\", "\\")

            # init destination file paths
            jsonFileDest = os.path.join(dataBase, fileId+".blueprint")
            descFileDest = os.path.join(dataBase, fileId+"-desc.json")

            # checks to see if its already been downloaded
            if not os.path.exists(jsonFileDest):

                # downloads workshop item (most errors happen here)
                downloadWorkshopItem(command)
            
                # init timeout handler (seconds * 1000 / 50)
                timeOut = 100
                errorCount = 0

                # wait for file to exist or timeout
                while (not os.path.exists(jsonFile)) and errorCount < timeOut:
                    errorCount += errorCount
                    time.sleep(50)

                # copy blueprint and description file over to central folder
                copyfile(jsonFile, jsonFileDest)
                copyfile(descFile, descFileDest)

            # gather json state (static versus dynamic)
            state = 0.0
            if len(command['params']) > 2:
                state = getImportType(command['params'][2])
            elif len(command['params']) > 1:
                state = getImportType(command['params'][1])

            # load the json blueprint
            with open(jsonFileDest, 'r') as f:
                jsonContent = json.loads(f.read())

            # update the state
            array = jsonContent["bodies"]
            for i in range(len(array)):
                array[i]["type"] = state

            # save the json blueprint
            with open(jsonFileDest, 'w') as json_file:
                json.dump(jsonContent, json_file)

            # create command queue
            commandQue = []
            commandQue.extend(toJson(command))

            # update command queue
            addToQue(commandQue, False)

        except Exception as e:
            # handle any download or file errors
            logCommandError(e, command)
def getImportType(string):
    if (string == "static"):
        return 1
    else:
        return 0

def logCommandError(e, command):
    # print error
    print(e)
    # generate new log command
    command['type'] = "log"
    command['params'] = str(e)
    commandQue = []
    commandQue.extend(toJson(command))
    # add log to queue (to send error msg to SM)
    addToQue(commandQue, False)

def downloadWorkshopItem(command):

    # configure the start params correctly
    param = param = command['params']

    # if start params is not a string (ie. its an array) configure it
    if not isinstance(command['params'], str):
        param = command['params'][0]
        
    # configure node run command
    startArgs = "node ./SteamWorkshopDownloader/index.js " + param + " \"" + SM_Location + "\" > log.txt"

    # start node app to download workshop item
    exitCode = os.system(startArgs)

    # if app exits with error (69) alert of download failure
    if exitCode == 69:
        raise Exception("Failed To Download Workshop Item: {0}".format(str(command['params'])))
    
def generateCommand(command,parameter,cmdData): #Generates command dictionary
    command =  {'id': cmdData['id'], 'type':command, 'params':parameter, 'username': cmdData['author'], 
                'sponsor': cmdData['sponsor'], 'userid': cmdData['userid'], 'amount': cmdData['amount']}
    # print("Generated command:",command)
    return command

def validatePayment(command,price,message):

    # Validate payment data for the specified command
    # not necessary, just need price and message
    if command != None: 
        if SETTINGS['allFree'] or (SETTINGS['sponsorFree'] and message['sponsor']) or ((SETTINGS['fixedCost'] >0 and message['amount'] >= SETTINGS['fixedCost']) or message['amount'] >= price) :
           return True
        elif message['amount'] < price:
            print("Insuficcient payment",message['amount'],price)
            return False
        else:
            log("Payment Failed")
            return False
         

def validateCommand(parameters): 

    # {command is a array of parameters}
    comType = str(parameters[0])
    index = None
    price = None
    errorType = None

    # if comType == None or index error then wth??
    # Check if command valid first
    if comType in SETTINGS['commands'] or comType in SETTINGS['internalCommands']: 

         # a single line commnand with no extra params ex: kill, trip...
        if len(parameters) == 1 or comType  in SETTINGS['single']:
            price = SETTINGS['commands'][comType]

            #if an actual price
            if type(price) is int: 
                return comType,index,price

            # the command is supposed to have a parameter
            else: 
                errorType = "Invalid parameter count"
                return False,index,errorType

        # command = with X parameters (max params is infinite for now)
        elif len(parameters) > 1: 

            # grab the next index
            index = str(parameters[1]) 

        ## do not uncomment these logs, you will get an error if you do

            # log(SETTINGS['commands'][comType])
            # log(index)
            
            # Check for command type, or failure 
            if comType in SETTINGS['commands']:

                # If valid item within that command
                if index in SETTINGS['commands'][comType]:

                    # should be the maximum layer needed
                    price =  SETTINGS['commands'][comType][index] 
                    return comType,index,price

            # added section for internally handled commands like the import command
            elif comType in SETTINGS['internalCommands']:
                return comType,parameters[1:],int(SETTINGS['internalCommands'][comType])
            else:
                errorType = "Index Invalid"
                print("Unrecognized Index:",index)
        else:
            errorType = "Param Invalid"
            print("Too many or not enought parameters",parameters)
    else:
        errorType = "Command Invalid"
        print("unrecognized command",comType)
    #  Eventually have output error message
    return False,index,errorType

def parseMessage(chat,mesID):
    # parse any messages
    comType = None
    parameter = None
    parsed = {'id': mesID, 'command': chat.message, 'author': chat.author.name, 'sponsor': chat.author.isChatSponsor, 'userid': chat.author.channelId, 'amount': chat.amountValue}
    message = parsed['command'].lower()

    # is actually a command # Possibly separate out to parsing function
    if message[0] in SETTINGS['prefix']: 

        rawCommand = message.strip(message[0])
        parameters = rawCommand.split() #TODO: More validation to fix any potential mistakes

        # custom section for TheGuy920 and exclusive chat command ability
        if chat.author.channelId == "UCbBBHW3dQkyw7-b1eBurnuQ" and parameters[0] == "chat" and SETTINGS['TheGuyMode'] == True: # special mode for TheGuy920
            return generateCommand("chat",str(chat.message)[6:],parsed)

        if len(parameters) == 0:
            log("Only Recieved Prefix")
            return None

        comType,parameter,price = validateCommand(parameters)

        if comType == False:
            # possibly use index for details?
            print("Received Error for",rawCommand+": ",price) 
        else:
            # Now validate any payments
            validPayment = validatePayment(comType,price,parsed)
            if validPayment:
                command = generateCommand(comType,parameter,parsed)
                return command
            else:
                log("Invalid Payment")
    # super chat section (no prefix but payed monies)
    elif chat.amountValue > 0:
        return generateCommand("chat",str(chat.message),parsed)

    return None
    
def readChat():

    commandQue = []
    cID = 0

    while chat.is_alive():

        # Also do stats reading/outputting
      
        with open(gameStats, 'r') as inFile:
            gameInfo = json.load(inFile)
            # log("Got GameStats",gameStats)

        with open(statOutput, 'w') as outfile:
            deaths = gameInfo['deaths']
            output = "Deaths: {:.0f}".format(deaths)
            outfile.write(output)
            # log("outputing",output)

        for c in chat.get().sync_items():
            # log(c.datetime,c.author.name,c.message)
            command = parseMessage(c,cID)
            if command != None:
                commandQue.append(command)
                cID +=1
            if len(commandQue) >0:
                addToQue(commandQue, True)
            time.sleep(1)

        commandQue = []

        try:
            chat.raise_for_status()
        except Exception as e:
            print(type(e), str(e))

def toJson(obj):
    # this is basically the same as generateCommand, but I made another one for some reason

    jsonContent = jsonContent = "[ {\"id\": "+str(obj["id"])+", \"type\": \""+str(obj["type"])+"\", \"params\": \""+str(obj["params"])+"\", \"username\": \""+str(obj["username"])+"\", \"sponsor\": "+str(obj["sponsor"]).lower()+", \"userid\": \""+str(obj["userid"])+"\", \"amount\": "+str(obj["amount"])+"} ]"
    
    # specical configuration if more than one parameter
    if not isinstance(obj['params'], str):
        params =  "\""+"\",\"".join(obj["params"])+"\""
        jsonContent = "[ {\"id\": "+str(obj["id"])+", \"type\": \""+str(obj["type"])+"\", \"params\": [ "+params+" ], \"username\": \""+str(obj["username"])+"\", \"sponsor\": "+str(obj["sponsor"]).lower()+", \"userid\": \""+str(obj["userid"])+"\", \"amount\": "+str(obj["amount"])+"} ]"
    
    return json.loads(jsonContent)

# Planned commands: give speed, give slowness, lightning strike?, chop wood?
# chat = pytchat.create(video_id =  SETTINGS['videoID']) # start reading livechat #Create it here?? or store in settings and generate on main()

chat = None

debug = False

# custom logging style (kinda dumb ngl)
def log(string):
    print("["+str(string)+"]")

if __name__ == '__main__':
    if debug:
        pass
        # debug stuff here
    else:

        # verify working video url
        try:
            try:
                chat = pytchat.create(video_id=sys.argv[1])
                SETTINGS['videoID'] = sys.argv[1]
            except:
                chat = pytchat.create(SETTINGS['videoID'])
        except:
            log("Video Id Failure")
            ValidVideo = False
            userIn = ''
            while(not ValidVideo):
                if len(userIn) > 0:
                    log('Video Id \'{0}\' is not valid'.format(userIn))
                try:
                    userIn = input("YouTube Video Id => ")
                    chat = pytchat.create(video_id=userIn)
                    SETTINGS['videoID'] = userIn
                    ValidVideo = True
                except:
                    pass

        log("Installing Pre-Requisites")

        # create nessesary files and folders if the do not exist
        if not os.path.exists(os.path.join(smBase, "StreamReaderData")):
            os.makedirs(os.path.join(smBase, "StreamReaderData"))

        if not os.path.exists(statOutput):
            open(statOutput, 'a').close()

        if not os.path.exists(gameStats):
            open(gameStats, 'a').close()

        streamchatFile = open(os.path.join(dataBase, "streamchat.json").replace("\\\\","\\"), "w")
        streamchatFile.write("[]")
        streamchatFile.close()

        # install modded lua files
        copyfile(os.path.join(base,"survival_streamreader.lua"), os.path.join(dataBase, "survival_streamreader.lua"))
        copyfile(os.path.join(base,"BaseWorld.lua"), os.path.join(smBase, "worlds", "BaseWorld.lua"))
        copyfile(os.path.join(base,"SurvivalGame.lua"), os.path.join(smBase, "SurvivalGame.lua"))

        log("Stream Reader initialized")
        # start the reader
        readChat()
