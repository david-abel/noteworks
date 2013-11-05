import pyglet, os, random

class Music(object):
    def __init__(self, fileName):
        self.source = pyglet.media.load(fileName, streaming=True)
        self.player = pyglet.media.Player()
        self.player.eos_action = pyglet.media.Player.EOS_LOOP # Loops the song
        self.player.queue(self.source)

    def play(self, volume = 50):
        # self.set_volume(volume)
        self.player.play()
        # DEBUG
        # print self.player.volume, "VOL"
        
    def stop(self):
        self.player.pause()
        self.rewind()
        
    def rewind(self):
        self.player.seek(0.0)
        
    def pause(self):
        self.player.pause()
        
    def unpause(self):
        self.player.play()
        
    def fadeout(self):
        # TODO figure out
        self.stop()
        
    def is_playing(self):
        return self.player.playing
        
    def get_position(self):
        return self.player.time * 1000.0

    def increase_volume(self):
        self.player.volume += 2


    def decrease_volume(self):
        self.player.volume -= 2


    def set_volume(self, newVolume):
        self.player.volume = newVolume


# theme = 'theme_' + str(random.randint(1,2)) + '.wav'
theme = 'theme_1.wav'
menu = 'menu_theme.wav'
intro_sound = 'intro_v2.wav'

sound_file = os.path.join('sounds', theme)  # create a sound file
theme_player = Music(sound_file)

menu_sound_file = os.path.join('sounds', menu)  # create a sound file
menu_player = Music(menu_sound_file)

intro_file = os.path.join('sounds', intro_sound)
intro_sound_player = Music(intro_file)

sound_player = pyglet.media.Player()
