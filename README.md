# fhir-attrib-setter

Set attributes on FHIR resources en masse, based on search criteria. First use case is Patient.active.
 
3. Edit configurable items in the __config.env__ file:
   - Log file location
   - FHIR server endpoint
   - FHIR server auth token
   - Debug level (anything less than 9 is "info/warning", 9 or greater is "debug")
   - Types of resources to include/exclude

4. Edit configurable items in the __paintracker_daily_update_dawg_to_fhir_via_fume_job.ps1__ file (this file starts runs the Python script.  It's meant to be run via Windows Task Scheduler):
   - Log file location
   - Path to Python script [__cosri_patient_active_setter.py__]
