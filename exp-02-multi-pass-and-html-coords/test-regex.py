import re
import context.broad_context

testString = '10–13 April 2022'

for idx, format in enumerate(context.broad_context.DateRanges):
    matches = re.findall(format, testString)
    print('{}-{}'.format(matches, idx))
