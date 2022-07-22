Scrap Mechanic Crowd Control
=============

A WIP Crowd Control implementation into Scrap Mechanic
SPECIAL THANKS TO THE GUY for honestly writing a majority of the code. excellent and smart guy.
Felt bad for not using it, but we will now!

<br/>

### Command Setup ###
___
```
{prefix}{command} {parameter}
```
<br/>

### Command Prefixes ###
___
```
/
$
%
&
```
<br/>

### Commands ###
___
#### Spawn ####
```diff
+0 second cooldown
```
- Spawn entities
  - _spawn woc_
```
totebot         
woc          
worm        
haybot        
tapebot        
redtapebot        
farmbot
```           
#### Give ####
```diff
+0 second cooldown
```
- Give player items
  - _give components_
```
components
glowsticks
ammo
```   
#### Heal ####
```diff
+20 second cooldown
```
- Heal player to 100% health
  - _heal_
#### Shield ####
```diff
+30 second cooldown
```
- 10 second invincibility
  - _shield_
#### Rain ####
```diff
+30 second cooldown
```
- Make it rain explosives
  - _rain_
#### Blast ####
```diff
+60 second cooldown
```
- Explodes all bots within 200 meters
  - _blast_
#### Kit ####
```diff
+0 second cooldown
```
- Gives player specified kit
  - _kit food_
```
seed        
food       
starter      
pipe     
meme
```            
#### Aggro ####
```diff
+0 second cooldown
```
- Aggro all nearby units to player
  - _aggro_
#### Kill ####
```diff
+70 second cooldown
```
- $2 Kill player instantly. use superchat with command in message
  - _kill_
#### Trip ####
```diff
+45 second cooldown
```
- Make player trip
  - _trip_ 
#### Slap ####
```diff
+45 second cooldown
```
- Slap player in a random direction
  - _slap_ 
#### Raid ####
```diff
+45 second cooldown
```
- Spawns a random raid level
  - _raid_
#### Fast ####
```diff
+30 second cooldown
```
- Speed player up 7 secs
  - _fast_
#### Slow ####
```diff
+30 second cooldown
```
- Slow player down 7 secs
  - _slow_
#### Import ####
```diff
+0 second cooldown
```
- Import Creation
  - _import 123456789_
  - _import 123456789 on static_
  - _import 123456789 dynmaic_
  - _import 123456789 above_
```
{ creation id } { optional param } { optional param }
```
```
on
above
right
left
front
behind
```
```
static
dynamic
```
#### Super Chat ####
```diff
+0 second cooldown
```
- Super Chat shows up in game
