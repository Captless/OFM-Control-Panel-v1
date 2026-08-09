# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
s = open('webui/static/index.html', encoding='utf-8').read()
i = s.find('class="settings-grid"')
j = s.find('</main>')
seg = s[i:j]
for l in seg.split('\n'):
    t = l.strip()
    if 'settings-pane' in t or '<h4>' in t or '<h5>' in t:
        print(t)
