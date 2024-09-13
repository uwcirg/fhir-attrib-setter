# fhir-attrib-setter

Set attributes on FHIR resources en masse, based on search criteria. 
First use case is to set Patient.active = false for those that meet this criteria:
Lacking the identifier w/ system "http://www.uwmedicine.org/epic_patient_id", and (are missing the active attribute, or have active = true).

3. Edit configurable items in the __config.env__ file:
   - Log file location
   - FHIR server endpoint
   - FHIR server auth token
   - Debug level (anything less than 9 is "info/warning", 9 or greater is "debug")
   - Types of resources to include/exclude

4. Edit configurable items in the __fhir-attrib-setter.patient.active.ps1__ file (this file starts runs the Python script.  It's meant to be run via Windows Task Scheduler):
   - Log file location
   - Path to Python script [__fhir-attrib-setter.patient.active__]
