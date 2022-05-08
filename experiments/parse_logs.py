log = """
App 31437 / 31438: AUC 0.978 	 MP 0.136 	 MR 0.680 	 F1 0.227 	 MAP 0.530 	 coverage 0.527 	 AUC 0.978 	 MP 0.077 	 MR 0.774 	 F1 0.141 	 MAP 0.543 	 coverage 0.600	 0.41383609687959055 sec 
App 31437 / 31438: AUC 0.978 	 MP 0.135 	 MR 0.677 	 F1 0.226 	 MAP 0.527 	 coverage 0.514 	 AUC 0.978 	 MP 0.077 	 MR 0.773 	 F1 0.141 	 MAP 0.540 	 coverage 0.592	 0.4083352391405463 sec 
App 31437 / 31438: AUC 0.978 	 MP 0.135 	 MR 0.675 	 F1 0.225 	 MAP 0.527 	 coverage 0.520 	 AUC 0.978 	 MP 0.077 	 MR 0.772 	 F1 0.140 	 MAP 0.540 	 coverage 0.600	 0.4265939836949827 sec 
App 31437 / 31438: AUC 0.978 	 MP 0.135 	 MR 0.677 	 F1 0.226 	 MAP 0.529 	 coverage 0.514 	 AUC 0.978 	 MP 0.077 	 MR 0.772 	 F1 0.140 	 MAP 0.542 	 coverage 0.608	 0.23476545696927936 sec 
App 31437 / 31438: AUC 0.977 	 MP 0.134 	 MR 0.672 	 F1 0.224 	 MAP 0.526 	 coverage 0.524 	 AUC 0.977 	 MP 0.077 	 MR 0.769 	 F1 0.140 	 MAP 0.539 	 coverage 0.608	 0.1877353682137486 sec 
"""

import numpy as np

sum = 0
count = 0
sum_sqrt = 0

for line in log.split("\n"):
    line = line.split("\t")
    if len(line) < 2:
        continue
    line = [col.strip() for col in line]
    line = line[:-1]
    line = [float(col[col.rfind(" ")+1:]) for col in line]
    line.pop(6)
    line.pop(0)
    sum = sum+np.array(line)
    sum_sqrt = sum_sqrt+np.array(line)**2
    count += 1

print(sum/count)
print((sum_sqrt/count-(sum/count)**2)**0.5)
