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

now = datetime.datetime.now()

config = dotenv_values("config.env")

LOG_FILE = open(config['LOG_FILE_PATH'], "a", encoding="utf-8")

fhir_endpoint = config['FHIR_ENDPOINT']
fhir_auth_token = config['FHIR_AUTH_TOKEN']
fume_endpoint = config['FUME_ENDPOINT']

log_it("=========================== STARTING DAILY RUN =============================")

# Set debug level, anything less than 9 is "info/warning", 9 or greater is "debug"
debug_level = config['DEBUG_LEVEL']

    # Check if patient already exists in FHIR store, update if found, insert if not
    fhir_query_response = None
    fhir_query_headers = {'Authorization': fhir_auth_token}
    fhir_query_params = {'identifier': 'uwDAL_Clarity|' + str(pat_data['pat_id']) + ',http://www.uwmedicine.org/epic_patient_id|' + str(pat_data['pat_id'])}
    fhir_query_response = requests.get(fhir_endpoint + '/Patient', headers = fhir_query_headers, params = fhir_query_params)

    if debug_level > '8':
        log_it("FHIR patient query URL: " + fhir_query_response.url)

    if fhir_query_response is not None:
        if fhir_query_response.status_code != 200:
            log_it("FHIR patient query failed, status code: " + str(fhir_query_response.status_code))
            break
        else:
            fhir_query_reply = fhir_query_response.json()
    
            if debug_level > '8':
                log_it("FHIR patient query response: " + json.dumps(fhir_query_reply))
        
            if fhir_query_reply["total"] > 1:
                log_it("ERROR: Multiple existing patients found with same ID (" + str(pat_data['pat_id']) + "), this should never happen... exiting.")
            else:
                if fhir_query_reply["total"] == 1:
                    if "entry" in fhir_query_reply:                                     # Existing patient found, update
                        log_it("Patient ID (" + str(pat_data['pat_id']) + ") found in FHIR store, updating...")
                        patient_request_method = "PUT"
                        patient_hapi_id = fhir_query_reply["entry"][0]["resource"]["id"]
    
                        if debug_level > '8':
                            log_it("Existing patient resource found, HAPI ID (" + str(patient_hapi_id) + ")")
                    
                        # Need to pull any existing identifiers (except 'epic_patient_id' and 'mrn') out of the existing patient resource to add them to the update bundle
                        addl_identifiers = {}
                        for identifier in fhir_query_reply["entry"][0]["resource"]["identifier"]:
                            if identifier["system"] in ["http://www.uwmedicine.org/mrn", "http://www.uwmedicine.org/epic_patient_id"]:
                                continue
    
                            if debug_level > '8':
                                log_it("Adding existing identifier to updated patient resource bundle: " + identifier["system"] + "|" + identifier["value"])
                        
                            updated_pat_map = pat_map + """
  * identifier
    * system = '""" + identifier["system"] + """'
    * value = \"""" + identifier["value"] + """\"
    """
                else:                                                                   # Patient not fouund, insert as new
                    log_it("Patient ID (" + str(pat_data['pat_id']) + ") not found in FHIR store, adding...")
                    patient_request_method = "POST"           
                    patient_hapi_id = None
                
                    # Send patient resource to FHIR server
                    fhir_patient_response = None
                    fhir_patient_headers = {'Content-type': 'application/fhir+json;charset=utf-8',
                                            'Authorization': fhir_auth_token}
                    if patient_request_method == "POST":
                        fhir_patient_response = requests.post(fhir_endpoint, json = pat_bundle, headers = fhir_patient_headers)
                    else:
                        fume_patient_response_json = fume_patient_response.json()
                        fume_patient_response_json["id"] = patient_hapi_id
                        fhir_patient_response = requests.put(fhir_endpoint + "/Patient/" + patient_hapi_id, json = fume_patient_response_json, headers = fhir_patient_headers)
                    if fhir_patient_response is not None:
    
                        if debug_level > '8':
                            log_it("FHIR patient " + patient_request_method + " URL: " + fhir_patient_response.url)
                    
                        fhir_patient_reply = fhir_patient_response.json()
    
                        if debug_level > '8':
                            log_it("FHIR patient " + patient_request_method + " response: " + json.dumps(fhir_patient_reply))
                    
                        if "entry" in fhir_patient_reply:
                            patient_hapi_id = fhir_patient_reply["entry"][0]["response"]["location"].split("/")[1]
                        if patient_request_method == "POST":
                            patient_action = "added"
                        else:
                            patient_action = "updated"
                        log_it("Patient ID (" + str(pat_data['pat_id']) + ") resource " + patient_action + ", HAPI ID (" + str(patient_hapi_id) + ")...")
                        pat_cnt = pat_cnt + 1
                        
                                    # Delete any existing FHIR procedure resources not found in the current list of patient procedures from the DAWG
                                    for proc_id in list(set(existing_fhir_proc_ids.keys()).difference(dawg_proc_ids)):
                                        fhir_proc_del_response = None
                                        fhir_proc_del_response = requests.delete(fhir_endpoint + "/Procedure/" + existing_fhir_proc_ids[proc_id])
    
                                        if debug_level > '8':
                                            log_it("FHIR procedure DELETE URL: " + fhir_proc_del_response.url)
                                    
                                        if fhir_proc_del_response is not None:
    
                                            if debug_level > '8':
                                                log_it("FHIR procedure DELETE response: " + json.dumps(fhir_proc_del_response.json()))
    
                                            log_it("Procedure ID (" + str(proc_id) + ") resource deleted, HAPI ID (" + str(existing_fhir_proc_ids[proc_id]) + ")...")
                                            proc_del_cnt = proc_del_cnt + 1
                    else:
                        log_it("ERROR: Unable to add patient resource with ID (" + str(pat_data["pat_id"]) + "), skipping...")
                else:
                    log_it("ERROR: No data returned from FUME... exiting.")
    else:
        log_it("ERROR: Unable to query FHIR store for patients... exiting.")

log_it("Total patients added/updated: " + str(pat_cnt))
log_it("Total procedures deleted: " + str(proc_del_cnt))

log_it("=========================== FINISH DAILY RUN =============================")

LOG_FILE.close()
