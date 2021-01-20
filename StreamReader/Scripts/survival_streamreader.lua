
dofile("$SURVIVAL_DATA/Scripts/game/util/Timer.lua") -- TODO: Make my own timer class that returns count and limit as well...
dofile("$SURVIVAL_DATA/Scripts/game/survival_items.lua")
dofile("$SURVIVAL_DATA/Scripts/game/survival_survivalobjects.lua")

StreamReader = class( nil )
local readClock = os.clock 

MOD_FOLDER = "$SURVIVAL_DATA/Scripts/game"

function StreamReader.sv_onCreate( self,survivalGameData )
    print("oncreate",survivalGameData)
	if sm.isHost then
		self:onCreate(survivalGameData)
	end
end
-- TODO: Stop reading commands while player is dead
function StreamReader.onCreate( self,survivalGameData ) -- Server_
    --print( "Loading Stream Reader",survivalGameData )
    self.gameData = survivalGameData
    --print('prenetwork',self.network)
    self.network = survivalGameData.network -- Needs more research
    --print("POSTNET",self.network)
    self.readRate = 1 -- Whole seconds in which to wait before reading file again
    self.started = readClock()
    self.localClock = 0
    self.gotTick = false
    self.fileName = "streamchat.json"
    self.lastInstruction = {['id']= -1}
    self.world = survivalGameData.sv.saved.overworld
    self.instructionQue = {}
    
    self.initialized = false


    -- Cooldowns and other timers
    -- CooldownLimits
    self.raidLimit = 60 -- whole seconds in which the cooldown counts
    self.killLimit = 0
    self.shieldLimit =  30 -- How long shield (invincibility) lasts
    self.healLimit = 10 -- how long to wait until player can be healed again
    self.rainLimit = 45 -- How long before the bombs can drop
    self.slapLimit = 50 
    self.tripLimit = 50
    self.blastLimit = 15
    self.spawnLimit = 10 -- Only here just in case
    self.speedLimit = 15

    self.shieldLength = 20
    self.rainLength = 1
    self.speedLength = 7
    -- cooldown counters
    self.raidCooldown = Timer()
    self.killCooldown = Timer()
    self.shieldCooldown = Timer() 
    self.healCooldown = Timer()
    self.rainCooldown = Timer()
    self.slapCooldown = Timer()
    self.tripCooldown = Timer()
    self.blastCooldown = Timer()
    self.spawnCooldown = Timer() -- Maybe not?
    self.speedCooldown = Timer()

    -- LimitedEffect Timers
    self.shieldEffect = Timer() -- five seconds?
    self.rainEffect = Timer() -- How long it rains for
    self.speedEffect = Timer() -- HOw long we be speeding

    -- Start counters
    self.raidCooldown:start(self.raidLimit)
    self.killCooldown:start(self.killLimit)
    self.shieldCooldown:start(self.shieldLimit)
    self.healCooldown:start(self.healLimit)
    self.rainCooldown:start(self.rainLimit)
    self.slapCooldown:start(self.slapLimit)
    self.tripCooldown:start(self.tripLimit)
    self.blastCooldown:start(self.blastLimit)
    self.spawnCooldown:start(self.spawnLimit)
    self.speedCooldown:start(self.speedLimit)
    self.shieldEffect:start(self.shieldLength)
    self.rainEffect:start(0)
    self.speedEffect:start(0)

    self.deathCounter = 51
    self.lives = 100 -- Just in case
    -- stats = 
    self.gameStats = { -- Not entirely sure what to put here
        deaths = 0,
        bonks = 0,
        robotKills = 0
    }
    -- states
    self.shielding = false
    self.raining = false
    self.speedEffected = false
    self.speedSet = 0 -- -1 for slow, 1 for fast
    self.playerDead = false
    self.dataChange = false
    
end

function StreamReader.server_onDestroy(self)
    print("streamreader destroy")
end

function StreamReader.server_onRefresh( self )
	print("Refresh")
end

function StreamReader.sv_onRefresh( self,survivalGameData )
    --print("ReloadingReader",survivalGameData)
    self:server_onDestroy()
    self:onCreate(survivalGameData)
end

function StreamReader.init(self)
    print("Streamreader init hehe")
end

function StreamReader.sv_readJson(self,fileName)
    --print("ReadingJson",fileName)
    

    local instructions = sm.json.open( fileName )
    if instructions ~= nil then
        --print("GotJson",instructions)
        return instructions
    else
        return nil
    end
    return instructions
end


function StreamReader.tickSeconds(self) -- ticks off every second that has passed (server)
    local now = readClock()
	local floorCheck = math.floor(now - self.started)
	if self.localClock ~= floorCheck then
        self.gotTick = true
        
        self.localClock = floorCheck

        self.raidCooldown:tick()
        self.killCooldown:tick()
        self.shieldCooldown:tick() 
        self.healCooldown:tick()
        self.rainCooldown:tick()
        self.slapCooldown:tick()
        self.tripCooldown:tick()
        self.blastCooldown:tick()
        self.spawnCooldown:tick()
        
        self.shieldEffect:tick()
        self.rainEffect:tick()
        self.speedEffect:tick()
		
	else
		self.gotTick = false
		self.localClock = floorCheck
    end
end

function searchUnitID(unit)
    local uuid = nil
    if unit == "woc" then
        uuid = unit_woc
    elseif unit == "tapebot"  then
        uuid = unit_tapebot
    elseif unit == "redtapebot" then
        uuid = unit_tapebot_red
    elseif unit == "totebot" then
        uuid = unit_totebot_green
    elseif unit == "haybot" then
        uuid = unit_haybot
    elseif unit == "worm" then
        uuid = unit_worm
    elseif unit == "farmbot"  then
        uuid = unit_farmbot
    end
    return uuid
end

function searchKitParam(kit)
    local instruct = nil
    if kit == "meme" then
        instruct = "/memekit"
    elseif kit == "seed" then
        instruct = "/seedkit"
    elseif kit == "pipe" then
        instruct = "/pipekit"
    elseif kit == "food" then
        instruct = "/foodkit"
    elseif kit == "starter" then
        instruct = "/starterkit"
    end
    return instruct
end


function searchGiveParam(give) -- Possibly combine into one gant switch?
    local item = nil
    if give == "components" then
        item = "/components"
    elseif give == "ammo"  then
        item = "/ammo"
    elseif give == "glowsticks" then
        item = "/glowsticks"
    end
    return item
end

function searchItemID(item)
    local uuid = nil
    if item == 'components' then
        uuid = obj_consumable_component
    end
    return uuid
end

function StreamReader.runInstructions(self,instructionQue)
    --print("Running Instructions",instructionQue,self.instructionQue)
    --print('final test',instructionQue)
    for k=1, #instructionQue do local instruction=instructionQue[k] -- Double check the thing
        self:runInstruction(instruction)
        self.lastInstruction = instruction
    end
end

function StreamReader.runInstruction(self,instruction) -- (Server)?
    --print("runing instruction",instruction)
    local alertmessage = ""
    if instruction == nil then
        return
    end
    local chatInstruction = "/"..instruction.type
    local chatParam = instruction.params
    local chatMessage = {chatInstruction,chatParam}
    
    if chatInstruction == "/kit" then -- Simple things
        chatMessage = {searchKitParam(chatParam)}
    elseif chatInstruction == "/raid" then
        if self.raidCooldown:done() then
            local raidlevel = math.floor(sm.noise.randomNormalDistribution(1,6))-- Randomize the raid level
            if raidlevel <=0 then raidlevel = 1  -- Handle potential negatives
            elseif raidlevel >=11 then raidlevel = 9 end -- Handle overages.
            chatMessage = {chatInstruction,tonumber(raidlevel),3} --
            self.raidCooldown:reset()
        else
            chatMessage = {chatInstruction}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/give" then
        chatMessage = {searchGiveParam(chatParam)}
    elseif chatInstruction == "/aggro" then
        chatMessage = {"/aggroall"}
    elseif chatInstruction == "/trip" then
        if self.tripCooldown:done() then
            chatMessage = {"/tumble",true}
            self.tripCooldown:reset()
        else 
            chatMessage = {"/trip"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/kill" then -- Kills Player
        if self.killCooldown:done() then
            chatMessage = {"/die"}
            self.killCooldown:reset()
        else
            chatMessage = {"/kill"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/heal" then -- heals player to 100%
        if self.healCooldown:done() then
            chatMessage = {"/sethp",100}
            self.healCooldown:reset()
        else
            chatMessage = {"/heal"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == '/spawn' then
        local spawnParams = { -- Spawn specified unit around you...
            uuid = sm.uuid.new( "00000000-0000-0000-0000-000000000000" ),
            world =self.world,
            position = self.playerLocation + sm.vec3.new(sm.noise.randomRange(-10,10),sm.noise.randomRange(-10,10),3),
            yaw = 0.0
        }
        spawnParams.uuid = searchUnitID(instruction.params) 
        self.network:sendToServer( "sv_spawnUnit", spawnParams )
    elseif chatInstruction == "/slap" then -- TODO: add paid Megaslap option?
        if self.slapCooldown:done() then
            local direction = sm.vec3.new(sm.noise.randomRange(-1,1),sm.noise.randomRange(-1,1),sm.noise.randomRange(0,1))
            local force = sm.noise.randomRange(1000,7000) 
            self.slapParams = direction * force
            self.gameData:cl_onChatCommand({"/tumble",true}) -- This is a workaround to client-server callbacks, eventually you should just add your own functions to survivalGame
            self.slapCooldown:reset()
        else
            chatMessage = {"/slap"}
            chatInstruction = "cooldown"
        end

    elseif chatInstruction == "/shield" then -- Grant brief invincibility TODO: add effect on player to show shield
        if self.shieldCooldown:done() then
            self.shieldEffect:reset()
            self.shieldEffect:start(self.shieldLength)
            self.shieldCooldown:reset()
        else
            chatMessage = {"/shield"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/rain" then -- Make it rain explosives
        if self.rainCooldown:done() then
            self.rainEffect:reset()
            self.rainEffect:start(self.rainLength)
            self.rainCooldown:reset()
        else
            chatMessage = {"/rain"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/slow" then
        if self.speedCooldown:done() then
            self.speedEffect:reset()
            self.speedEffect:start(self.speedLength)
            self.speedSet = -1
            self.speedCooldown:reset()
        else
            chatMessage = {"/slow"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/fast" then
        if self.speedCooldown:done() then
            self.speedEffect:reset()
            self.speedEffect:start(self.speedLength)
            self.speedSet = 1
            self.speedCooldown:reset()
        else
            chatMessage = {"/fast"}
            chatInstruction = "cooldown"
        end
    elseif chatInstruction == "/blast" then
        if self.blastCooldown:done() then
            if not self.blast then
                self.blast = true
            end
            self.blastCooldown:reset()
        else
            chatMessage = {"/blast"}
            chatInstruction ="cooldown"
        end
    elseif chatInstruction == "/import" then
        self.gameData:cl_importCreation(chatParam)
    end
    if chatInstruction == "cooldown" then
        print("is on cooldown")
        alertmessage = chatMessage[1] .. " Is on cooldown" -- alert player name? just say "/spawn failed"?
    elseif chatInstruction ~= "/spawn" and chatInstruction ~= "/import" then
        --print("running",chatInstruction)
        self.gameData:cl_onChatCommand(chatMessage)
    end

    local usernameColor = "#ff0000"
    local textColor = "#ffffff"
    local moneyColor = "#aaaa00"
   
    -- Alert messages
    local showPayments = (self.showPayments or false) -- TODO: Move to actual configuration
    if chatInstruction ~= "cooldown" then -- TODO: separate to different function(*s)
        if showPayments then
            if instruction.type == "spawn" then
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to spawn a "..instruction.params
            elseif instruction.type == 'give' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to give you "..instruction.params
            elseif instruction.type == 'kit' then 
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to give you a "..instruction.params.. " kit"
            elseif instruction.type == 'raid' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to spawn a level "..chatMessage[2] .. " raid."
            elseif instruction.type == 'aggro' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to aggro all nearby enemies"
            elseif instruction.type == 'kill' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to kill you... goodbye"
            elseif instruction.type == 'trip' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." paid "..moneyColor..instruction.amount.." "..textColor.."to trip you"
            end
        else
            if instruction.type == "spawn" then
                alertmessage = usernameColor..instruction.username.." "..textColor.." spawned a "..instruction.params
            elseif instruction.type == 'give' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." gave you "..instruction.params
            elseif instruction.type == 'kit' then 
                alertmessage = usernameColor..instruction.username.." "..textColor.." gave you a "..instruction.params.. " kit"
            elseif instruction.type == 'raid' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." spawned a level "..chatMessage[2] .. " raid."
            elseif instruction.type == 'aggro' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." aggrovated all nearby enemies"
            elseif instruction.type == 'kill' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." killed you... goodbye"
            elseif instruction.type == 'trip' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." tripped you"
            elseif instruction.type == 'slap' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." slapped you"
            elseif instruction.type == 'shield' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." is protecting you"
            elseif instruction.type == 'rain' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." made it rain"
            elseif instruction.type == 'heal' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." healed you"
            elseif instruction.type == 'blast' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." blasted all bots"
            elseif instruction.type == 'speed' then
                local suffix = "changed Your Speed"
                if self.speedSet == -1 then
                    suffix = "slowed you down"
                elseif self.speedSet == 1 then
                    suffix = "sped you up"
                end
                alertmessage = usernameColor..instruction.username.." "..textColor..suffix
            elseif instruction.type == 'speed' then
                alertmessage = usernameColor..instruction.username.." "..textColor.." imported a creation"
            end
        end
    end
    if instruction ~= nil then
        print("Ran Instruction:",instruction.type)
    end
    --local testMessge = "#ff0000Hello"
    sm.gui.chatMessage( alertmessage )
end

function StreamReader.sv_importCreation(importParams)
    sm.creation.importFromFile( importParams.world, "$SURVIVAL_DATA/LocalBlueprints/"..importParams.name..".blueprint", importParams.position )
end

-- Misc funtions
function StreamReader.cl_awaitSlap(self) -- Waits for character to be tumbling before applying impulse
    if self.slapParams ~= nil then
        self.player.character:applyTumblingImpulse( self.slapParams) -- TODO: add hit effect
        self.slapParams = nil -- delete to fly lol
    else
        return
    end
end

function StreamReader.cl_changeSpeed(self)
    local speed = 1
    --print(self.speedEffect:done(),self.speedEffected)
    if not self.speedEffect:done() and not self.speedEffected then
        if self.speedSet == 1 then 
            speed = 6
        elseif self.speedSet == -1 then
            speed = 0.4
        else
            speed = 1
        end
        sm.gui.chatMessage("Starting Speed Change")
        self.player.character:setMovementSpeedFraction( speed )-- TODO: use this to add speed/slow/reversed controls
        self.speedEffected = true
    elseif self.speedEffect:done() and self.speedEffected then
        sm.gui.chatMessage("Stopping Speed CHange")
        self.player.character:setMovementSpeedFraction(1) -- or default
        self.speedSet = 0
        self.speedEffected = false
    elseif self.speedEffect:done() and not self.speedEffected then
        if self.player.character ~=  nil then
            self.player.character:setMovementSpeedFraction(1) -- or default
        end
        self.speedSet = 0
    end
end

function  StreamReader.cl_shield(self) -- Shileds player while shiledEffect timer is not done
    --print(self.survivalGameData)
    
    if not self.gameData then return end -- maubeunecessary...
    if not self.shieldEffect:done() and not self.shielding then
        --self.gameData:cl_shield({character = self.player.character, position = self.playerLocation}) -- in case I want effects to wotk (sm.sendToPlayer)
        self.network:sendToServer( "sv_switchGodMode" ) -- need better way to do this...
        self.shielding = true
        sm.gui.chatMessage("#00ff00Shield Started")
    elseif self.shieldEffect:done() and self.shielding then
        self.shielding = false
        self.network:sendToServer( "sv_switchGodMode" )
        sm.gui.chatMessage("#ff0000Shield Stopped")
    end
    -- body
end

function StreamReader.sv_rain(self,params) -- calls rain event from/to server
    if not self.world then return end -- maubeunecessary...
    if not self.rainEffect:done() and not self.raining then
        print("Making it rain")
        sm.event.sendToWorld( self.world, "sv_e_onChatCommand", {"/rain",location = self.playerLocation} ) -- Add Item command? -- need better way to do this...
        self.raining = true
        --sm.gui.chatMessage("#ff0000Prepare For Rain")
    elseif self.rainEffect:done() and self.raining then
        self.raining = false
        --[[local bodies = sm.body.getAllBodies()
        for _, body in ipairs( bodies ) do
			local usable = body:isUsable()
			if usable then 
				local shape = body:getShapes()[1]
				if shape:getShapeUuid() == obj_interactive_propanetank_small or  shape:getShapeUuid() == obj_interactive_propanetank_large then
					sm.physics.explode( shape:getWorldPosition() , 7, 2.0, 6.0, 25.0, "RedTapeBot - ExplosivesHit" )
				end
			end
			--print(shape)
		end]]
        --sm.gui.chatMessage("#00ff00RainStopped")
    end
end

function StreamReader.sv_blast(self)-- Destroys all units arroung?
    if not self.blast then return end
    sm.event.sendToWorld( self.world, "sv_e_onChatCommand", {"/blast",location = self.playerLocation} ) -- Add Item command? -- need better way to do this...
    self.blast = false
end

function StreamReader.readFileAtInterval(self,interval) --- Reads specified file at interval (sever?)
    if self.gotTick and self.localClock % interval == 0 then -- Everysecond...
       
        local jsonData = self:sv_readJson(MOD_FOLDER.."/"..self.fileName)
        --print("Reading json",jsonData)
        if jsonData == nil or jsonData == {} or not jsonData or #jsonData == 0 or jsonData == "{}" then
            --print("NO data")
            return
        end
    
        local lastInstructionID = jsonData[#jsonData].id
        if self.lastInstruction == nil or lastInstructionID ~= self.lastInstruction.id then
            self.recievedInstruction = true
            --print("Got new instructions",lastInstructionID,self.lastInstruction.id)
            -- Only append instructions that are > than lastInstruction
            for i,j in pairs(jsonData) do
                if self.lastInstruction == nil or j.id > self.lastInstruction.id then
                    --print("using",j)
                    table.insert(self.instructionQue,j)
                else
                    --print("rejected",j)
                end
            end
            --self.instructionQue = jsonData -- Or should I append the new data?
            self.lastInstruction = self.instructionQue[#self.instructionQue]
        end
    end
end

function clearTable(table,lastID)
    for k = 0, lastID do
        for i, j in pairs(table) do
            if k == j.id then
                --print("removing",k)
                table[i] = nil
                --table.remove(table, j)
            end
        end
    end
    --print("Trimmed instructions",table)
    return table
end

function StreamReader.clearInstructions(self)-- Clears the json file of stuff
    local path = MOD_FOLDER.."/"..self.fileName
    local lastInstructions =  self:sv_readJson(path)
    if lastInstructions == nil or self.lastInstruction == nil then -- Shorcut this error
        print("no last instruction",self.lastInstruction)
        return
    end
    local lastInstructionID = self.lastInstruction.id
    local clearedTable = clearTable(lastInstructions,lastInstructionID)
    if clearedTable == nil or clearedTable == {} then
        clearJson = "[]"
    else
        clearJson = clearedTable
    end
    self.instructionQue = clearedTable
	sm.json.save(clearJson, path )
end

function StreamReader.sv_onFixedUpdate( self, timeStep )    
    -- Server awaiting
    if self.initialized then
        self:readFileAtInterval(self.readRate)
        self:tickSeconds()
        self:sv_rain()
        self:sv_blast()
    end
    if self.dataChange then -- output stats to json
        print("dataChange",self.gameStats)
        self:outputData(self.gameStats)
        self.dataChange = false
    end
end

function StreamReader.cl_onFixedUpdate( self, timeStep )
    if self.initialized then
        local dead = self.player:getCharacter():isDowned()
        if dead and not self.playerDead then
            self.deathCounter = self.deathCounter + 1
            self.gameStats.deaths = self.deathCounter -- probably unecessary, could consolidate
            self.playerDead = true
            sm.gui.chatMessage("#ffff00You have died #ff0000" .. self.deathCounter .. " #ffff00times")
            self.dataChange = true
        elseif not dead and self.playerDead then
            self.playerDead = false 
        end
    end


    self.move = 0
    local player = sm.localPlayer.getPlayer()
    if self.player == nil then self.player = player end
    if player ~= nil then
        local char = player.character
    
        if char ~= nil then
            local pos = char:getWorldPosition()
           
            local dir = char:getDirection()
            local tel = pos + dir * 5
            local cellX, cellY = math.floor( tel.x/64 ), math.floor( tel.y/64 )
			local telParams = {cellX,cellY,player,tel}
            --self.network:sendToServer( "sv_teleport", telParams )
            if pos ~= nil then -- check type too?
                self.playerLocation = pos
                if not self.initialized then -- everything is loaded
                    self.initialized = true
                    print("StreamReader Initialized")
                end
            end
        end
    end
    -- Await async Functions here
    self:cl_awaitSlap()
    self:cl_shield()
    self:cl_changeSpeed()
    if self.recievedInstruction then
        --print("recieved instructions",self.instructionQue)
        --local success, message = pcall(self:runInstructions(), self.instructionQue)  USE THIS WHEN Confidently finished
        --print("Instruction result",success,message)
        self:runInstructions(self.instructionQue)
        self:clearInstructions()
        self.recievedInstruction = false   
    end
    --print(self.playerLocation) 
end

function StreamReader.outputData(self,data) -- writes data to json file
    local filename = "gameStats.json"
    local path = MOD_FOLDER.."/"..filename
    print("saving:",data)
    sm.json.save(data,path)

end