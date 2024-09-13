﻿$Logfile = "O:\Workspaces\mcjustin\fhir-attrib-setter.cosri.patient.active\prod\fhir-attrib-setter-cosri-patient-active.log"
$Timestamp = Get-Date -UFormat "%Y-%m-%d %T"
Add-content $Logfile -value "[$Timestamp] Running COSRI Patient active setter script..."
cd "O:\Workspaces\mcjustin\fhir-attrib-setter.cosri.patient.active\prod"
Invoke-Expression "& python 'O:\Workspaces\mcjustin\fhir-attrib-setter.cosri.patient.active\prod\fhir-attrib-setter.patient.active.py' "
$Timestamp = Get-Date -UFormat "%Y-%m-%d %T"
Add-content $Logfile -value "[$Timestamp] Done." 
