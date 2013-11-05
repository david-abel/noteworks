'''
imageLayer.py
Class that create a cocos layer from an image
'''
from cocos.layer import Layer
from pyglet.gl.gl import glColor4ub, glPushMatrix, glPopMatrix
from pyglet.resource import image


class ImageLayer(Layer):
    def __init__(self, img):
        super(ImageLayer, self).__init__()
        self.img = image(img)

    def draw(self):
        glColor4ub(255, 255, 255, 255)
        glPushMatrix()
        self.transform()
        self.img.blit(0, 0)
        glPopMatrix()
