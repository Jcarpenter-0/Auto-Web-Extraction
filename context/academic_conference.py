import re
from typing import List
from typing import Dict

import context.broad_context
import context.formats.html


# ======================================================================================================================
# Academic Conference Context
# ======================================================================================================================

# Specific Context Labels should be Single-Label:(Label(s),Format(s),Expected Occurrences,Behavior(s)), we truncate behaviors for scope control
conferenceFields:List[context.formats.html.Field] = []

conferenceFields.append(context.formats.html.Field('Conference-Hosting-Dates',
                                                  dataFormats=context.broad_context.DateRanges,
                                                  dataTypeIndex=0))

conferenceLocations = [re.compile('[Vv]irtual [Cc]onference'), re.compile('[Vv]irtual [Ee]vent'), re.compile('[Vv]irtual')]
conferenceLocations.extend(context.broad_context.Address)

conferenceFields.append(context.formats.html.Field('Conference-Location',
                                                      dataFormats=conferenceLocations,
                                                   dataTypeIndex=1))

conferenceFields.append(context.formats.html.Field('Initial-Submission-Deadline',
                                                  labelFormats=[re.compile("[Aa]bstracts? [Rr]egistration [Dd]eadline"),
                                                                re.compile("[Rr]efereed [Pp]apers?"),
                                                                re.compile("[Aa]bstracts? [Dd]ue")],
                                                  dataFormats=context.broad_context.DateRegexses,
                                                     dataTypeIndex=3))

conferenceFields.append(context.formats.html.Field('Notification',
                                                      labelFormats=[re.compile("[Nn]otification of [Aa]cceptance"),
                                                                    re.compile("[Nn]otification"),
                                                                    re.compile("[Aa]uthor response period"),
                                                                    re.compile("[Pp]aper acceptance notification"),
                                                                    re.compile("[Aa]uthor notification"),
                                                                    re.compile("[Aa]cceptance notification")],
                                                      dataFormats=context.broad_context.DateRegexses,
                                                        dataTypeIndex=3))


conferenceFields.append(context.formats.html.Field('Final-Submission-Deadline',
                                                      labelFormats=[re.compile("Final [Pp]aper files? due"),
                                                                  re.compile("Final [Pp]aper due"),
                                                                  re.compile("Final [Pp]aper [Ss]ubmissions?"),
                                                                  re.compile("[Pp]aper [Ss]ubmissions?")],
                                                      dataFormats=context.broad_context.DateRegexses,
                                                       dataTypeIndex=3))

conferenceFields.append(context.formats.html.Field('Conference-Organizers',
                                                      labelFormats=[re.compile("[Cc]onference [Oo]rganizers?"),
                                                                    re.compile("[Oo]rganizers?")],
                                                      dataFormats=context.broad_context.Names,
                                                   dataTypeIndex=6,
                                                   behaviorClasses=[context.formats.html.NameBehaviors()],
                                                   occurences=5))
