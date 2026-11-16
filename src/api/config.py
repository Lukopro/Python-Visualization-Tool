# file for configuration class

# user sanitization uses regex pattern matching
import re

# Class for all configuration options
# manages a singleton object to be referenced by other modules
class Config:

    # declare singleton object
    config = None

    DEFAULTS = {

        # used for testing
        'debug': False,

        # visualizer defaults
        'render_frames': False,

        # tracer defaults
        'steps_back': 3,
        'max_scopes': 2,

        # graph defaults
        'height': '900px',
        'width': '100%',
        'directed': True,
        'bgcolor': '#FFFFFF',
        'font_color': "#111827"

    }

    # initializes config to default values
    def __init__(self):
        # initialize config dictionary
        self.configOpts = {}

        # visualizer config
        self.configOpts['render_frames'] = self.DEFAULTS['render_frames']

        # tracer config
        self.configOpts['steps_back'] = self.DEFAULTS['steps_back']
        self.configOpts['max_scopes'] = self.DEFAULTS['max_scopes']

        # graph config
        self.configOpts['height'] = self.DEFAULTS['height']
        self.configOpts['width'] = self.DEFAULTS['width']
        self.configOpts['directed'] = self.DEFAULTS['directed']
        self.configOpts['bgcolor'] = self.DEFAULTS['bgcolor']
        self.configOpts['font_color'] = self.DEFAULTS['font_color']


    # used to update configuration settings
    # ex. update(render_frames=True) would set render_frames to True
    def update(self, render_frames: bool=None, steps_back: int=None, max_scopes: int=None,
               height: str=None, width: str=None,
               directed: bool=None, bgcolor: str=None, font_color: str=None):

        # visualizer configs
        # render_frames must be a boolean
        if type(render_frames) is bool:
            self.configOpts['render_frames'] = render_frames

        # tracer configs
        # steps_back must be a positive integer
        if type(steps_back) is int and steps_back > 0:
            self.configOpts['steps_back'] = steps_back
        # max_scopes must be a positive integer
        if type(max_scopes) is int and max_scopes > 0:
            self.configOpts['max_scopes'] = max_scopes

        # graph configs
        # height must be a string in <number>px form
        # <number> must be positive
        # ex. '300px'
        if type(height) is str:
            if re.match(r'^\d+px$', height) is not None:
                self.configOpts['height'] = height
        # width must be a string in <number>% form
        # <number must be positive
        # ex. '80%'
        if type(width) is str:
            if re.match(r'^\d+%$', width) is not None:
                self.configOpts['width'] = width
        # directed must be a boolean
        if type(directed) is bool:
            self.configOpts['directed'] = directed
        # bgcolor must be a hex color using 8-bit color space
        # ex. '#FFFFFF' is white
        if type(bgcolor) is str:
            if re.match(r'^#[a-fA-F0-9]{6}$', bgcolor) is not None:
                self.configOpts['bgcolor'] = bgcolor
            else:
                # compare against defined colors
                # the system default color
                if bgcolor.lower() == 'default':
                    self.configOpts['bgcolor'] = Config.DEFAULTS['bgcolor']
        # font_color must be a hex color using 8-bit color space
        # ex. '#FFFFFF' is white
        if type(font_color) is str:
            if re.match(r'^#[a-fA-F0-9]{6}$', font_color) is not None:
                self.configOpts['font_color'] = font_color
            else:
                # compare against defined default colors
                if font_color.lower() == 'default':
                    self.configOpts['font_color'] = Config.DEFAULTS['font_color']

    # getter function for visualizer to read specific config options
    def get_opt(self, opt):
        return self.configOpts[opt]

    # returns formatted string of all configuration options
    def __str__(self):
        result_str = ""
        for opt, val in self.configOpts.items():
            result_str += f"{opt<20}: {val}\n"
        return result_str

    # overrides call to create new object with reference to single object
    # enforces the creation of exactly one object (singleton)
    def __new__(cls):
        if cls.config is None:
            cls.config = super().__new__(cls)
        return cls.config