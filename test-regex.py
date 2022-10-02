import re
import context.broad_context

testString = 'January 6, 2021  (23:59, UTC-5, EST)'

for idx, format in enumerate(context.broad_context.DateRegexses):
    matches = re.findall(format, testString)
    print('{}-{}'.format(matches, idx))
