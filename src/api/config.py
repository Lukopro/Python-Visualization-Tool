# file for configuration class

# Class for all configuration options
# manages a singleton object to be referenced by other modules
class Config:

    # declare singleton object
    config = None

    DEFAULTS = {
        # visualizer defaults
        'render_frames': False,
        # tracer defaults

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


        # graph config
        self.configOpts['height'] = self.DEFAULTS['height']
        self.configOpts['width'] = self.DEFAULTS['width']
        self.configOpts['directed'] = self.DEFAULTS['directed']
        self.configOpts['bgcolor'] = self.DEFAULTS['bgcolor']
        self.configOpts['font_color'] = self.DEFAULTS['font_color']


    # used to update configuration settings
    # ex. update(render_frames=True) would set render_frames to True
    def update(self, render_frames: bool =None, height: str =None, width: str =None,
               directed: bool =None, bgcolor: str =None, font_color: str =None):

        # visualizer configs
        if render_frames is not None:
            self.configOpts['render_frames'] = render_frames
        # tracer configs


        # graph configs
        if height is not None:
            self.configOpts['height'] = height
        if width is not None:
            self.configOpts['width'] = width
        if directed is not None:
            self.configOpts['directed'] = directed
        if bgcolor is not None:
            self.configOpts['bgcolor'] = bgcolor
        if font_color is not None:
            self.configOpts['font_color'] = font_color

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