import pytchat # most recent thing in the core is the updated stuff
import time
import json
import os


# Import settings? for now have global settings
# TODO: Money pool to allow viewers to donate to a common goal
SETTINGS = {
    'allFree': False, # make everything freee
    'sponsorFree': True, #channel sponsors get free commands
    'fixedCost': 0, # if >0 and allFree == false, all commands will cost this price
    'interval': 1, #rate in which to check for new commands, BROKEN until fixed...
    'prefix': ['!','/','$','%'],
    'filename': 'streamchat.json',
    'videoID': "2foo8cmrXjs",
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
    'single': ['raid', 'fast', 'slow','heal','shield','blast','trip','slap','aggro','rain'] #uneccesary but list of all commands
}
#Planned commands: give speed, give slowness, lightning strike?, chop wood?
chat = pytchat.create(video_id =  SETTINGS['videoID']) # start reading livechat #Create it here?? or store in settings and generate on main()

def outputCommandQueue(commandQue):
    with open(SETTINGS['filename'], 'w') as outfile:
        jsonMessage = json.dumps(commandQue)
        #print("Writing commands",jsonMessage)
        outfile.write(jsonMessage)

def addToQue(commands): # adds to the already existing command que
    #CHeck if exists first
    #print("addQWue",commands)
    if not os.path.exists(SETTINGS['filename']):
        f = open(SETTINGS['filename'], "a")
        f.write('[]') #make blank
        f.close()
    with open(SETTINGS['filename'], 'r') as inFile:
        currentQue = json.load(inFile)
        #print("Got Que",currentQue,"adding",commands)
        if currentQue == None: # if empty? or check len too
            currentQue = [] # Create empty list
            currentQue.extend(commands)
        else:
            currentQue.extend(commands)
    outputCommandQueue(currentQue) # TODO: get callback on success?

def generateCommand(command,price,parameter,cmdData): #Generates command dictionary
    command =  {'id': cmdData['id'], 'type':command, 'params':parameter, 'username': cmdData['author'], 
                'sponsor': cmdData['sponsor'], 'userid': cmdData['userid'], 'amount': cmdData['amount']}
    print("Generated command:",command)
    return command

def validatePayment(command,price,message): #Validate payment data for the specified command
    if command != None: # not nexessary, just need price and message
        if SETTINGS['allFree'] or (SETTINGS['sponsorFree'] and message['sponsor']) or ((SETTINGS['fixedCost'] >0 and message['amount'] >= SETTINGS['fixedCost']) or message['amount'] >= price) :
           return True
        elif message['amount'] < price:
            print("Insuficcient payment",message['amount'],price)
            return False
        else:
            print("Payment Failed")
            return False
             
def validateCommand(parameters): # {command is a array of parameters}
    comType = str(parameters[0])
    index = None
    price = None
    errorType = None
    # if comType == None or index error then wth??
    if comType in SETTINGS['commands']: # Check if command valid first
        if len(parameters) == 1 or comType  in SETTINGS['single']: # a single line commnand with no extra params ex: kill, trip...
            price = SETTINGS['commands'][comType]
            if type(price) is int: #if an actual price
                return comType,index,price
            else: # the command is supposed to have a parameter
                errorType = "Invalid parameter count"
                return False,index,errorType
        elif len(parameters) == 2: # command = with parameters max params is 2 for now
            index = str(parameters[1]) #grab the next index
            print(SETTINGS['commands'][comType])
            print(index)
            
            if index in SETTINGS['commands'][comType]: # IF valid item within that command
                price =  SETTINGS['commands'][comType][index] #should be the maximum layer needed
                return comType,index,price
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
    #print(parsed)
    #print(message[0])

    if message[0] in SETTINGS['prefix']: # is actually a command # Possibly separate out to parsing function
        rawCommand = message.strip(message[0])
        parameters = rawCommand.split() #TODO: More validation to fix any potential mistakes
        if len(parameters) == 0:
            print("Only Recieved Prefix")
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
                print("Invalid Payment")
    return None
    
def readChat():
    commandQue = []
    cID = 0
    while chat.is_alive():
        # Also do stats reading/outputting
        
        with open("gameStats.json", 'r') as inFile:
            gameStats = json.load(inFile)
            #print("Got GameStats",gameStats)
        with open("statOutput.txt", 'w') as outfile:
            deaths = gameStats['deaths']
            output = "Deaths: {:.0f}".format(deaths)
            outfile.write(output)
            #print("outputing",output)

        for c in chat.get().sync_items():
            #print(c.datetime,c.author.name,c.message)
            command = parseMessage(c,cID)
            if command != None:
                commandQue.append(command)
                cID +=1
            if len(commandQue) >0:
                addToQue(commandQue)
            time.sleep(1)
        commandQue = []
        try:
            chat.raise_for_status()
        except Exception as e:
            print(type(e), str(e))


def main():
    print("Stream Reader initializing")
    # read/parse settings
    #path = os.getcwd()
    #print(path)
    os.chdir('./JsonData')
    #path = os.getcwd()
    #print(path)
    print("Reading Chat")
    readChat()#start the reader
    #pull any erros here





main()