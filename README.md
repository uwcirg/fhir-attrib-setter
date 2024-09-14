# fhir-attrib-setter

Set attributes on FHIR resources en masse, based on search criteria. 

First use case is to set Patient.active = false for those that meet this criteria:
Lacking the identifier w/ system "http://www.uwmedicine.org/epic_patient_id", and (are missing the active attribute, or have active = true).
This will run as a nightly job on the DAWG server, and serves as a one-off cleanup of duplicative Patient resources (created during early dev phases for these projects), and to "delete" Patient resources added by users via COSRI/FEMR (rare cases where clinicians look up Patients in COSRI prior to the Patient being in there yet, i.e. didn't have a CPR appointment scheduled and in the DAWG at the time that https://github.com/uwcirg/dawg-to-fhir was run early that morning).

3. Edit configurable items in the __config.env__ file:
   - Log file location
   - FHIR server endpoint
   - FHIR server auth token
   - Debug level (anything less than 9 is "info/warning", 9 or greater is "debug")
   - Types of resources to include/exclude

4. Edit configurable items in the __fhir-attrib-setter.patient.active.ps1__ file (this file starts runs the Python script.  It's meant to be run via Windows Task Scheduler):
   - Log file location
   - Path to Python script [__fhir-attrib-setter.patient.active__]
