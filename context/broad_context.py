import re
import context.sources

# ======================================================================================================================
# Query
# ======================================================================================================================

SearchEngines = []
SearchEngines.append(context.sources.Google())
SearchEngines.append(context.sources.Bing())
SearchEngines.append(context.sources.Yahoo())
SearchEngines.append(context.sources.DuckDuckGo())

# ======================================================================================================================
# Basic Safety Checks
# ======================================================================================================================

DomainDics = set()
DomainIgnores = {'googleadservices', 'youtube', 'youtu', 'twitter','facebook', 'linkedin', 'job', 'jobs', 'advertising','addons','translate'}


DirDics = {'search','journal','news'}
DirIgnores = {'editor', 'press-release', 'award', 'certification','about','advertising','communities'
    ,'professional','job','membership','auth','it-services','support','careers'}


PathDiscs = {'search','organize','insider'}
PathIgnores = {'award', 'editor', 'shopping', 'advertising', 'tool', 'store', 'map', 'course', 'flight',
               'product', 'podcast', 'finance', 'login', 'contact', 'subscribe', 'webinar', 'policy', 'subscriptions',
               'magazines','account','sponsorship','volunteering','advertising','job', 'registration','cart','join',
               'login', 'video', 'webinar','faq','sponsor','scholarship','members','jobs'}


MimeChecks = {'html'}
MimeDiscs = set()
MimeIgnores = {'pdf', 'zip', 'rar', 'exe', 'png', 'jpg', 'jpeg', 'docx', 'doc', 'odt', 'txt', 'gif', 'mp3', 'mp4', 'jpeg','xml','7em','cfm','io'}

# ======================================================================================================================
# Basic Primitive Data Format Regexes
# ======================================================================================================================

Currency = [re.compile("\$[0-9]+\.[0-9][0-9]")]

Address = [re.compile("[0-9]+ [A-Za-z]+ (Ave)?(St)? [A-Z][A-Z],? [A-Z][a-z]+,? [A-Z][A-Z] [0-9]+"),
           re.compile("[A-Z]{1,10}[a-z]{1,10}, [A-Z]{1,3}[a-z]{0,3}, [A-Z]{1,3}"),
           re.compile("[A-Z]{1,10}[a-z]{1,10}, [A-Z][a-z]{3,10} [A-Z][a-z]{3,10}")]

Names = [re.compile("[A-Z][a-z]{1,14}\s[A-Z][a-z]{1,14}"),
         re.compile("[A-Z][A-Za-z]+™*")]

DateRanges = [re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.[JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2} . [JFMASOND][a-z]{1,9} \d{1,2}, \d{4,6}"),
              re.compile("[JFMASOND][A-Z]{0,9}[a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]?[0-9] - [0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]?[0-9]-[0-9]?[0-9], [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2} . [JFMASOND][a-z]{1,9} \d{1,2} \d{4,6}"),
              re.compile("[JFMASOND][a-z]{0,10} [0-9]{1,2}–[0-9]{1,2} [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}–[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}-[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[0-9]{1,2}.[0-9]{1,2} [JFMASOND]?[jfmasond]?[a-z]+ [0-9][0-9][0-9][0-9]"),
              re.compile("[JFMASOND][a-z]{1,9} \d{1,2}.\d{1,2}, \d{4,6}")]

DateRegexses = [
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] [ap]m [A-Z][A-Z] ?[A-Z][A-Z][A-Z]?"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], [1-9][0-9][0-9][0-9]+ +\([1-9]?[0-9]:[0-9][0-9], [A-Z][A-Z][A-Z]-[0-9]+, [A-Z][A-Z][A-Z]\)"),
    re.compile("[MTWFS][a-z]+, ?[JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[1-9]?[0-9]:[0-9][0-9] [ap]m ?[A-Z][A-Z][A-Z]?"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ ?[1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ \([1-9]?[0-9]:[0-9][0-9][ap]m [A-Z][A-Z][A-Z]\)"),
    re.compile("[JFMASOND][a-z]+ [1-9]?[0-9], ?[1-9][0-9][0-9][0-9]+ *\([1-9]?[0-9]:[0-9][0-9][A-Z][A-Z] [A-Z][a-z]+ [Tt]ime\)"),
    re.compile("[MTWFS][a-z]+, [0-9]?[0-9] [JFMASOND][a-z]+ [1-9][0-9]+ [0-9]?[0-9]:[0-5][0-9][ap]m [A-Z][A-Z][A-Z]"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+ [0-9]?[0-9]:[0-5][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[0-9]+:[0-9][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+, ?[0-9]+:[0-9][0-9] [A-Z][a-zA-Z][A-Z]"),
    re.compile("[JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+, [0-9]?[0-9]:[0-5][0-9] [A-Z][A-Z][A-Z]"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ [1-3]*[0-9], [1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]+,? [JFMASOND][a-z]+ [1-3]*[0-9], ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [1-3]*[0-9], [1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+"),
    re.compile("[MTWFS][a-z]+, [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9], [1-9][0-9]+"),
    re.compile("[MTWFS][a-z]+ [JFMASOND][a-z]+ [0-9]?[0-9] [1-9][0-9]+"),
    re.compile("[A-Za-z][a-z]+ [1-3]?[0-9], ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[A-Za-z][a-z]+ [1-3]?[0-9] ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[MTWFS][a-z][a-z] [1-3]?[0-9] ?[1-9][0-9][0-9][0-9]+"),
    re.compile("[1-3]?[0-9] [JFMASOND][a-z]+ [1-9][0-9][0-9][0-9]+"),
    re.compile("[0-9][0-9]\\\[0-9][0-9]\\\[0-9]+"),
    re.compile("[0-9][0-9]/[0-9][0-9]/[0-9]+"),
    re.compile("[0-9][0-9]-[0-9][0-9]-[0-9]+")
]

Floats = [re.compile("[0-9]+\.[0-9][0-9]\s")]

Ints = [re.compile("[0-9]+\s")]

Bools = [re.compile("[Tt][Rr][Uu][Ee]\s"),
         re.compile("[Ff][Aa][Ll][Ss][Ee]\s")]

UnitsOfMeasure = []


AllPrimitives = []
AllPrimitives.append(Currency)
AllPrimitives.append(DateRanges)
AllPrimitives.append(DateRegexses)
AllPrimitives.append(Floats)
AllPrimitives.append(Ints)
AllPrimitives.append(Bools)
AllPrimitives.append(UnitsOfMeasure)
AllPrimitives.append(Address)
#AllPrimitives.append(Names)

