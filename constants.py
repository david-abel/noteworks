'''
constants.py
stores any variables that are constant to the entire game
'''

from pyglet.window import key

'''GAME OPTIONS'''
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
FULL_SCREEN = True
MAP_FILE = "level1.map"
SHOW_TUTORIAL = True
SCROLL_CONST = 1000
DEFAULT_ACTION_DURATION = 10
BLEED = 200.0
STATUS_BAR_HEIGHT = 70
SOUND = True
MUSIC = True

MULTIPLAYER = False

DEFAULT_MAP = "level1"
DEFAULT_MULT_MAP = "mult2"

BUILDING_HOTKEYS = {
    key.Q: 7,  # Q
    key.W: 3,  # W
    key.E: 5,  # E
    key.A: 1,  # A
    key.D: 0,  # D
    key.Z: 6,  # Z
    key.X: 2,  # X
    key.C: 4,  # C
}

TROOP_HOTKEYS = {
    key.A: 0,  # A
    key.S: 1,  # S
    key.D: 2  # D
}

'''MENU OPTIONS'''
BUTTON_FONT_HEIGHT = 24
ACTION_BUTTON_WIDTH = 40

'''MULTIPLAYER OPTIONS'''
#SERVER_IP = "137.22.234.214"
#SERVER_IP="10.0.1.2"
#SERVER_IP = "137.22.30.170"
#SERVER_IP = "137.22.167.19"
SERVER_IP = "137.22.30.15"

'''COLORS_OPTIONS'''
GAME_BG_COLOR = (255, 255, 255)
EDGE_COLOR = (80, 80, 80, 155)
AS_EDGE_COLOR = (80, 80, 130, 155)
MAP_BG_COLOR = (255, 255, 255)
PLAYER_COLORS = [(200,30,30),(60,60,60),(168,107,57),(34,101,101)]
#PLAYER_COLORS = [(255,255,255),(255,255,255),(255,255,255),(255,255,255)]
AS_COLORS = [(155, 155, 155), (100, 100, 100),(155, 155, 155),(155, 155, 155),(155, 155, 155),(155, 155, 155)]
ADJ_EDGE_COLOR = (80, 130, 80, 155)
'''UNIT_OPTIONS'''

UNIT_SCALE_NORMAL = 1.0
UNIT_SCALE_SELECTED = 1.2

TIMER_SCALE = 0.3

UNIT_STARTING_OPACITY = 100

DECRYPT_DURATION = 3


'''MAP_OPTIONS'''
MAP_SCROLL_SPEED = 512
MAP_MOUSE_SCROLL_SPEED = 512
SLOT_RADIUS = 55.4

TIMER_X_OFFSET = 15
TIMER_Y_OFFSET = 15

ACTIONMENU_X_OFFSET = 90
ACTIONMENU_Y_OFFSET = 5

NUM_OF_SLOTS = 4
ANGLE_MULTIPLIER = 4.9

HALF_VISIBLE = 0.6  # opacity of 0.6 is half visible

AS_OPACITY = 1  # maximum AS opacity
AS_SCALE = 0.4
AS_EDGE_WIDTH = 6

TROOP_SLOT_SCALE = 0.7

MINIMAPCIRCLE_OPACITY = 200

HIGHLIGHTED_VERTEX_COLOR = (220,120,220)
VERTEX_COLOR = (255,255,255)

'''TIMING_OPTIONS'''
UNIT_SLOT_TO_VERTEX_SPEED = 0.1  # num of seconds it takes for a unit to move from a slot to a vertex
LEVEL1 = 10  # time research takes at LEVEL<n>
LEVEL2 = 20
LEVEL3 = 30
LEVEL4 = 40

'''Z-INDEX'''
TIMER_Z = 11
PACKET_Z = 2
BUILDING_Z = 8
TROOP_Z = 7
SLOT_Z = 3
VERTEX_Z = 3
EDGE_Z = 1
AS_CIRCLE_Z = 0
BACKGROUND_Z = -1
MINMAP_CIRCLE_Z = 11
RSA_Z = 8
MENU_BUTTON_Z = 10
ACTION_MENU_Z = 9


'''TEST_OPTIONS'''
CELL_SIZE = 124  # will change to reflect diameter of vertex sprite (or slightly larger...)
BUILD_OFFSET_X = 35
BUILD_OFFSET_Y = 50
# for testing, center of a unit relative to the bottom left of the unit
UNIT_SIZE = 5

TEST_SPEEDUP = 4.0  # time multiplier for testing purposes

BUTTON_DICTIONARY = {
    'TAPTGet' : 'apt-get_action_button.png',
    'TInstaller' : 'installer_action_button.png',
    "TPing": "ping_action_button.png",
    "TDOS":"dos_action_button.png",
    "TSQL":"sql_action_button.png",
    "TDNSPoison":"dns_action_button.png",
    "TBufferOverflow":"bufferflow_action_button.png",
    "TSQLInjection":"sql_action_button.png",
    "THandshake":"hand_shake_action_button.png",
    "TSpoof":"spoof_action_button.png",
    
    "BDB":"database_action_button.png",
    "BCPU":"cpu_action_button.png",
    "BRSA":"rsa_action_button.png",
    "BFirewall":"firewall_action_button.png",
    "BAlgorithmFactory":"algorithm_factory_action_button.png",
    "BSoftwareUpdater":"research_factory_action_button.png",
    "BDatabase":"database_action_button.png",
    "BHandshake":"hand_shake_action_button.png",
    "BSpoofedBuilding":"spoofed_building_action_button.png",
    "BSpoof":"spoofed_building_action_menu.png",

    "UPingOfDeath":"ping_of_death_action_button.png",
    "UNMap":"nmap_action_button.png",
    "USinkhole":"sinkhole_action_button.png",

    "RPortScanner":"port_research_action_button.png",
    "RHandshake":"hand_shake_research_action_button.png",
    "RBigData":"database_research_action_button.png",
    "RAdvancedAlgorithms":"advanced_research_factory.png",
    "RPingResearch": "ping_research_action_button.png",
    "RNetworkTopology": "sinkhole_research_action_button.png",
    "RFPGA":"cpu_research_action_button.png",
    "RRSA":"rsa_research_action_button.png",
    "ROverflow":"pod_research_action_button.png",

    "DSpoof":"spoof_label.png",
    
    "Shake":"shake_action_button.png",
    "Encrypt":"encrypt_action_button.png",
    "Decrypt":"dencrypt_action_button.png",
    "NMap":"perform_nmap_action_button.png",
    "Ping":"execute_ping_action_button.png",
    
    "Attack":"attack_action_button.png",
}

