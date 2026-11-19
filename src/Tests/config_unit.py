"""
Unit Test for Config Submodule

Primarily this script is to verify proper
configuration parameter filtering and assignment
"""

from api.config import Config

config = Config() # initialize config object

''' REJECTED CASES '''

# debug tests
config.update(debug="False")
config.update(debug=1)

# render_frames tests
config.update(render_frames="False")
config.update(render_frames=1)

# max_scopes tests
config.update(max_scopes=2.5)
config.update(max_scopes=True)

# height tests
# width tests
# bg_color tests
# font_color tests

''' ACCEPTED CASES '''