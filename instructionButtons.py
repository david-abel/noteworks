from cocos import euclid, collision_model
from cocos.layer.base_layers import Layer
from cocos.sprite import Sprite
from utils import aabb_to_aa_rect
from constants import *
import os
import pyglet

class BackButton(Sprite):
	def __init__(self,x,y):
		super(BackButton, self).__init__(os.path.join("images", "instructions", "back_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class BackButtonUD(Sprite):
	def __init__(self,x,y):
		super(BackButtonUD, self).__init__(os.path.join("images", "instructions", "back_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class UnitDetailsButton(Sprite):
	def __init__(self,x,y):
		super(UnitDetailsButton, self).__init__(os.path.join("images", "instructions", "unit_description_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class ControlsButton(Sprite):
	def __init__(self,x,y):
		super(ControlsButton, self).__init__(os.path.join("images", "instructions", "controls_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class TechTreeButton(Sprite):
	def __init__(self,x,y):
		super(TechTreeButton, self).__init__(os.path.join("images", "instructions", "tech_tree_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class AttackTroopDetailsButton(Sprite):
	def __init__(self,x,y):
		super(AttackTroopDetailsButton, self).__init__(os.path.join("images", "instructions", "attack_troop_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class UtilityTroopDetailsButton(Sprite):
	def __init__(self,x,y):
		super(UtilityTroopDetailsButton, self).__init__(os.path.join("images", "instructions", "utility_troop_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position

class BuildingsDetailsButton(Sprite):
	def __init__(self,x,y):
		super(BuildingsDetailsButton, self).__init__(os.path.join("images", "instructions", "building_details_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position
		
class ResourceDetailsButton(Sprite):
	def __init__(self,x,y):
		super(ResourceDetailsButton, self).__init__(os.path.join("images", "instructions", "resource_button.png"))
		self.position = x,y
		self.cshape = aabb_to_aa_rect(self.get_AABB())
		self.cshape.center = self.position



