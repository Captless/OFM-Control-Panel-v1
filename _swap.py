# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'webui/static/index.html'
s = open(p, encoding='utf-8').read()

grid = s.index('class="settings-grid"')
# Prompt bank pane start
pb_start = s.index('class="settings-pane prompt-bank-pane"', grid)
# Identity pane start
id_start = s.index('class="settings-pane identity-pane"', grid)
# settings grid close: after identity pane end -> '</div>\n    </div>\n  </section>' (grid close + section close)
end = s.index('</main>')
# find the exact boundary: identity pane ends at its section close + pane div close
id_section_end = s.index('</section>', id_start)
pane_end = s.index('</div>', id_section_end)  # closes settings-pane
# after pane_end there may be whitespace then grid close '</div>' then section close
grid_close = s.index('</div>', pane_end)
tail = s[grid_close:end]

pb_block = s[pb_start:id_start]
id_block = s[id_start:pane_end]
prefix = s[:pb_start]
postfix = s[pane_end:]

new = prefix + id_block + pb_block + postfix
open(p, 'w', encoding='utf-8', newline='').write(new)
print('SWAPPED OK')
print('pb len', len(pb_block), 'id len', len(id_block))
