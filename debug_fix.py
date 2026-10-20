import re

with open('app/static/admin.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Check getAuthHeaders
print("Checking getAuthHeaders in admin.html...")
m = re.search(r'const getAuthHeaders = \(\) => \{.*?return \{(.*?)\};\s*\};', content, re.DOTALL)
if m:
    print("Found getAuthHeaders, inner length:", len(m.group(1)))
    # print first 200 chars
    print(m.group(1)[:200])

