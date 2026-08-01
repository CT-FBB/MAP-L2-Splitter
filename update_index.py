import re

with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add CSS
css_addition = """
.tab-navigation {
  display: flex;
  background: rgba(13, 17, 32, 0.8);
  border-bottom: 1px solid var(--border);
  padding: 0 40px;
}
.tab-btn {
  background: transparent;
  color: var(--dim);
  border: none;
  font-family: 'Outfit', sans-serif;
  font-size: 16px;
  font-weight: 600;
  padding: 16px 24px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 3px solid transparent;
}
.tab-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.02);
}
.tab-btn.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
}
.tab-content {
  display: none;
}
.tab-content.active {
  display: block;
}
</style>
</head>
"""
content = content.replace("</style>\n</head>", css_addition)

# 2. Add Tab Buttons
tab_html = """
<!-- TAB NAVIGATION -->
<div class="tab-navigation">
  <button class="tab-btn active" id="btn-tab1" onclick="switchTab('tab1')">🔍 OLT Search</button>
  <button class="tab-btn" id="btn-tab2" onclick="switchTab('tab2')">🗺️ L2MAP</button>
</div>

<script>
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  document.getElementById('btn-' + tabId).classList.add('active');
  document.getElementById(tabId).classList.add('active');
}
</script>

<div class="main" style="max-width: 100% !important; padding: 20px;">
  <!-- TAB 1: Search -->
  <div id="tab1" class="tab-content active" style="max-width: 1000px; margin: 0 auto;">
"""

content = content.replace('<div class="main">', tab_html)

# 3. Close tab1, Add Tab 2 iframe, and close main. We just append to the very end before </body>
# But wait, index.html might have </body> at the end.
end_html = """
  </div> <!-- end tab1 -->
  
  <!-- TAB 2: L2MAP -->
  <div id="tab2" class="tab-content" style="height: 85vh; width: 100%;">
    <iframe src="olt_map.html" style="width:100%; height:100%; border:none; border-radius:12px; background: #fefaf0;"></iframe>
  </div>
</div> <!-- end main -->
"""
# Let's replace the last closing </div> that matches main. Actually, simpler to just replace </body>
content = content.replace("</body>", end_html + "\n</body>")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(content)
