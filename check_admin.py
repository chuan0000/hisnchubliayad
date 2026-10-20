with open('app/static/admin.html') as f:
    text = f.read()

script = text.split('<script>')[2].split('</script>')[0]

# Replace getAuthHeaders back to normal
import re

fixed_script = re.sub(
    r'const getAuthHeaders = \(\) => \{\s*return \{.*?\'Authorization\': `Bearer \$\{token\.value\}`,',
    'const getAuthHeaders = () => {\n          return {\n            \'Authorization\': `Bearer ${token.value}`,',
    script,
    flags=re.DOTALL
)

test_code = '''
const Vue = {
  createApp: (opts) => {
    try {
      console.log("Calling setup()...");
      const ret = opts.setup();
      console.log("setup() returned successfully! Keys count:", Object.keys(ret).length);
    } catch(err) {
      console.error("SETUP ERROR:", err);
    }
  },
  ref: (v) => ({ value: v }),
  computed: (fn) => ({ value: fn() }),
  onMounted: (fn) => {}
};
const localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
const window = { location: { origin: "" } };
const document = { documentElement: { classList: { add: () => {}, remove: () => {} } }, getElementById: () => null };
''' + fixed_script

with open('/tmp/eval_admin.js', 'w') as out:
    out.write(test_code)

print("Wrote /tmp/eval_admin.js")
