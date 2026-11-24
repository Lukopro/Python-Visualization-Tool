"""
Unit Test for Config Submodule

Primarily this script is to verify proper
configuration parameter filtering and assignment
"""

from api.config import Config

config = Config() # initialize config object

''' REJECTED CASES '''

# debug tests
config.update(debug="False") # bad type
assert config.get_opt('debug') != "False"
config.update(debug=1) # bad type
assert config.get_opt('debug') != 1

# render_frames tests
config.update(render_frames="False") # bad type
assert config.get_opt('render_frames') != "False"
config.update(render_frames=1) # bad type
assert config.get_opt('render_frames') != 1

# max_scopes tests
config.update(max_scopes=2.5) # bad type
assert config.get_opt('max_scopes') != 2.5
config.update(max_scopes=True) # bad type
assert config.get_opt('max_scopes') != True

# height tests
config.update(height=2.5) # bad type
assert config.get_opt('height') != 2.5
config.update(height=True) # bad type
assert config.get_opt('height') != True

# width tests
config.update(width=2.5) # bad type
assert config.get_opt('width') != 2.5
config.update(width=True) # bad type
assert config.get_opt('width') != True

# bg_color tests
config.update(bg_color="") # empty string
assert config.get_opt('bg_color') != ""
config.update(bg_color="#00000J") # illegal hex char "J"
assert config.get_opt('bg_color') != "#00000J"
config.update(bg_color="00A020") # no "#" sign
assert config.get_opt('bg_color') != "00A020"

# font_color tests
config.update(font_color="") # empty string
assert config.get_opt('bg_color') != ""
config.update(font_color="#00000J") # illegal hex char
assert config.get_opt('bg_color') != "#00000J"
config.update(font_color="00A020") # no "#" sign
assert config.get_opt('bg_color') != "00A020"

''' ACCEPTED CASES '''
