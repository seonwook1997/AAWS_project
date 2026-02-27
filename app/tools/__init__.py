from app.tools.utility import (
    read_image_and_analyze, 
    web_search_custom_tool
)
from app.tools.browser_user_tool import (
    browse_web
)

# Export Tool Lists for Agents
tools_basic = []
tools_multimodal = [read_image_and_analyze, web_search_custom_tool]
tools_navigator = [browse_web]
