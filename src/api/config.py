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
        # whether to render function and global frames in visualization
        'render_frames': False,

        # tracer defaults
        # steps back is for the most part internal constant
        # represents the number of frames from the draw call reaches the caller's frame
        'steps_back': 3,
        # number of scopes from the caller's frame to draw
        # each frame is a scope
        'max_scopes': 2,

        # graph defaults
        # height of the window in px
        'height': '900px',
        # width of the window in px
        'width': '100%',
        # background color of graphics window
        'bgcolor': '#FFFFFF',
        # color of text in graphics window
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
        self.configOpts['bgcolor'] = self.DEFAULTS['bgcolor']
        self.configOpts['font_color'] = self.DEFAULTS['font_color']


    # used to update configuration settings
    # ex. update(render_frames=True) would set render_frames to True
    def update(self, debug: bool=None, render_frames: bool=None, steps_back: int=None, max_scopes: int=None,
               height: str=None, width: str=None,
               bgcolor: str=None, font_color: str=None):

        # debug mode, not specific to a particular module
        if type(debug) is bool:
            self.configOpts['debug'] = debug
            if debug:
                print(f"debug input {debug} accepted.")
                print(f"debug is set to: {self.configOpts['debug']}")
        elif debug and type(debug) is not None:
            print(f"debug input {debug} rejected.")

        # visualizer configs
        # render_frames must be a boolean
        if type(render_frames) is bool:
            if debug:
                print(f"render_frames input {render_frames} accepted.")
                print(f"render_frames is set to: {self.configOpts['render_frames']}")
            self.configOpts['render_frames'] = render_frames
        elif debug and type(render_frames) is not None:
            print(f"render_frames input {render_frames} rejected.")

        # tracer configs
        # steps_back must be a positive integer
        if type(steps_back) is int and steps_back > 0:
            self.configOpts['steps_back'] = steps_back
            if debug:
                print(f"steps_back input {steps_back} accepted.")
                print(f"steps_back is set to: {self.configOpts['steps_back']}")
        elif debug and type(steps_back) is not None:
            print(f"steps_back input {steps_back} rejected.")
        # max_scopes must be a positive integer
        if type(max_scopes) is int and max_scopes > 0:
            self.configOpts['max_scopes'] = max_scopes
            if debug:
                print(f"max_scopes input {max_scopes} accepted.")
                print(f"max_scopes is set to: {self.configOpts['max_scopes']}")
        elif debug and type(max_scopes) is not None:
            print(f"max_scopes input {max_scopes} rejected.")

        # graph configs
        # height must be a string in <number>px form
        # <number> must be positive
        # ex. '300px'
        if type(height) is str:
            if re.match(r'^\d+px$', height) is not None:
                self.configOpts['height'] = height
                if debug:
                    print(f"height input {height} accepted.")
                    print(f"height is set to: {self.configOpts['height']}")
            elif debug and type(height) is not None:
                print(f"height input {height} rejected.")
        # width must be a string in <number>% form
        # <number must be positive
        # ex. '80%'
        if type(width) is str:
            if re.match(r'^\d+%$', width) is not None:
                self.configOpts['width'] = width
                if debug:
                    print(f"width input {width} accepted.")
                    print(f"width is set to: {self.configOpts['width']}")
            elif debug and type(width) is not None:
                print(f"width input {width} rejected.")
        # bgcolor must be a hex color using 8-bit color space
        # ex. '#FFFFFF' is white
        if type(bgcolor) is str:
            if re.match(r'^#[a-fA-F0-9]{6}$', bgcolor) is not None:
                self.configOpts['bgcolor'] = bgcolor
                if debug:
                    print(f"bgcolor input {bgcolor} accepted.")
                    print(f"bgcolor is set to: {self.configOpts['bgcolor']}")
            else:
                # compare against defined colors
                assigned = False
                # the system default color
                if bgcolor.lower() == 'default':
                    self.configOpts['bgcolor'] = Config.DEFAULTS['bgcolor']
                    assigned = True

                if debug and assigned:
                    print(f"bgcolor input {bgcolor} accepted.")
                    print(f"bgcolor is set to: {self.configOpts['bgcolor']}")
        elif debug and type(bgcolor) is not None:
            print(f"bgcolor input {bgcolor} rejected.")
        # font_color must be a hex color using 8-bit color space
        # ex. '#FFFFFF' is white
        if type(font_color) is str:
            if re.match(r'^#[a-fA-F0-9]{6}$', font_color) is not None:
                self.configOpts['font_color'] = font_color
                if debug:
                    print(f"font_color input {font_color} accepted.")
                    print(f"font_color is set to: {self.configOpts['font_color']}")
            else:
                # compare against defined default colors
                assigned = False
                # the system default color
                if font_color.lower() == 'default':
                    self.configOpts['font_color'] = Config.DEFAULTS['font_color']

                if debug and assigned:
                    print(f"font_color input {font_color} accepted.")
                    print(f"font_color is set to: {self.configOpts['font_color']}")
        elif debug and type(font_color) is not None:
            print(f"font_color input {font_color} rejected.")

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