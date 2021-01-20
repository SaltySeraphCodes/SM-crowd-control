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

dir_path = os.path.dirname(os.path.realpath(__file__))

base = os.path.join(dir_path, "Scripts")
smBase = os.path.join(SM_Location, "Survival", "Scripts", "game")

# Import settings? for now have global settings
# TODO: Money pool to allow viewers to donate to a common goal
SETTINGS = {
    'allFree': False, # make everything freee
    'sponsorFree': True, #channel sponsors get free commands
    'fixedCost': 0, # if >0 and allFree == false, all commands will cost this price
    'interval': 1, #rate in which to check for new commands, BROKEN until fixed...
    'prefix': ['!','/','$','%'],
    'filename': os.path.join(smBase, 'streamchat.json'),
    'videoID': "vid-id-here",
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
        'give':{ #give items to player (automatically gives stack if possible?)
            'components': 0, #gives 10
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
        'aggro': 0, #aggro all nearby units to player
        'kill': 2, #kill player instantly
        'trip': 0, #Make player trip
        'slap': 0,
        'shield':0, #shield player for bried ammount of time
        'rain': 0, # spawn a bunch of explosives in the air, could be random objects?
        'raid': 0, #random raid at levels
        'blast':0,
        'heal': 0,
        'fast':0,
        'slow':0
    },
    'internalCommands':
    {
        'import':0
    },
    'single': ['raid', 'fast', 'slow','heal','shield','blast','trip','slap','aggro','rain'] #uneccesary but list of all commands
}

def outputCommandQueue(commandQue):
    print("OUT=>", commandQue)
    with open(SETTINGS['filename'], 'w') as outfile:
        jsonMessage = json.dumps(commandQue)
        # log("Writing commands",jsonMessage)
        outfile.write(jsonMessage)

def addToQue(commands, handleCommand): # adds to the already existing command que
    # log(commands)
    # Check if exists first
    # log("addQWue",commands)
    if not os.path.exists(SETTINGS['filename']):
        f = open(SETTINGS['filename'], "a")
        f.write('[]') # make blank
        f.close()
    with open(SETTINGS['filename'], 'r') as inFile:
        currentQue = json.load(inFile)
        # log("Got Que",currentQue,"adding",commands)
        if currentQue == None: # if empty? or check len too
            currentQue = []    # Create empty list
            currentQue.extend(commands)
        else:
            currentQue.extend(commands)
        if handleCommand == True:
            commandHandler(currentQue) # TODO: get callback on success?
        elif handleCommand == False:
            print("Sending Queue=>", currentQue)
            outputCommandQueue(currentQue)

def commandHandler(commandQue):
    commandList = copy.copy(commandQue)
    for command in copy.copy(commandQue):
        if command['type'] in SETTINGS['internalCommands']:
            commandList.remove(command)
            handleInternalCommand(command)
    if(len(commandList) > 0):
        addToQue(commandList, False)

def handleInternalCommand(command):
    # log(command)
    if command['type'] == "import":
        try:
            downloadWorkshopItem(command)
        except:
            pass
        jsonFile = os.path.join(dir_path,"downloads",command['params'],"blueprint.json").replace("\\\\", "\\")
        print(jsonFile)
        while not os.path.exists(jsonFile):
            pass
        copyfile(jsonFile, os.path.join(SM_Location, "Survival", "LocalBlueprints", command['params']+".blueprint"))
        commandQue = []
        commandQue.extend(toJson(command))
        addToQue(commandQue, False)

def downloadWorkshopItem(command):
    startArgs = "node ./SteamWorkshopDownloader/index.js " + command['params'] + " \"" + SM_Location + "\" > log.txt"
    os.system(startArgs)
    
def generateCommand(command,price,parameter,cmdData): #Generates command dictionary
    command =  {'id': cmdData['id'], 'type':command, 'params':parameter, 'username': cmdData['author'], 
                'sponsor': cmdData['sponsor'], 'userid': cmdData['userid'], 'amount': cmdData['amount']}
    # print("Generated command:",command)
    return command

def validatePayment(command,price,message): #Validate payment data for the specified command
    if command != None: # not nexessary, just need price and message
        if SETTINGS['allFree'] or (SETTINGS['sponsorFree'] and message['sponsor']) or ((SETTINGS['fixedCost'] >0 and message['amount'] >= SETTINGS['fixedCost']) or message['amount'] >= price) :
           return True
        elif message['amount'] < price:
            print("Insuficcient payment",message['amount'],price)
            return False
        else:
            log("Payment Failed")
            return False
             
def validateCommand(parameters): # {command is a array of parameters}
    comType = str(parameters[0])
    index = None
    price = None
    errorType = None
    # if comType == None or index error then wth??
    if comType in SETTINGS['commands'] or comType in SETTINGS['internalCommands']: # Check if command valid first
        if len(parameters) == 1 or comType  in SETTINGS['single']: # a single line commnand with no extra params ex: kill, trip...
            price = SETTINGS['commands'][comType]
            if type(price) is int: #if an actual price
                return comType,index,price
            else: # the command is supposed to have a parameter
                errorType = "Invalid parameter count"
                return False,index,errorType
        elif len(parameters) == 2: # command = with parameters max params is 2 for now
            index = str(parameters[1]) # grab the next index
            # log(SETTINGS['commands'][comType])
            # log(index)
            
            if comType in SETTINGS['commands']:
                if index in SETTINGS['commands'][comType]: # IF valid item within that command
                    price =  SETTINGS['commands'][comType][index] # should be the maximum layer needed
                    return comType,index,price
            elif comType in SETTINGS['internalCommands']:
                return comType,index,int(SETTINGS['internalCommands'][comType])
            else:
                errorType = "Index Invalid"
                print("Unrecognized Index:",index)
        else:
            errorType = "Param Invalid"
            print("Too many or not enought parameters",parameters)
    else:
        errorType = "Command Invalid"
        print("unrecognized command",comType)
    return False,index,errorType # Eventually have output error message

def parseMessage(chat,mesID): # parse any messages
    comType = None
    parameter = None
    parsed = {'id': mesID, 'command': chat.message, 'author': chat.author.name, 'sponsor': chat.author.isChatSponsor, 'userid': chat.author.channelId, 'amount': chat.amountValue}
    message = parsed['command'].lower()
    # log(parsed)
    # log(message[0])

    if message[0] in SETTINGS['prefix']: # is actually a command # Possibly separate out to parsing function
        rawCommand = message.strip(message[0])
        parameters = rawCommand.split() #TODO: More validation to fix any potential mistakes
        if len(parameters) == 0:
            log("Only Recieved Prefix")
            return None
        comType,parameter,price = validateCommand(parameters)
        if comType == False:
            print("Received Error for",rawCommand+": ",price) #possibly use index for details?
        else: # Now validate any payments
            validPayment = validatePayment(comType,price,parsed)
            if validPayment:
                command = generateCommand(comType,price,parameter,parsed)
                return command
            else:
                log("Invalid Payment")
    return None
    
def readChat():
    commandQue = []
    cID = 0
    while chat.is_alive():
        # Also do stats reading/outputting
        
        with open(os.path.join(dir_path, 'JsonData', "gameStats.json"), 'r') as inFile:
            gameStats = json.load(inFile)
            # log("Got GameStats",gameStats)
        with open(os.path.join(dir_path, 'JsonData', "statOutput.txt"), 'w') as outfile:
            deaths = gameStats['deaths']
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
    jsonContent = "[ {\"id\": "+str(obj["id"])+", \"type\": \""+str(obj["type"])+"\", \"params\": \""+str(obj["params"])+"\", \"username\": \""+str(obj["username"])+"\", \"sponsor\": "+str(obj["sponsor"]).lower()+", \"userid\": \""+str(obj["userid"])+"\", \"amount\": "+str(obj["amount"])+"} ]"
    return json.loads(jsonContent)

# Planned commands: give speed, give slowness, lightning strike?, chop wood?
# chat = pytchat.create(video_id =  SETTINGS['videoID']) # start reading livechat #Create it here?? or store in settings and generate on main()

chat = None

debug = False

def log(string):
    print("["+str(string)+"]")

if __name__ == '__main__':
    if debug:
        pass
        # debug stuff here
    else:
        try:
            chat = pytchat.create(video_id=sys.argv[1])
            SETTINGS['videoID'] = sys.argv[1]
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

        copyfile(os.path.join(base,"survival_streamreader.lua"), os.path.join(smBase, "survival_streamreader.lua"))
        copyfile(os.path.join(base,"BaseWorld.lua"), os.path.join(smBase, "BaseWorld.lua"))
        copyfile(os.path.join(base,"SurvivalGame.lua"), os.path.join(smBase, "SurvivalGame.lua"))

        log("Stream Reader initializing")

        streamchatFile = open(os.path.join(smBase, "streamchat.json").replace("\\\\","\\"), "w")
        streamchatFile.write("[]")
        streamchatFile.close()
        # read/parse settings
        # path = os.getcwd()
        # log(path)
        log("Chat Reader Started")
        # start the reader
        readChat()
        # pull any erros here
