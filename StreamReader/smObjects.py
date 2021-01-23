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
from os import listdir
from os.path import isfile, join
from Scientific.Geometry import Vector

## work in progress, currently usless, and too much effort

class Blocks:
    def __init__(self, smPath):
        self.smPath = smPath
        self.blocks = {}
    def LoadBlocks(self):

        inventorydecpath = os.path.join(self.smPath, "Gui","Language","English","InventoryItemDescriptions.json");
        
        with open(inventorydecpath, 'r') as outfile:
            inventoryitemdesc = json.loads(outfile)

        with open(os.path.join(self.smPath, "Objects","Database","ShapeSets","blocks.json"), 'r') as outfile:
            blockz = json.loads(outfile)
                
        for i in range(len(blockz)):
            prop = blockz[i]
            for k in range(blockz[prop.name]):
                part = blockz[prop.name][k]
                uuid = str(part.uuid)
                name = "unnamed shape " + uuid;
                if not(inventoryitemdesc[uuid] == None):
                    name = str(inventoryitemdesc[uuid].title)
                self.blocks[uuid] = Block(self.smPath, name, "vanilla", part, None)

        ScrapShapeSets = os.path.join(self.smPath, "Objects","Database","ShapeSets")
        shapeSetFile = [f for f in listdir(ScrapShapeSets) if isfile(join(ScrapShapeSets, f))]

        for i in range(len(shapeSetFile)):
            file = os.path.join(ScrapShapeSets, shapeSetFile[i])
            with open(file, 'r') as outfile:
                parts = json.loads(outfile)
            for p in range(len(parts)):
                prop = parts[p]
                for k in range(parts[prop.name]):
                    part = parts[prop.name][k]
                    uuid = str(part.uuid)
                    name = "unnamed shape " + uuid;
                    if not(inventoryitemdesc[uuid] == None):
                        name = str(inventoryitemdesc[uuid].title)
                    self.blocks[uuid] = Part(self.smPath, name, "vanilla", part, None, True)

    def GetBlocks(self):
        return self.blocks
    
    def containsBlockId(self, uuid):
        return not self.blocks[uuid] == None

    def GetCenterOfMass(self, blueprint):
        CenterOfMass = Vector(0, 8, 2)
        bodies = blueprint.bodies
        for i in range(len(bodies)):
            for k in range(len(bodies[i].childs)):
                child = bodies[i].childs[k]
                if self.containsBlockId(str(child.shapeId)):

                    center = Vector((center.X * totalweight + point.X * weight) / tot, (center.Y * totalweight + point.Y * weight) / tot, (center.Z * totalweight + point.Z * weight) / tot)
class Block:

    def __init__(self, smLoc, name, Modname, block, desc):
        self.smLoc = smLoc
        self.name = name
        self.Modname = Modname
        self.block = block
        self.desc = desc

    def GetWeight(self, bounds):
        if not(self.weight == -1):
            return this.weight
        density = 500;
        if not(self.block.density == None):
           density = self.block.density
        weight = (int)(density * (int)(bounds.x + density) * (int)(bounds.y + density) * (int)(bounds.z));
        return weight;

class Part:

    def __init__(self, smLoc, name, Modname, block, desc, preRender):
        self.smLoc = smLoc
        self.name = name
        self.Modname = Modname
        self.block = block
        self.desc = desc
        self.preRender = preRender

    def GetWeight(self, bounds):
        if not(self.weight == -1):
            return self.weight
        density = 500
        if not(self.part.density == None):
            density = self.part.density;
        weight = (int)(density * (int)(bounds.x + density)* (int)(bounds.y + density) * (int)(bounds.z));
        return weight;