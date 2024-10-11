# -*- coding: utf-8 -*-
"""
Copyright 2024 University of Washington Clinical Informatics Research Group

@author: mcjustin

This is a migration per https://www.pivotaltracker.com/story/show/188376912 
This should be run the day before Jim's updated dawg-to-fhir code runs, namely
when it's able to set this to the actual appt dt for the appts that it finds.
Set a new extension w/ "url": "http://www.uwmedicine.org/time_of_next_appointment",
and w/ "valueDateTime": [now + 20 years] (date format e.g. 2024-10-07T09:00:00)
on all patients who have active=true.
If this extension already exists for the Patient, it is not touched.
Count of 5000 should be fine for the current use case but we may want to support pagination instead.
prod has ~2000 of these
"""

from dotenv import dotenv_values
from os.path import exists
import datetime, os, pathlib, re, requests, simplejson, time, dateutil
from dateutil.relativedelta import relativedelta

def log_it(message):
    LOG_FILE.write("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] ")
    LOG_FILE.write(message + "\n")

config = dotenv_values("config.env")

LOG_FILE = open(config['LOG_FILE_PATH'], "a", encoding="utf-8")

fhir_endpoint = config['FHIR_ENDPOINT']
fhir_auth_token = config['FHIR_AUTH_TOKEN']
dry_run = config['DRY_RUN']

log_it("========= fhir-attrib-setter.patient.extension STARTING RUN ==========")

if dry_run > '0':
    log_it('===THIS IS A DRY RUN, RESOURCES WILL NOT BE TOUCHED.===')

# Set debug level, anything less than 9 is "info/warning", 9 or greater is "debug"
debug_level = config['DEBUG_LEVEL']

# Open a session to the FHIR endpoint instead of making individual calls as this speeds things up significantly
session = requests.Session()

fhir_query_response = None
fhir_query_headers = {'Authorization': fhir_auth_token}
# It would be nice to be able to include a search param to exclude those that have the extension set, but we don't yet have a SearchParam for that in Hapi (still a todo).
fhir_query_params = {'identifier': 'http://www.uwmedicine.org/epic_patient_id|', 'active': 'true', '_count': '5000'}
fhir_query_response = session.get(fhir_endpoint + '/Patient', headers = fhir_query_headers, params = fhir_query_params)

log_it("FHIR patient query URL: " + fhir_query_response.url)

pat_cnt = 0

now_plus_20_yrs = (datetime.datetime.now() + relativedelta(years=20)).strftime("%Y-%m-%dT%H:%M:%S")
extension_url = "http://www.uwmedicine.org/time_of_next_appointment"

if fhir_query_response is not None:
    if fhir_query_response.status_code != 200:
        log_it("FHIR patient query failed, status code: " + str(fhir_query_response.status_code))
    else:
        fhir_query_reply = fhir_query_response.json()

        log_it("Count of Patient resources that matched the FHIR query (note that we still need to filter out those who already have the extension set):" + str(fhir_query_reply["total"]))
        if debug_level > '8':
            log_it("FHIR patient query response: " + simplejson.dumps(fhir_query_reply))

        # iterate over fhir_query_reply["entry"]
        for entry in fhir_query_reply["entry"]:
            patient_hapi_id = entry["resource"]["id"]

            if "extension" not in entry["resource"]:
                entry["resource"]["extension"] = []
            this_extension_exists = any(
                ext.get("url") == extension_url for ext in entry["resource"]["extension"]
            )

            if not this_extension_exists:
                log_it("Patient ID (" + patient_hapi_id + ") matches criteria (active=true and this extension does not yet exist).")

            # If the extension does not exist, add it.
            if dry_run < '1' and not this_extension_exists:
                entry["resource"]["extension"].append({"url": extension_url, "valueDateTime": now_plus_20_yrs})

                fhir_patient_response = session.put(fhir_endpoint + "/Patient/" + patient_hapi_id, json = entry["resource"], headers = fhir_query_headers)

                if fhir_patient_response is not None:
                    fhir_patient_resonse_json = fhir_patient_response.json()
                    if debug_level > '8':
                        log_it("Tried PUT Patient id " + patient_hapi_id + " at " + fhir_patient_response.url + ", skipping. Response code was " + str(fhir_query_response.status_code) + " and json was: " + simplejson.dumps(fhir_patient_resonse_json) + ", next will check whether it was accepted.")

                    # Hapi might respond w/ a 200 code even though it had an error and didn't write anything. json for such a resonse: {"resourceType": "OperationOutcome", "issue": [{"severity": "error", "code": "processing", "diagnostics": "HAPI-0450: Failed to parse request body as JSON resource. Error was: HAPI-1821: [element=\"valueDateTime\"] Invalid attribute value \"2044-10-11 09:57:27\": Invalid date/time format: \"2044-10-11 09:57:27\": Expected character 'T' at index 10 but found  "}]}

                    clean_code_but_error_in_returned_json = True
                    if fhir_patient_resonse_json and hasattr(fhir_patient_resonse_json, "issue") and any(issue.get("severity") == "error" for issue in fhir_patient_resonse_json["issue"]):
                        clean_code_but_error_in_returned_json = False

                    if fhir_query_response.status_code != 200 or clean_code_but_error_in_returned_json == False:
                        log_it("ERROR: Unable to update/PUT Patient id " + patient_hapi_id + " at " + fhir_patient_response.url + ", skipping. Response code was " + str(fhir_query_response.status_code) + " and json was: " + simplejson.dumps(fhir_patient_resonse_json))
                    else: 
                        if debug_level > '8':
                            log_it("FHIR patient PUT URL: " + fhir_patient_response.url)
                        pat_cnt = pat_cnt + 1
                        if debug_level > '8':
                            log_it("FHIR patient PUT response: " + simplejson.dumps(fhir_patient_resonse_json))
                        log_it("Successfully updated Patient " + patient_hapi_id)
                else:
                    log_it("ERROR: Unable to update/PUT Patient id " + patient_hapi_id + "at " + fhir_patient_response.url + " (no response), skipping.")
else:
    log_it("ERROR: Unable to query FHIR store for patients... exiting.")

log_it("Total patients updated: " + str(pat_cnt))

log_it("========= fhir-attrib-setter.patient.extension FINISH RUN ==========")

LOG_FILE.close()
