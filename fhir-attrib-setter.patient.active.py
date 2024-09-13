# -*- coding: utf-8 -*-
"""
Copyright 2024 University of Washington Clinical Informatics Research Group

@author: mcjustin
"""

from dotenv import dotenv_values
from os.path import exists
import datetime, os, pathlib, re, requests, simplejson as json, time

def log_it(message):
    LOG_FILE.write("[" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "] ")
    LOG_FILE.write(message + "\n")

config = dotenv_values("config.env")

LOG_FILE = open(config['LOG_FILE_PATH'], "a", encoding="utf-8")

fhir_endpoint = config['FHIR_ENDPOINT']
fhir_auth_token = config['FHIR_AUTH_TOKEN']
fume_endpoint = config['FUME_ENDPOINT']
dry_run = config['DRY_RUN']

log_it("=========================== STARTING RUN =============================")

if dry_run > '0':
    log_it('===THIS IS A DRY RUN, RESOURCES WILL NOT BE TOUCHED.===')

# Set debug level, anything less than 9 is "info/warning", 9 or greater is "debug"
debug_level = config['DEBUG_LEVEL']

# Open a session to the FHIR endpoint instead of making individual calls as this speeds things up significantly
session = requests.Session()

fhir_query_response = None
fhir_query_headers = {'Authorization': fhir_auth_token}
# Find all Patient resources that have an identifier with this system, 
# and (have active=true, or the active property not present).
# Count of 5000 should be fine for the current use case but we may want to support pagination instead.
fhir_query_params = {'identifier': 'http://www.uwmedicine.org/epic_patient_id|', 'active': ':not=false', '_count': '5000'}
#fhir_query_params = {'identifier': 'uwDAL_Clarity|' + str(pat_data['pat_id']) + ',http://www.uwmedicine.org/epic_patient_id|' + str(pat_data['pat_id'])}
fhir_query_response = session.get(fhir_endpoint + '/Patient', headers = fhir_query_headers, params = fhir_query_params)

if debug_level > '8':
    log_it("FHIR patient query URL: " + fhir_query_response.url)

pat_cnt = 0

if fhir_query_response is not None:
    if fhir_query_response.status_code != 200:
        log_it("FHIR patient query failed, status code: " + str(fhir_query_response.status_code))
        break
    else:
        fhir_query_reply = fhir_query_response.json()

        if debug_level > '8':
            log_it("FHIR patient query response: " + json.dumps(fhir_query_reply))

        # iterate over fhir_query_reply["entry"]
        for entry in fhir_query_reply["entry"]
            patient_hapi_id = entry["resource"]["id"]
            activeStatusMsg = "the \"active\" attribute was not present; adding it, set to false."
            if "active" in entry["resource"]:
                if entry["resource"]["active"] == false:
                    log_it("Patient ID (" + str(pat_data['pat_id']) + ") matches criteria, but the active attribute was found to be false already. This is not expected, halting this script now.")
                    errant_state = true
                    break
                else:                    
                    activeStatusMsg = "the \"active\" attribute was set to true; changing it to false.";
            log_it("Patient ID (" + str(pat_data['pat_id']) + ") matches criteria:" + activeStatusMsg)
            entry["resource"]["active"] = false
            
            if dry_run < '1':
            
                fhir_patient_response = session.put(fhir_endpoint + "/Patient/" + patient_hapi_id, json = entry["resource"], headers = fhir_patient_headers)

                if fhir_patient_response is not None:
                    fhir_patient_reply = fhir_patient_response.json()
                    if fhir_query_response.status_code != 201:
                        log_it("ERROR: Unable to update/PUT Patient id " + patient_hapi_id + " at " + fhir_patient_response.url + ", skipping. Response code was " + fhir_query_response.status_code + "(!= 201) and json was: " + json.dumps(fhir_patient_reply))
                    else: 
                        if debug_level > '8':
                            log_it("FHIR patient PUT URL: " + fhir_patient_response.url)
                        pat_cnt = pat_cnt + 1
                        if debug_level > '8':
                            log_it("FHIR patient PUT response: " + json.dumps(fhir_patient_reply))
                        log_it("Successfully updated Patient " + patient_hapi_id)
                else:
                    log_it("ERROR: Unable to update/PUT Patient id " + patient_hapi_id + "at " + fhir_patient_response.url + " (no response), skipping.")
        else:
            log_it("ERROR: Unable to query FHIR store for patients... exiting.")

log_it("Total patients added/updated: " + str(pat_cnt))

log_it("=========================== FINISH RUN ================================")

LOG_FILE.close()
