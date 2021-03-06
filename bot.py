#From https://realpython.com/how-to-make-a-discord-bot-python/
import os
import discord
from dotenv import load_dotenv

#Question Class to have helpful methods for interacting with a question.
class question:
    def __init__(self, content, resType, options):
        self.content = content
        self.resType = resType
        self.options = options
        for option in self.options:
            option = option.replace('\n','')

    def __repr__(self): 
        toRet= f"\n ❓ Question Number {qNum} ❓ :\n  \n{self.content}\n"
        for option in self.options:
            toRet = f"{toRet}{option}\n"
        toRet += f"\nResponse: ➡️ (?): {None} ⬅️"
        toRet += f"\nGuess: ↪️ (?): {None} ↩️"
        return toRet

    def getUpdatedString(self, channel):
        respInput = None
        guessInput = None
        rSymbol = '?'
        resp = None
        gSymbol = "?"
        guess = None

        if channel in responses:
            respInput = responses[channel][0]
            rSymbol = whichResponseSymbol(respInput)
            resp = whichResponseFull(respInput)

        if channel in plurality:
            guessInput = plurality[channel][0]
            gSymbol = whichResponseSymbol(guessInput)
            guess = whichResponseFull(guessInput)

        toRet= f"\n ❓ Question Number {qNum} ❓ :\n  \n{self.content}\n"
        for option in self.options:
            toRet = f"{toRet}{option}\n"
        toRet += f"\nResponse: ➡️ ({rSymbol}): {resp} ⬅️"
        toRet += f"\nGuess: ↪️ ({gSymbol}): {guess} ↩️"
        return toRet

    def getResponses(self):
        toRet = []
        for option in self.options:
            posL = option.find("(")
            posR = option.find(")")
            toRet.append(option[posL+1:posR])
        return toRet

    def getResponsesFull(self, messageContent):
        response = whichResponseSymbol(messageContent)
        for option in self.options:
            posL = option.find("(")
            posR = option.find(")")
            if(response in option[posL+1:posR]):
                return(option[posR+2:])

    def getOptions(self):
        toRet = ""
        for option in self.options:
            toRet = f"{toRet}{option}\n"
        return toRet

#Get token/Guild name
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
GM = os.getenv('DISCORD_GM')

'''
playerIds = [
127250286686240768,
471433592455561226,
224698087652851712,
164545381332418560,
237633696713277450,
236913614840135680,
449014739679576066,
223584013800046593,
240259771280654338,
239114620915154944,
234714326940909580,
236918813143072779
]'''

'''
silverSurferPlayerChannels = [
818680360325611590,
818680662693118004,
818680477313400892,
818680492890914836,
818680606770200586,
818681158715310122,
818680546167095306,
818680630748512307,
832368804851220509,
818680576604635186,
818680509214883870,
818680521856122910,
832041499985575946]
'''

GENERAL_CHAT = 838884093936402477

playerIds = [
682563694924005396,
72878956226818048,
178366248634155008,
223584013800046593,
162746564610228225,
196092454217187328,
408092024592531456,
478024554447634447,
690741345022902274,
412773820546678794
]

playerChannels = [
839199273161850910,
839199282757107742,
839675180552290324,
839199294992941058,
839199303352320050,
839199310633893908,
839199158057566209,
839199185436803103,
839199318594027530,
839199253989818388,
839199263212961842
]

#Give the bot all power and permissions
intents = discord.Intents().all()
client = discord.Client(prefix=',',intents=intents)

guild = None

#Save the question number for display reason
qNum = 0

#Save the most recent question
lastQuestion = None

#Dictionaries for tracking
#Messages save the most recent bot message to edit them for user experience reasons
messages = {}
responses = {}
plurality = {}

#0 means waiting on user response, 1 not waiting on response, tells the bot when to listen to user responses
state = 0

questionFile = open('C:/Users/Firel/Desktop/Coding/PollBot/fq.txt','r')

@client.event
async def on_ready():
    global guild
    guild = discord.utils.get(client.guilds, name=GUILD)
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

@client.event
async def on_member_join(member):
    print(f'{member.name} joined.')


@client.event
async def on_reaction_add(reaction,user):
    if user != client.get_user(813253594227933225):
        responses.pop(reaction.message.channel, None)
        plurality.pop(reaction.message.channel, None)
        await reaction.message.edit(content=f"{lastQuestion}")
        await reaction.message.remove_reaction('🔄', user)
        printLeftover()


@client.event
async def on_message(message):
    #Make sure to not respond to own messages
    if message.author == client.user:
        return

    #Needed to allow the Gm to play while controlling the bot from a single channel
    flag = True

    #GameMaster commands
    if int(message.author.id) == int(GM):
        print(f"Recieved {message.content} from GM {message.author}")
        flag = await gmCommand(message)

    #Player response
    if flag and message.channel.id in playerChannels:
        print(f"Recieved {message.content} from {message.author}")
        await playerResponse(message)

async def gmCommand(message):
    global qNum
    global state
    global lastQuestion
    global responses
    global messages

    #next question command, alternates sending question or sending the results of the questions
    if message.content.startswith('.'):
        if state == 0:
            await sendNextQuestion()
        elif state == 1:
            await sendResults()
        return False

    #mute all non GM users in General Chat
    elif message.content.startswith('mute'):
        for id in playerIds:
            member = guild.get_member(id)
            if member in guild.get_channel(GENERAL_CHAT).members:
                await member.edit(mute = True)
        return False

    #unmute all members
    elif message.content.startswith('unmute'):
        for id in playerIds:
            member = guild.get_member(id)
            if member in guild.get_channel(GENERAL_CHAT).members:
                await member.edit(mute = False)
        return False

    #jump to question number x. Usage: goto x
    elif message.content.startswith('goto'):
        split = message.content.split(" ") 
        if(split[1].isnumeric()):
            responses = {}
            plurality = {}
            state = 1
            qNum = int(split[1])
            f.seek(0,0)
            count = 0
            line = ""
            while(qNum != count):
                print(line)
                line = questionFile.readline()
                if ';' in line:
                    count = count+1
            lastQuestion = parseQuestion(line)
            for chanId in playerChannels:
                pChan = client.get_channel(chanId)
                await pChan.send(lastQuestion)
        return False

    #skip everything but question part
    elif message.content.startswith('next'):
        responses = {}
        plurality = {}
        await sendNextQuestion()
        return False

    #clears all messages in all player channels. Mainly useful for testing purposes
    elif message.content.startswith('clear'):
        for chanId in playerChannels:
            channel = client.get_channel(chanId)
            await channel.purge()
        return False
    return True

async def sendNextQuestion():
    global state
    global messages
    global responses
    global plurality
    global qNum
    global lastQuestion

    messages = {}
    responses = {}
    plurality = {}
    state = 1
    qNum = qNum + 1

    #Skip lines not properly formatted for questions,
    # not perfect but allows titles and comments in the .txt file
    line = questionFile.readline()
    while ';' not in line:
        line = questionFile.readline()
    print(line)

    lastQuestion = parseQuestion(line)

    '''
    Multiple for loops to send the question and then to react to it.
    While innefficient this is due to the built in delay on reactions
    enforced on discord bots. This shows the questions to all users 
    before reacting.
    '''
    for chanId in playerChannels:
        pChan = client.get_channel(chanId)
        message = await pChan.send(lastQuestion)
        messages[pChan] = message

    for chanId in playerChannels:
        pChan = client.get_channel(chanId)
        message = messages[pChan]
        await message.add_reaction('🔄') 

    #Question type dc (discussion) need no responses
    if lastQuestion.resType == 'dc':
        state = 0

    return True

#Build the results message
async def sendResults():
    global responses
    global plurality
    global state
    state = 0
    resultsDict = {}
    
    for response in lastQuestion.getResponses():
        resultsDict[response] = []

    for response in responses:
        print(response,responses[response])
        tempResponse = whichResponseSymbol(responses[response])
        resultsDict[tempResponse].append(response)

    toSend = f" 📊 Results for Question {qNum} 📊 :\n  \n❓ Anwsers ❓\n"
    maxVotes = 0
    for key in resultsDict:
        if len(resultsDict[key]) > maxVotes:
            maxVotes = len(resultsDict[key])
        toSend +=f"{whichResponseFull(key)} ({len(resultsDict[key])})|"
        for channel in resultsDict[key]:
            tempChannel = channel.name[0].upper()+channel.name[1:]
            toSend +=f" {tempChannel},"

        #Drop a garbage character 
        toSend = toSend[:-1]
        toSend +="\n"

    toSend = toSend + " \n🗳️ Plurality 🗳️\n"

    maxKeys = []
    for key in resultsDict:
        if len(resultsDict[key]) == maxVotes:
            maxKeys.append(key)

    resultsDict = {}
    for tempResponse in lastQuestion.getResponses():
        resultsDict[tempResponse] = []
    for pluralityResp in plurality:
        tempResponse = whichResponseSymbol(plurality[pluralityResp])
        resultsDict[tempResponse].append(pluralityResp)

    for key in maxKeys:
        toSend +=f"🎈 {whichResponseFull(key)} 🎈 ({len(resultsDict[key])}) |"
        for channel in resultsDict[key]:
            tempChannel = channel.name[0].upper()+channel.name[1:]
            toSend +=f" {tempChannel},"
        toSend = toSend[:-1]
        toSend +=f"\n"

    for key in resultsDict:
        if key not in maxKeys:
            toSend +=f"💢 {whichResponseFull(key)} 💢 ({len(resultsDict[key])}) |"
            for channel in resultsDict[key]:
                tempChannel = channel.name[0].upper()+channel.name[1:]
                toSend +=f" {tempChannel},"
            toSend = toSend[:-1]
            toSend +=f"\n"
        
    for chanId in playerChannels:
        pChan = client.get_channel(chanId)
        await pChan.send(toSend)

    responses = {}
    plurality = {}

async def playerResponse(message):
    resp = message.content[0]
    if message.channel not in responses:
        if await testResponse(resp,message.channel):
            if message.channel in messages:
                oldMess = messages[message.channel]
                await oldMess.edit(content=lastQuestion.getUpdatedString(message.channel))

    elif message.channel not in plurality:
        if await testGuess(resp,message.channel):
            if message.channel in messages:
                oldMess = messages[message.channel]
                await oldMess.edit(content=lastQuestion.getUpdatedString(message.channel))
    printLeftover()

async def testResponse(message, messageChannel):
    global responses
    if acceptableResponse(message):
        await messageChannel.send(f"You sent \"{message}\" as your response which means you responded \"{whichResponseFull(message)}\"\n")
        responses[messageChannel] = message
        return True
    else:
        await messageChannel.send(f"\"{message}\" is not in the available responses. Please respond with a message that only contains one of {lastQuestion.getResponses()}")
        return False

async def testGuess(message, messageChannel):
    global plurality
    if acceptableResponse(message):
        await messageChannel.send(f"You sent \"{message}\" as your guess which means you guessed {whichResponseFull(message)}")
        plurality[messageChannel] = message
        return True
    else:
        await messageChannel.send(f"\"{message}\" is not in the available guesses. Please respond with a message that only contains one of {lastQuestion.getResponses()}")
        return False

def hasNotSent(messageChannel,array):
    return messageChannel in array

def whichResponseSymbol(messageContent):
    for response in lastQuestion.getResponses():
        if response in messageContent.upper():
            return response

def whichResponseFull(messageContent):
    return lastQuestion.getResponsesFull(messageContent)


def acceptableResponse(messageContent):
    response = messageContent[0]
    if lastQuestion:
        for response in lastQuestion.getResponses():
            if response in messageContent.upper():
                return True
    return False

#If there are 3 or less players who have not responded tell the gm who through the console
def printLeftover():
    if len(playerChannels) - len(plurality) <= 3 and len(playerChannels) - len(plurality) != 0:
        toRet = "Have not Responded fully:"
        for channel in playerChannels:
            pChan = client.get_channel(channel)
            if pChan not in plurality:
                toRet += f"| {pChan} "
        print(toRet)

def parseQuestion(formattedQuestion):
    split = formattedQuestion.split(';')
    if len(split) > 0:
        if split[1].startswith('yn'):
            return question(split[0],split[1],['(Y) Yes','(N) No'])
        elif split[1].startswith('mc'):
            return question(split[0],split[1],split[2:])
        elif split[1].startswith('fg'):
            return question(split[0],split[1],['(A) Andrew','(B) Austin','(C) Ben','(D) Chris','(E) Cooper','(F) Emily','(G) JohnLee','(H) Max','(I) Pega','(J) Silver','(K) Simon'])
        elif split[1].startswith('dc'):
            return question(split[0],split[1],[])
    return question("Something went wrong.","",["(1) Please Hold"])

def parsePopularity(question):
    return f""" 🗳️ Popularity for Question {qNum} 🗳️ :\n  \n Did the plurality of people vote for \n{question.getOptions()} for the question \n\"{question.content}\""""

client.run(TOKEN)   

