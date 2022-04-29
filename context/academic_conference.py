import re
from typing import List
from typing import Dict
import datetime
from datetime import datetime
from dateutil.parser import parse

import context.broad_context

conferenceFields:Dict[str, List[re.Pattern]] = dict()


# Need to define the label-less formats here and the associated label they should be assigned
conferenceLabellessFields:Dict[str, List[re.Pattern]] = dict()

conferenceLabellessFields['Conference-Hosting-Dates'] = [re.compile("[JFMASOND][a-z]+ [0-9]+\-[0-9]+ [0-9]+")]


conferenceFields['Initial-Submission-Deadline'] = [re.compile("[Aa]bstracts?( [Rr]egistration)*( [Dd]eadline)*"),
                                           re.compile("[Rr]efereed( [Pp]apers?)?"),
                                           re.compile("[Aa]bstracts? [Dd]ue")]

conferenceFields['Notification-Of-Acceptance'] = [re.compile("[Nn]otification( of [Aa]cceptance)?"),
                                           re.compile("[Nn]otification of [Aa]cceptance"),
                                           re.compile("[Aa]uthor response period"),
                                           re.compile("[Pp]aper acceptance notification"),
                                           re.compile("[Aa]uthor notification"),
                                           re.compile("[Aa]cceptance notification")]

conferenceFields['Final-Submission-Deadline'] = [re.compile("Final [Pp]aper files? due"),
                                                 re.compile("Final [Pp]aper due")]

