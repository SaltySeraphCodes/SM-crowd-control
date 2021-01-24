# Scrap Mechanic Crowd Control

### Command Setup
> **{ prefix }{ command }  { parameter }**

### Commands:
        
#### spawn
- Spawn entities

```diff
+0 second cooldown
```
```
totebot         
woc          
worm        
haybot        
tapebot        
redtapebot        
farmbot
```           
#### give
- Give player items
  - "give components"

```diff
+0 second cooldown
```
```
components
glowsticks
ammo
```   
#### heal
- Heal player to 100% health
  - "heal"

```diff
+20 second cooldown
```
#### shield
- 10 second invincibility
  - "shield"

```diff
+30 second cooldown
```
#### rain
- Make it rain explosives
  - "rain"

```diff
+30 second cooldown
```
#### blast
- Explodes all bots within 200 meters
  - "blast"

```diff
+60 second cooldown
```
#### kit
- Gives player specified kit
  - "kit food"

```diff
+0 second cooldown
```
```
seed        
food       
starter      
pipe     
meme
```            
#### aggro
- Aggro all nearby units to player
  - "/aggro"

```diff
+0 second cooldown
```
#### kill
- $2 Kill me instantly. use superchat with command in message
  - "kill"

```diff
+70 second cooldown
```
#### trip
- Make player trip
  - "trip" 

```diff
+45 second cooldown
```
#### slap
- Slap me in a random direction
  - "slap" 
```diff
+45 second cooldown
```
#### raid
- Spawns a random raid level
  - "raid"

```diff
+45 second cooldown
```
#### fast
- Speed me up 7 secs
  - "fast"

```diff
+30 second cooldown
```
#### slow
- Slow me down 7 secs
  - "slow"

```diff
+30 second cooldown
```
#### import
- Import creation
  - "import 123456789"
  - "import 123456789 on static"
  - "import 123456789 dynmaic"
  - "import 123456789 above"

```diff
+0 second cooldown
```
```
{ creation id } { [ on, above, right, left, front, behind ] } { [static or dynamic] }
```
#### super chat
- super chat shows up in game
```diff
+0 second cooldown
```
