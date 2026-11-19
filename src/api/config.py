# file for configuration class

# user sanitization uses regex pattern matching
import re

# Class for all configuration options
# manages a singleton object to be referenced by other modules
class Config:

    # declare singleton object
    _config = None

    DEFAULTS = {

        # used for testing
        'debug': False,

        # visualizer defaults
        # whether to render function and global frames in visualization
        'render_frames': False,

        # tracer defaults
        # steps back is an internal constant
        # represents the number of frames from the draw call reaches the caller's frame
        'steps_back': 3,
        # number of scopes from the caller's frame to draw
        # each frame is a scope
        'max_scopes': 1,

        # graph defaults
        # height of the window in px
        'height': 960,
        # width of the window in px
        'width': 960,
        # background color of graphics window
        'bg_color': '#FFFFFF',
        # color of text in graphics window
        'font_color': "#111827"

    }

    # initializes config to default values
    def __init__(self):

        # "_initialized" flag is boolean declared in __new__ method
        # stops config from wiping itself out after it was initialized
        if not self._initialized:

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
            self.configOpts['bg_color'] = self.DEFAULTS['bg_color']
            self.configOpts['font_color'] = self.DEFAULTS['font_color']

            # set intialized flag
            self._initialized = True


    # used to update configuration settings
    # ex. update(render_frames=True) would set render_frames to True
    def update(self, debug: bool=None, render_frames: bool=None, max_scopes: int=None,
               height: int=None, width: int=None,
               bg_color: str=None, font_color: str=None):

        # debug mode, not specific to a particular module
        if type(debug) is bool:
            self.configOpts['debug'] = debug
            if debug:
                print(f"debug input {debug} accepted.")
                print(f"debug is set to: {self.configOpts['debug']}")
        elif debug and debug is not None:
            print(f"debug input {debug} rejected.")

        # visualizer configs
        # render_frames must be a boolean
        if type(render_frames) is bool:
            self.configOpts['render_frames'] = render_frames
            if debug:
                print(f"render_frames input {render_frames} accepted.")
                print(f"render_frames is set to: {self.configOpts['render_frames']}")
        elif debug and render_frames is not None:
            print(f"render_frames input {render_frames} rejected.")

        # tracer configs
        # max_scopes must be a positive integer
        if type(max_scopes) is int and max_scopes > 0:
            self.configOpts['max_scopes'] = max_scopes
            if debug:
                print(f"max_scopes input {max_scopes} accepted.")
                print(f"max_scopes is set to: {self.configOpts['max_scopes']}")
        elif debug and max_scopes is not None:
            print(f"max_scopes input {max_scopes} rejected.")

        # graph configs
        # height is in px, a positive integer
        # ex '300' for 300px
        if type(height) is int and height > 0:
            self.configOpts['height'] = height
            if debug:
                print(f"height input {height} accepted.")
                print(f"height is set to: {self.configOpts['height']}")
        elif debug and height is not None:
            print(f"height input {height} rejected.")
        # width is in px, a positive integer
        # ex. '300' for 300px
        if type(width) is int and width > 0:
            self.configOpts['width'] = width
            if debug:
                print(f"width input {width} accepted.")
                print(f"width is set to: {self.configOpts['width']}")
        elif debug and width is not None:
            print(f"width input {width} rejected.")
        # bg_color must be a hex color using 8-bit color space
        # ex. '#FFFFFF' is white
        if type(bg_color) is str:
            if re.match(r'^#[a-fA-F0-9]{6}$', bg_color) is not None:
                self.configOpts['bg_color'] = bg_color
                if debug:
                    print(f"bg_color input {bg_color} accepted.")
                    print(f"bg_color is set to: {self.configOpts['bg_color']}")
            else:
                # compare against defined colors
                assigned = False
                # the system default color
                if bg_color.lower() == 'default':
                    self.configOpts['bg_color'] = Config.DEFAULTS['bg_color']
                    assigned = True

                if debug and assigned:
                    print(f"bg_color input {bg_color} accepted.")
                    print(f"bg_color is set to: {self.configOpts['bg_color']}")
        elif debug and bg_color is not None:
            print(f"bg_color input {bg_color} rejected.")
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
        elif debug and font_color is not None:
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
        if cls._config is None:
            cls._config = object.__new__(cls)
            cls._config._initialized = False
        return cls._config
