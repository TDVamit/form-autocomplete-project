import os
import nest_asyncio
import re
import copy
from typing import Any, List, Union
from agents import Agent, RunContextWrapper, Runner, function_tool,Usage,RunHooks
from dataclasses import dataclass
from openai import AsyncOpenAI
import json
import datetime
import asyncio
import hashlib
from datetime import datetime
import asyncio
import copy



# Add after the existing imports
_description_cache = {}
_field_cache = {}

def get_descriptions_cached(data_hash):
    """Cache descriptions extraction"""
    if data_hash not in _description_cache:
        _description_cache[data_hash] = extract_descriptions(data.data)
    return _description_cache[data_hash]

def get_next_field_cached(data_hash, data):
    """Cache next field computation"""
    if data_hash not in _field_cache:
        _field_cache[data_hash] = next_field(data)
    return _field_cache[data_hash]

def get_data_hash(data):
    """Generate hash for form data state"""
    return hashlib.md5(json.dumps(data.data, sort_keys=True).encode()).hexdigest()

# Function to log messages to a file with timestamp
LIVE_LOGS = []

def log_to_file(message):
    try:
      timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      try:
          with open("form_autocomplete.log", "a", encoding="utf-8") as log_file:
              log_file.write(f"[{timestamp}] {message}\n")
          LIVE_LOGS.append(f"[{timestamp}] {message}")
      except UnicodeEncodeError:
          # If Unicode encoding fails, try to clean the message
          clean_message = str(message).encode('ascii', 'replace').decode('ascii')
          with open("form_autocomplete.log", "a", encoding="utf-8") as log_file:
              log_file.write(f"[{timestamp}] {clean_message} (Unicode characters removed)\n")
          LIVE_LOGS.append(f"[{timestamp}] {clean_message} (Unicode characters removed)")
      except Exception as e:
          # Last resort fallback - write to a separate error log
          with open("log_errors.txt", "a", encoding="utf-8") as error_file:
              error_file.write(f"[{timestamp}] Error logging message: {str(e)}\n")
          LIVE_LOGS.append(f"[{timestamp}] Error logging message: {str(e)}")
    except Exception as e:
      print(f"error in log_to_file: {e}")

# Function to get the last n live logs
def get_live_logs(n=50):
    return LIVE_LOGS[-n:]

# Apply nest_asyncio patch to allow nested event loops
nest_asyncio.apply()

form = {
  "lead_repo": {
    "type": "object",
    "description": "Lead repo",
    "is_required": True,
    "value": {
      "insured": {
        "type": "object",
        "description": "Insured's details",
        "ask_collected":True,
        "is_required": True,
        "value": {
          "first_name": {
            "type": "string",
            "description": "Insured first name",
            "is_required": True,
            "value": None
          },
          "middle_name": {
            "type": "string",
            "description": "Insured middle name",
            "is_required": False,
            "value": None
          },
          "last_name": {
            "type": "string",
            "description": "Insured last name",
            "is_required": True,
            "value": None
          }
        }
      },
      "date_of_birth": {
        "type": "date",
        "description": "Insured dob",
        "is_required": True,
        "value": None
      },
      "gender": {
        "type": "enum",
        "description": "Insured gender",
        "is_required": True,
        "value": None,
        "enum": ["Male", "Female", "Other"]
      },
      "marital_status": {
        "type": "enum",
        "description": "Insured marital status",
        "is_required": False,
        "value": None,
        "enum": ["Single", "Married", "Divorced", "Widowed", "Domestic Partner"]
      },
      "email": {
        "type": "string",
        "description": "Insured email",
        "is_required": True,
        "value": None
      },
      "phone_number": {
        "type": "object",
        "description": "Insured phone number",
        "ask_collected":True,
        "is_required": True,
        "value": {
          "country_code": {
            "type": "string",
            "description": "country code",
            "is_required": True,
            "value": None
          },
          "number": {
            "type": "string",
            "description": "phone number",
            "is_required": True,
            "value": None
          }
        }
      },
      "can_text": {
        "type": "boolean",
        "description": "Insured text-capable?", 
        "is_required": False,
        "value": None
      },
      "contact_preference": {
        "type": "enum",
        "description": "Contact method",
        "is_required": False,
        "value": None,
        "enum": ["Phone", "Email", "Text"]
      },
      "occupation": {
        "type": "string",
        "description": "Insured occupation",
        "is_required": False,
        "value": None
      },
      "education": {
        "type": "enum",
        "description": "Insured education",
        "is_required": False,
        "value": None,
        "enum": ["High School", "Some College", "Associates Degree", "Bachelors", "Masters", "PhD"]
      },
      "social_security_number": {
        "type": "string",
        "description": "Insured SSN",
        "is_required": True,
        "value": None
      },
      "address_detail": {
        "type": "object",
        "description": "Address details",
        "is_required": True,
        "value": {
          "insured_address": {
            "type": "object",
            "description": "Insured address",
            "ask_collected":True,
            "is_required": True,
            "value": {
              "street_address": {
                "type": "string",
                "description": "insured street",
                "is_required": True,
                "value": None
              },
              "city": {
                "type": "string",
                "description": "insured city",
                "is_required": True,
                "value": None
              },
              "state": {
                "type": "string",
                "description": "insured state",
                "is_required": True,
                "value": None
              },
              "zip_code": {
                "type": "string",
                "description": "zip code",
                "is_required": True,
                "value": None
              }
            }
          },
          "mailing_address": {
            "type": "object",
            "description": "Mailing address",
            "ask_collected":True,
            "is_required": False,
            "value": {
              "street_address": {
                "type": "string",
                "description": "Mailing street",
                "is_required": False,
                "value": None
              },
              "city": {
                "type": "string",
                "description": "Mailing city",
                "is_required": False,
                "value": None
              },
              "state": {
                "type": "string",
                "description": "Mailing state",
                "is_required": False,
                "value": None
              },
              "zip_code": {
                "type": "string",
                "description": "Mailing ZIP code",
                "is_required": False,
                "value": None
              }
            }
          },
          "years_at_address": {
            "type": "integer",
            "description": "Years at address",
            "is_required": False,
            "value": None
          },
          "county": {
            "type": "string",
            "description": "County",
            "is_required": False,
            "value": None
          },
          
        }
      }
    }
  },
  "questionaire_repo": {
      "type": "object",
      "description": "Questionnaire repo",
      "is_required": False,
      "value": {
      "number_of_co_insured": {
          "type": "integer",
          "description": "Number of co-insured",
          "is_required": False,
          "value": None
      },
      "co_insured": {
          "type": "list",
          "description": "List of co‑insured entries",
          "is_required": False,
          "value": [
              {
                  "type": "object",
                  "description": "Co‑insured details",
                  "is_required": False,
                  "value": {
                      "name": {
                          "type": "object",
                          "description": "Name object",
                          "ask_collected": True,
                          "is_required": False,
                          "value": {
                              "first_name": {"type": "string", "description": "First name", "is_required": False, "value": None},
                              "middle_name":{"type":"string","description":"Middle name","is_required":False,"value":None},
                              "last_name": {"type":"string","description":"Last name","is_required":False,"value":None},
                          }
                      },
                      "date_of_birth":       {"type":"date","description":"DOB (YYYY-MM-DD)","is_required":False,"value":None},
                      "gender":              {"type":"enum","description":"Gender","is_required":False,"value":None,"enum":["Male","Female","Other"]},
                      "relationship":        {"type":"enum","description":"Relation to insured","is_required":False,"value":None,"enum":["Spouse","Child","Parent","Other"]},
                      "marital_status":      {"type":"enum","description":"Marital status","is_required":False,"value":None,"enum":["Single","Married","Divorced","Widowed","Domestic Partner"]},
                      "occupation":          {"type":"string","description":"Occupation","is_required":False,"value":None},
                      "education":           {"type":"enum","description":"Education level","is_required":False,"value":None,"enum":["High School","Some College","Associates Degree","Bachelors","Masters","PhD"]},
                  }
              }
          ]
      },
      "additional_co_insured": {
        "type": "boolean",
        "description": "Additional co-insured",
        "is_required": False,
        "value": None
      },
      "policy_details": {
          "type": "object",
          "description": "Policy details",
          "is_required": False,
          "value": {
              "effective_date":       {"type":"string","description":"YYYY‑MM‑DD","is_required":False,"value":None},
              "use":                  {"type":"enum","description":"UseType","is_required":False,"value":None},
              "policy_form":          {"type":"enum","description":"PolicyForm","is_required":False,"value":None},
              "protection_class":     {"type":"object","description":"CoverageDetails","is_required":False,"value":{}},
              "prior_carrier":        {"type":"string","description":"Prior carrier","is_required":False,"value":None},
              "prior_carrier_premium":{"type":"number","description":"Prior carrier premium","is_required":False,"value":None},
          }
      },
      "property_details": {
          "type": "object",
          "description": "Property details",
          "is_required": False,
          "value": {
              "year_built":              {"type":"integer","description":"Year built","is_required":False,"value":None},
              "effective_year_built":    {"type":"integer","description":"Effective year built","is_required":False,"value":None},
              "residence_type":          {"type":"enum","description":"ResidenceType","is_required":False,"value":None},
              "square_footage":          {"type":"integer","description":"Square footage","is_required":False,"value":None},
              "roof_type_shape":         {"type":"string","description":"Roof type/shape","is_required":False,"value":None},
              "electrical_panel_type":   {"type":"string","description":"Electrical panel","is_required":False,"value":None},
              "foundation":              {"type":"enum","description":"FoundationType","is_required":False,"value":None},
              "floors_stories":          {"type":"integer","description":"Floors/stories","is_required":False,"value":None},
              "exterior":                {"type":"string","description":"Exterior","is_required":False,"value":None},
              "framing":                 {"type":"string","description":"Framing","is_required":False,"value":None},
              "construction_style":      {"type":"string","description":"Construction style","is_required":False,"value":None},
              "construction_quality":    {"type":"string","description":"Construction quality","is_required":False,"value":None},
              "kitchen_quality":         {"type":"string","description":"Kitchen quality","is_required":False,"value":None},
              "bedrooms":                {"type":"integer","description":"Bedrooms","is_required":False,"value":None},
              "full_bathrooms":          {"type":"integer","description":"Full bathrooms","is_required":False,"value":None},
              "half_bathrooms":          {"type":"integer","description":"Half bathrooms","is_required":False,"value":None},
              "bathroom_quality":        {"type":"string","description":"Bathroom quality","is_required":False,"value":None},
              "garage_type":             {"type":"enum","description":"GarageType","is_required":False,"value":None},
              "garage_stalls":           {"type":"integer","description":"Garage stalls","is_required":False,"value":None},
              "number_of_detached_structures":{"type":"integer","description":"Number of detached structures","is_required":False,"value":None},
              "detached_structure_types":{"type":"list","description":"Detached structures","is_required":False,"value":[
                {"type":"object","description":"Detached structures details","is_required":False,"value":{"detached_structure_type":{
                  "type": "object",
                  "description": "Detached structure one",
                  "is_required": False,
                  "value": None
                }}}
              ]},
              "additional_structures":{"type":"boolean","description":"Additional structures","is_required":False,"value":None},
              "number_of_occupants":     {"type":"integer","description":"Number of occupants","is_required":False,"value":None},
          }
      },
      "risk_details": {
          "type": "object",
          "description": "Risk details",
          "is_required": False,
          "value": {
              "has_animals":              {"type":"boolean","description":"Has animals?","is_required":False,"value":None},
              "number_of_animals":        {"type":"integer","description":"Number of animals","is_required":False,"value":None},
              "animals":                  {"type":"list","description":"Animal types","is_required":False,"value":[
                {"type":"object","description":"Animal one","is_required":False,"value":{"animal_type":{
                  "type": "object",
                  "description": "Animal one",
                  "is_required": False,
                  "value": None
                }}}
              ]},
              "additional_animals":{"type":"boolean","description":"Additional animals","is_required":False,"value":None},
              "other_animals":            {"type":"string","description":"Othser animals","is_required":False,"value":None},
              "has_trampoline":           {"type":"boolean","description":"Has trampoline?","is_required":False,"value":None},
              "has_pool":                 {"type":"boolean","description":"Has pool?","is_required":False,"value":None},
              "pool_has_protective_covering":{"type":"boolean","description":"Pool covering?","is_required":False,"value":None},
              "ni_owns_other_properties": {"type":"boolean","description":"Owns other properties?","is_required":False,"value":None},
          }
      },
      "mortgage_details": {
          "type":"object",
          "description":"Mortgage details",
          "is_required":False,
          "value": {
              "mortgage_company": {"type":"string","description":"Company","is_required":False,"value":None},
              "loan_number":      {"type":"string","description":"Loan #","is_required":False,"value":None},
          }
      },
      "prior_claims_last_5_years": {
          "type":"boolean","description":"Claims in last 5 yrs?","is_required":False,"value":None
      },
  }
  }
}


co_insured = [
        {
            "name": {
                "first_name": None,
                "middle_name": None,
                "last_name": None
            },
            "date_of_birth": None,
            "gender": None,
            "relationship": None,
            "marital_status": None,
            "occupation": None,
            "education": None,
            "license_status": None,
            "licensed_state": None,
            "license_number": None,
            "licensed_age": None,
            "rated": None,
            "sr22_required": None,
            "drive_for_rideshare": None,
            "drive_for_delivery": None,
            "driver_discounts": None,
            "good_student_discount": None,
            "mature_driver_discount": None,
            "safe_driver_discount": None
        }
    ]

animals = [
    {
        "animal_type": None
    }
]

detached_structures = [
    {
        "detached_structure_type": None
    }
]

field_mapping = {

    "lead_repo.value.insured.value.first_name.value":           "lead_repo.insured.first_name",
    "lead_repo.value.insured.value.middle_name.value":          "lead_repo.insured.middle_name",
    "lead_repo.value.insured.value.last_name.value":            "lead_repo.insured.last_name",

    "lead_repo.value.date_of_birth.value":                      "lead_repo.date_of_birth.$date",
    "lead_repo.value.gender.value":                            "lead_repo.gender",
    "lead_repo.value.marital_status.value":                    "lead_repo.marital_status",
    "lead_repo.value.email.value":                             "lead_repo.email",

    "lead_repo.value.phone_number.value.country_code.value":    "lead_repo.phone_number.country_code",
    "lead_repo.value.phone_number.value.number.value":          "lead_repo.phone_number.number",

    "lead_repo.value.can_text.value":                          "lead_repo.can_text",
    "lead_repo.value.contact_preference.value":                "lead_repo.contact_preference",
    "lead_repo.value.occupation.value":                        "lead_repo.occupation",
    "lead_repo.value.education.value":                         "lead_repo.education",
    "lead_repo.value.social_security_number.value":            "lead_repo.social_security_number",

    "lead_repo.value.address_detail.value.insured_address.value.street_address.value":
                                                               "lead_repo.address_detail.insured_address.street_address",
    "lead_repo.value.address_detail.value.insured_address.value.city.value":
                                                               "lead_repo.address_detail.insured_address.city",
    "lead_repo.value.address_detail.value.insured_address.value.state.value":
                                                               "lead_repo.address_detail.insured_address.state",
    "lead_repo.value.address_detail.value.insured_address.value.zip_code.value":
                                                               "lead_repo.address_detail.insured_address.zip_code",

    "lead_repo.value.address_detail.value.mailing_address.value.street_address.value":
                                                               "lead_repo.address_detail.mailing_address.street_address",
    "lead_repo.value.address_detail.value.mailing_address.value.city.value":
                                                               "lead_repo.address_detail.mailing_address.city",
    "lead_repo.value.address_detail.value.mailing_address.value.state.value":
                                                               "lead_repo.address_detail.mailing_address.state",
    "lead_repo.value.address_detail.value.mailing_address.value.zip_code.value":
                                                               "lead_repo.address_detail.mailing_address.zip_code",

    "lead_repo.value.address_detail.value.years_at_address.value":
                                                               "lead_repo.address_detail.years_at_address",
    "lead_repo.value.address_detail.value.county.value":
                                                               "lead_repo.address_detail.county",

    "questionaire_repo.value.number_of_co_insured.value": "questionaire_repo.number_of_co_insured",
    "questionaire_repo.value.additional_co_insured.value": "questionaire_repo.additional_co_insured",
    "questionaire_repo.value.policy_details.value.effective_date.value":
                                                               "questionaire_repo.policy_details.effective_date",
    "questionaire_repo.value.policy_details.value.use.value":
                                                               "questionaire_repo.policy_details.use",
    "questionaire_repo.value.policy_details.value.policy_form.value":
                                                               "questionaire_repo.policy_details.policy_form",
    "questionaire_repo.value.policy_details.value.prior_carrier.value":
                                                               "questionaire_repo.policy_details.prior_carrier",
    "questionaire_repo.value.policy_details.value.prior_carrier_premium.value":
                                                               "questionaire_repo.policy_details.prior_carrier_premium",

    "questionaire_repo.value.property_details.value.year_built.value":
                                                               "questionaire_repo.property_details.year_built",
    "questionaire_repo.value.property_details.value.effective_year_built.value":
                                                               "questionaire_repo.property_details.effective_year_built",
    "questionaire_repo.value.property_details.value.residence_type.value":
                                                               "questionaire_repo.property_details.residence_type",
    "questionaire_repo.value.property_details.value.square_footage.value":
                                                               "questionaire_repo.property_details.square_footage",
    "questionaire_repo.value.property_details.value.roof_type_shape.value":
                                                               "questionaire_repo.property_details.roof_type_shape",
    "questionaire_repo.value.property_details.value.electrical_panel_type.value":
                                                               "questionaire_repo.property_details.electrical_panel_type",
    "questionaire_repo.value.property_details.value.foundation.value":
                                                               "questionaire_repo.property_details.foundation",
    "questionaire_repo.value.property_details.value.floors_stories.value":
                                                               "questionaire_repo.property_details.floors_stories",
    "questionaire_repo.value.property_details.value.exterior.value":
                                                               "questionaire_repo.property_details.exterior",
    "questionaire_repo.value.property_details.value.framing.value":
                                                               "questionaire_repo.property_details.framing",
    "questionaire_repo.value.property_details.value.construction_style.value":
                                                               "questionaire_repo.property_details.construction_style",
    "questionaire_repo.value.property_details.value.construction_quality.value":
                                                               "questionaire_repo.property_details.construction_quality",
    "questionaire_repo.value.property_details.value.kitchen_quality.value":
                                                               "questionaire_repo.property_details.kitchen_quality",
    "questionaire_repo.value.property_details.value.bedrooms.value":
                                                               "questionaire_repo.property_details.bedrooms",
    "questionaire_repo.value.property_details.value.full_bathrooms.value":
                                                               "questionaire_repo.property_details.full_bathrooms",
    "questionaire_repo.value.property_details.value.half_bathrooms.value":
                                                               "questionaire_repo.property_details.half_bathrooms",
    "questionaire_repo.value.property_details.value.bathroom_quality.value":
                                                               "questionaire_repo.property_details.bathroom_quality",
    "questionaire_repo.value.property_details.value.garage_type.value":
                                                               "questionaire_repo.property_details.garage_type",
    "questionaire_repo.value.property_details.value.garage_stalls.value":
                                                               "questionaire_repo.property_details.garage_stalls",
    "questionaire_repo.value.property_details.value.detached_structure_types.value":
                                                               "questionaire_repo.property_details.detached_structure_types",
    "questionaire_repo.value.property_details.value.additional_structures.value":
                                                               "questionaire_repo.property_details.additional_structures",
    "questionaire_repo.value.property_details.value.number_of_occupants.value":
                                                               "questionaire_repo.property_details.number_of_occupants",

    "questionaire_repo.value.risk_details.value.has_animals.value":
                                                               "questionaire_repo.risk_details.has_animals",
    "questionaire_repo.value.risk_details.value.number_of_animals.value":
                                                               "questionaire_repo.risk_details.number_of_animals",

    "questionaire_repo.value.risk_details.value.additional_animals.value":
                                                               "questionaire_repo.risk_details.additional_animals",
    "questionaire_repo.value.risk_details.value.other_animals.value":
                                                               "questionaire_repo.risk_details.other_animals",
    "questionaire_repo.value.risk_details.value.has_trampoline.value":
                                                               "questionaire_repo.risk_details.has_trampoline",
    "questionaire_repo.value.risk_details.value.has_pool.value":
                                                               "questionaire_repo.risk_details.has_pool",
    "questionaire_repo.value.risk_details.value.pool_has_protective_covering.value":
                                                               "questionaire_repo.risk_details.pool_has_protective_covering",
    "questionaire_repo.value.risk_details.value.ni_owns_other_properties.value":
                                                               "questionaire_repo.risk_details.ni_owns_other_properties",

    "questionaire_repo.value.mortgage_details.value.mortgage_company.value":
                                                               "questionaire_repo.mortgage_details.mortgage_company",
    "questionaire_repo.value.mortgage_details.value.loan_number.value":
                                                               "questionaire_repo.mortgage_details.loan_number",

    "questionaire_repo.value.prior_claims_last_5_years.value":
                                                               "questionaire_repo.prior_claims_last_5_years",
}


field_mapping_lists = {
    "questionaire_repo.value.co_insured.value":"questionaire_repo.co_insured",
    "questionaire_repo.value.risk_details.value.animals.value":"questionaire_repo.risk_details.animals",
    "questionaire_repo.value.property_details.value.detached_structure_types.value": "questionaire_repo.property_details.detached_structure_types",
}

# 1. co_insured subfield mapping
co_insured_field_map = {
    "value.name.value.first_name.value":    "name.first_name",
    "value.name.value.middle_name.value":   "name.middle_name",
    "value.name.value.last_name.value":     "name.last_name",
    "value.date_of_birth.value":            "date_of_birth",
    "value.gender.value":                   "gender",
    "value.relationship.value":             "relationship",
    "value.marital_status.value":           "marital_status",
    "value.occupation.value":               "occupation",
    "value.education.value":                "education",
}

animal_field_map = {
    "value.animal_type.value": "animal_type",

}

detached_structure_field_map = {
    "value.detached_structure_type.value": "detached_structure_type",
}


def sync_lists(form: dict,db_data: dict,mapping:dict,get_form:bool=True) -> dict:
    data_mapping_lists = {
      "questionaire_repo.value.co_insured.value": co_insured_field_map,
      "questionaire_repo.value.risk_details.value.animals.value": animal_field_map,
      "questionaire_repo.value.property_details.value.detached_structure_types.value": detached_structure_field_map,
      }
    copy_list_mapping_lists = {
      "questionaire_repo.value.co_insured.value": co_insured,
      "questionaire_repo.value.risk_details.value.animals.value": animals,
      "questionaire_repo.value.property_details.value.detached_structure_types.value": detached_structures,
      }
    for form_path, db_path in mapping.items():
        form_tokens = _parse_tokens(form_path)
        db_tokens = _parse_tokens(db_path)
        cur_form = form
        cur_db = db_data
        for i, token in enumerate(form_tokens[:-1]):
            cur_form = cur_form[token]
        form_final = form_tokens[-1]
        for i, token in enumerate(db_tokens[:-1]):
            cur_db = cur_db[token]
        db_final = db_tokens[-1]
        if get_form:
            list_length = len(cur_db[db_final])
            resize_list_with_ordinal(
                form,
                form_tokens,
                list_length
            )
        else:
            list_length = len(cur_form[form_final])
            copy_list = []
            for i in range(list_length):
                copy_list.extend(copy_list_mapping_lists[form_path])
            cur_db[db_final] = copy_list

        for i in range(list_length):
            db_form_conversion(cur_form[form_final][i], cur_db[db_final][i], data_mapping_lists[form_path], get_form,called_from_sync=True)

    if get_form:
        return form
    else:
        return db_data



def db_form_conversion(form: dict, db_data: dict,mapping:dict, get_form:bool=True,called_from_sync:bool=False) -> dict:
    output = {}
    for form_path, db_path in mapping.items():
      form_tokens = _parse_tokens(form_path)
      db_tokens = _parse_tokens(db_path)
      cur_form = form
      cur_db = db_data
      for i, token in enumerate(form_tokens[:-1]):
          cur_form = cur_form[token]
      form_final = form_tokens[-1]
      for i, token in enumerate(db_tokens[:-1]):
          cur_db = cur_db[token]        
      db_final = db_tokens[-1]
      if get_form:
        cur_form[form_final] = cur_db[db_final]
        output = form
      else:
        cur_db[db_final] = cur_form[form_final]
        output = db_data
    if not called_from_sync:
        sync_lists(form,db_data,field_mapping_lists,get_form=get_form)
    return output

def isComplete(field_object):
    try:
      field_type = field_object.get('type')
      value = field_object.get('value')
      
      if field_type not in {'list', 'object'}:
        return False if value is None else True

      elif field_type == "object":
        if not isinstance(value, dict):
          return False
        for sub_field_name, sub_field_object in value.items():
          if isinstance(sub_field_object, dict) and not isComplete(sub_field_object):
            return False
        return True

      elif field_type == "list":
        if not value or not isinstance(value, list):
          return False
        elif not isinstance(value[0], dict):
          return True
        for sub_field_object in value:
          if isinstance(sub_field_object, dict):
            sub_field_object = {f'field': sub_field_object}
            if not isComplete(sub_field_object):
              return False
        return True
    except Exception as e:
        log_to_file(f"exeption occured while finding if complete or not : { str(e)}")
        return True

def normalise(field_dict, current_path=""):
    try:
      for key, field in field_dict.items():
          field_path = f"{current_path}.value.{key}" if current_path else f"{key}"
          field["json_path"] = field_path + ".value"

          # Recurse into objects
          if field["type"] == "object":
              if "value" in field and isinstance(field["value"], dict):
                  normalise(field["value"], field_path)

          # Recurse into lists
          elif field["type"] == "list":
              # Check if field["value"] exists and is actually a list
              if "value" in field and isinstance(field["value"], list):
                  for idx, item in enumerate(field["value"]):
                      # Ensure item is a dictionary before accessing its properties
                      if isinstance(item, dict):
                          item_path = f"{field_path}.value[{idx}]"
                          item["json_path"] = item_path + ".value"
                          if item.get("type") == "object" and "value" in item and isinstance(item["value"], dict):
                              normalise(item["value"], item_path)
    except Exception as e:
        log_to_file(f"exeption occured while normalising : { str(e)}")
        

def next_field(form_object):
  for field_name, field_object in form_object.items():
    if not isinstance(field_object, dict):
      continue
      
    value = field_object.get('value')

    if field_object.get("ask_collected") and not isComplete(field_object):
      field_object["key"] = field_name
      return field_object

    if field_object.get('type') == 'object' and isinstance(value, dict):
        field = next_field(value)
        if field is not None:
          return field

    elif field_object.get('type') == 'list':
      if value == []:
          continue
      elif value is None:
        return field_object
      elif not isinstance(value, list) or not value:
        return None
      elif not isinstance(value[0], dict):
        return None
      for i, sub_field_object in enumerate(value):
        if isinstance(sub_field_object, dict):
          sub_field_object = {f'{field_name} {i}': sub_field_object}
          field = next_field(sub_field_object)
          if field is not None:
            return field

    else:
      if not isComplete(field_object):
        field_object["key"] = field_name
        return field_object
  return None




def extract_description_to_path(schema: dict) -> dict:
    """
    Traverse a nested schema dict and return a mapping from each
    'description' to its corresponding 'json_path'.
    """
    result = {}

    def recurse(node):
        # If this node has both description and json_path, record it
        if isinstance(node, dict):
            desc = node.get("description")
            path = node.get("json_path")
            if desc is not None and path is not None:
                result[desc] = path

            # Now dive into any children under 'value'
            if "value" in node:
                val = node["value"]
                if isinstance(val, dict):
                    recurse(val)
                elif isinstance(val, list):
                    for item in val:
                        recurse(item)

            # Also explore other dict/list fields just in case
            for v in node.values():
                if isinstance(v, dict):
                    recurse(v)
                elif isinstance(v, list):
                    for item in v:
                        recurse(item)

    recurse(schema)
    return result

def extract_descriptions(schema: dict) -> dict:
    """
    Traverse a nested schema dict and return a mapping from each
    'description' to its corresponding 'json_path'.
    """
    result = []

    def recurse(node):
        # If this node has both description and json_path, record it
        if isinstance(node, dict):
            desc = node.get("description")
            path = node.get("json_path")
            if desc is not None and path is not None:
                result.append(desc)

            # Now dive into any children under 'value'
            if "value" in node:
                val = node["value"]
                if isinstance(val, dict):
                    recurse(val)
                elif isinstance(val, list):
                    for item in val:
                        recurse(item)

            # Also explore other dict/list fields just in case
            for v in node.values():
                if isinstance(v, dict):
                    recurse(v)
                elif isinstance(v, list):
                    for item in v:
                        recurse(item)

    recurse(schema)
    return result

def extract_field_names(schema: dict) -> list:
    result = []

    def recurse(node, parent_key=None):
        if isinstance(node, dict):
            path = node.get("json_path")
            if path is not None and parent_key is not None:
                result.append(parent_key)

            # Check for nested structures under "value"
            if "value" in node:
                val = node["value"]
                if isinstance(val, dict):
                    recurse(val)
                elif isinstance(val, list):
                    for item in val:
                        recurse(item)

            # Continue recursion for other dictionary values
            for key, value in node.items():
                if isinstance(value, dict):
                    recurse(value, key)
                elif isinstance(value, list):
                    for item in value:
                        recurse(item)

    recurse(schema)
    return result


def extract_non_null_values(schema: dict) -> dict:
    """
    Recursively traverse a nested metadata schema and return a flat dict
    mapping each field's json_path to its non-None value.
    """
    result = {}

    def _recurse(node):
        val = node.get("value", None)
        description = node.get("description", None)
        if not isinstance(val, (dict, list)):
            if val is not None:
                result[description]=val
            return

        if isinstance(val, dict):
            for child in val.values():
                _recurse(child)

        elif isinstance(val, list):
            for item in val:
                _recurse(item)
    for top_node in schema.values():
        _recurse(top_node)

    return result



def find_object_by_json_path(schema: dict, target_path: str) -> dict | None:
  """
  Traverse the schema and return the entire object (dict) whose
  'json_path' equals target_path. Returns None if not found.
  """
  def recurse(node):
      if not isinstance(node, dict):
          return None

      # If this node has the matching json_path, return it
      if node.get("json_path") == target_path:
          return node

      # Otherwise, dive into its children
      # 1) Under "value"
      if "value" in node:
          val = node["value"]
          # If it's a dict, recurse there
          if isinstance(val, dict):
              found = recurse(val)
              if found:
                  return found
          # If it's a list, check each element
          elif isinstance(val, list):
              for item in val:
                  found = recurse(item)
                  if found:
                      return found

      # 2) Also search any nested dicts/lists in other fields
      for v in node.values():
          if isinstance(v, dict):
              found = recurse(v)
              if found:
                  return found
          elif isinstance(v, list):
              for item in v:
                  found = recurse(item)
                  if found:
                      return found

      return None

  # Kick off the recursion over every top‑level key
  for top in schema.values():
      result = recurse(top)
      if result:
          return result
  return None


@dataclass
class Form:
    data: dict
    history: list
    language_processor_response: list
    lead_repo: dict
    questionaire_repo: dict
    input_tokens: int
    output_tokens: int
    cached_tokens: int

# Ordinals map for renaming descriptions
ORDINALS = {
    1: "one",  2: "two",   3: "three", 4: "four",  5: "five",
    6: "six",  7: "seven", 8: "eight", 9: "nine", 10: "ten",
}

COMMON_SYNC_FIELDS = {
    "lead_repo.value.insured.value.first_name.value":"questionaire_repo.value.driver_details.value[0].value.name.value.first_name.value",
    "lead_repo.value.insured.value.middle_name.value":"questionaire_repo.value.driver_details.value[0].value.name.value.middle_name.value",
    "lead_repo.value.insured.value.last_name.value":"questionaire_repo.value.driver_details.value[0].value.name.value.last_name.value",
    "lead_repo.value.date_of_birth.value":"questionaire_repo.value.driver_details.value[0].value.date_of_birth.value",
    "lead_repo.value.gender.value":"questionaire_repo.value.driver_details.value[0].value.gender.value",
    "lead_repo.value.marital_status.value":"questionaire_repo.value.driver_details.value[0].value.marital_status.value",
    "lead_repo.value.occupation.value":"questionaire_repo.value.driver_details.value[0].value.occupation.value",
    "lead_repo.value.education.value":"questionaire_repo.value.driver_details.value[0].value.education.value",
    "questionaire_repo.value.driver_details.value[0].value.name.value.first_name.value": "lead_repo.value.insured.value.first_name.value",
    "questionaire_repo.value.driver_details.value[0].value.name.value.middle_name.value": "lead_repo.value.insured.value.middle_name.value",
    "questionaire_repo.value.driver_details.value[0].value.name.value.last_name.value": "lead_repo.value.insured.value.last_name.value",
    "questionaire_repo.value.driver_details.value[0].value.date_of_birth.value": "lead_repo.value.date_of_birth.value",
    "questionaire_repo.value.driver_details.value[0].value.gender.value": "lead_repo.value.gender.value",
    "questionaire_repo.value.driver_details.value[0].value.marital_status.value": "lead_repo.value.marital_status.value",
    "questionaire_repo.value.driver_details.value[0].value.occupation.value": "lead_repo.value.occupation.value",
    "questionaire_repo.value.driver_details.value[0].value.education.value": "lead_repo.value.education.value"
}

def _parse_tokens(path: str) -> List[Union[str, int]]:
    tokens = []
    for token in re.findall(r"[\w$]+|\[\d+\]", path):
        if token.startswith('['):
            tokens.append(int(token[1:-1]))
        else:
            tokens.append(token)
    return tokens

def update_assigned_driver_enums(data: dict):
    qr = data['questionaire_repo']['value']
    drivers = qr['driver_details']['value']
    # Build list of full names
    names = []
    for d in drivers:
        nm = d['value']['name']['value']
        parts = [nm['first_name']['value'] or "",
                 nm['middle_name']['value'] or "",
                 nm['last_name']['value'] or ""]
        full = " ".join(p for p in parts if p).strip() or "<unnamed>"
        if full in names:
            continue
        elif full == "<unnamed>":
            continue
        names.append(full)
    # Assign to each vehicle
    for veh in qr['vehicle_details']['value']:
        veh['value']['assigned_driver']['enum'] = names.copy()
        if veh['value']['assigned_driver']['value'] not in names:
            veh['value']['assigned_driver']['value'] = None

def _replace_ordinal_in_descriptions(node: Any, old_ord: str, new_ord: str):
    """Recursively replace old_ord→new_ord in every description field under node."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "description" and isinstance(v, str):
                node[k] = re.sub(rf"\b{old_ord}\b", new_ord, v, flags=re.IGNORECASE)
            else:
                _replace_ordinal_in_descriptions(v, old_ord, new_ord)
    elif isinstance(node, list):
        for item in node:
            _replace_ordinal_in_descriptions(item, old_ord, new_ord)

def _clear_values(node: Any):
    """
    Recursively wipe out only "real" data:
      • For primitive-typed fields, null out their value.
      • For list-typed fields, if items are dicts (schema templates), recurse;
        otherwise reset to empty list.
      • Always preserve object-typed fields (they carry nested schemas).
    """
    primitive_types = {"string", "integer", "boolean", "date", "enum"}

    if isinstance(node, dict):
        # 1) clear primitives
        if node.get("type") in primitive_types:
            node["value"] = None

        # 2) handle list-valued fields specially
        if "value" in node and isinstance(node["value"], list):
            items = node["value"]
            if items and all(isinstance(item, dict) for item in items):
                # a schema-list: keep it, but clear inside each entry
                for item in items:
                    _clear_values(item)
            else:
                # a data-list: drop all entries
                node["value"] = []

        # 3) recurse into everything else
        for child in node.values():
            _clear_values(child)

    elif isinstance(node, list):
        for item in node:
            _clear_values(item)


def resize_list_with_ordinal(data: dict, list_path: List[Union[str,int]], new_count: int):

    co_insured_list = {'type': 'object', 'description': 'Details for co‑insured one', 'is_required': False, 'value': {'name': {'type': 'object', 'description': "Co‑insured one's name", 'ask_collected': True, 'is_required': False, 'value': {'first_name': {'type': 'string', 'description': 'First name of co‑insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.name.value.first_name.value'}, 'middle_name': {'type': 'string', 'description': 'Middle name of co‑insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.name.value.middle_name.value'}, 'last_name': {'type': 'string', 'description': 'Last name of co‑insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.name.value.last_name.value'}}, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.name.value'}, 'date_of_birth': {'type': 'date', 'description': 'Date of birth of co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.date_of_birth.value'}, 'gender': {'type': 'enum', 'description': 'Gender of co-insured one', 'is_required': False, 'value': None, 'enum': ['Male', 'Female', 'Other'], 'json_path': 'questionaire_repo.value.co_insured.value[0].value.gender.value'}, 'relationship': {'type': 'enum', 'description': 'Relationship to the policyholder of co-insured one', 'is_required': False, 'value': None, 'enum': ['Spouse', 'Child', 'Parent', 'Other'], 'json_path': 'questionaire_repo.value.co_insured.value[0].value.relationship.value'}, 'marital_status': {'type': 'enum', 'description': 'Marital status of co-insured one', 'is_required': False, 'value': None, 'enum': ['Single', 'Married', 'Divorced', 'Widowed', 'Domestic Partner'], 'json_path': 'questionaire_repo.value.co_insured.value[0].value.marital_status.value'}, 'occupation': {'type': 'string', 'description': 'Occupation of co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.occupation.value'}, 'education': {'type': 'enum', 'description': 'Education level of co-insured one', 'is_required': False, 'value': None, 'enum': ['High School', 'Some College', 'Associates Degree', 'Bachelors', 'Masters', 'PhD'], 'json_path': 'questionaire_repo.value.co_insured.value[0].value.education.value'}, 'license_status': {'type': 'enum', 'description': 'License status of co-insured one', 'is_required': False, 'value': None, 'enum': ['Valid', 'Suspended', 'Expired'], 'json_path': 'questionaire_repo.value.co_insured.value[0].value.license_status.value'}, 'licensed_state': {'type': 'string', 'description': 'State where the co-insured one is licensed', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.licensed_state.value'}, 'license_number': {'type': 'string', 'description': "Co-insured one's license number (min. 8 chars)", 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.license_number.value'}, 'licensed_age': {'type': 'integer', 'description': 'Age when the co-insured one was licensed', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.licensed_age.value'}, 'rated': {'type': 'boolean', 'description': 'Whether the co-insured one is rated', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.rated.value'}, 'sr22_required': {'type': 'boolean', 'description': 'Whether an SR‑22 is required of co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.sr22_required.value'}, 'drive_for_rideshare': {'type': 'boolean', 'description': 'Whether the co-insured one uses rideshare services', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.drive_for_rideshare.value'}, 'drive_for_delivery': {'type': 'boolean', 'description': 'Whether the co-insured one uses delivery services', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.drive_for_delivery.value'}, 'driver_discounts': {'type': 'string', 'description': 'Any discounts applicable to the co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.driver_discounts.value'}, 'good_student_discount': {'type': 'boolean', 'description': 'Good student discount eligibility to co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.good_student_discount.value'}, 'mature_driver_discount': {'type': 'boolean', 'description': 'Mature driver discount eligibility to co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.mature_driver_discount.value'}, 'safe_driver_discount': {'type': 'boolean', 'description': 'Safe driver discount eligibility to co-insured one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.co_insured.value[0].value.safe_driver_discount.value'}}, 'json_path': 'questionaire_repo.value.co_insured.value[0].value'}
    detached_structure_list = {'type': 'object', 'description': 'Detached structures details', 'is_required': False, 'value': {'detached_structure_type': {'type': 'object', 'description': 'Detached structure one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.property_details.value.detached_structure_types.value[0].value.detached_structure_type.value'}}, 'json_path': 'questionaire_repo.value.property_details.value.detached_structure_types.value[0].value'}
    animals_list ={'type': 'object', 'description': 'Animal one', 'is_required': False, 'value': {'animal_type': {'type': 'object', 'description': 'Animal one', 'is_required': False, 'value': None, 'json_path': 'questionaire_repo.value.risk_details.value.animals.value[0].value.animal_type.value'}}, 'json_path': 'questionaire_repo.value.risk_details.value.animals.value[0].value'}

    list_type_mapping = {
        "detached_structure_types":detached_structure_list,
        "co_insured":co_insured_list,
        "animals":animals_list,
    }
    
    cur = data
    for t in list_path:
        cur = cur[t]
    lst = cur  # this is the list itself
    for key,value in list_type_mapping.items():
        if key in list_path:
            available_template = value
    template = lst[0] if lst else available_template
    if new_count < 1:
        lst.clear()
        return
    if template is None:
        raise ValueError("Cannot resize empty list without a template")

    # Grow
    while len(lst) < new_count:
        idx = len(lst)  # 1 for second item
        new = copy.deepcopy(template)
        _clear_values(new)
        old_ord = ORDINALS[1]            # template is always "one"
        new_ord = ORDINALS.get(idx+1, str(idx+1))
        _replace_ordinal_in_descriptions(new, old_ord, new_ord)
        lst.append(new)
    # Shrink
    if len(lst) > new_count:
        del lst[new_count:]

def normalize_questionnaire(q_repo: dict) -> dict:
    try:
      """
      1) Finds any description ending in an English ordinal word
        (one, two, three, …) and replaces that with the ordinal
        matching its JSON-path index + 1.
      2) Updates number_of_drivers, number_of_co_insured, number_of_vehicles
        to match list lengths (if they were not originally None).
      """
      # helper: replace trailing ordinal with the correct one
      def fix_description(desc: str, correct_idx: int) -> str:
          # regex: last word if it's an ordinal
          return re.sub(
              r"\b(" + "|".join(ORDINALS.values()) + r")\b$",
              ORDINALS.get(correct_idx, r"\1"),
              desc,
              flags=re.IGNORECASE
          )

      def _recurse_and_fix(node, correct_idx: int):
          if isinstance(node, dict):
              for k, v in node.items():
                  if k == "description" and isinstance(v, str):
                      node[k] = fix_description(v, correct_idx)
                  else:
                      _recurse_and_fix(v, correct_idx)
          elif isinstance(node, list):
              for elt in node:
                  _recurse_and_fix(elt, correct_idx)

      # the three lists we care about
      groups = ["detached_structure_types", "co_insured", "animals"]

      for field in groups:
          items = q_repo["value"].get(field, {}).get("value") or []
          for elem in items:
              # pull the first [n] we find in its json_path
              jp = elem.get("json_path", "")
              m = re.search(r"\[(\d+)\]", jp)
              if not m:
                  continue
              zero_idx = int(m.group(1))
              one_idx = zero_idx + 1
              # walk that element and fix any description
              _recurse_and_fix(elem, one_idx)

      # now update the counts
      count_fields = {
          "number_detached_structures":    len(q_repo["value"].get("property_details", {}).get("value", {}).get("detached_structure_types", {}).get("value", [])),
          "number_of_co_insured": len(q_repo["value"].get("co_insured",    {}).get("value", [])),
          "number_of_animals    ":   len(q_repo["value"].get("risk_details", {}).get("value", {}).get("animals", {}).get("value", []))
      }
      for cf, new_val in count_fields.items():
          node = q_repo["value"].get(cf)
          if node and node.get("value") is not None:
              node["value"] = new_val

      return
    except Exception as e:
        print(f"Error in normalize_questionnaire: {e}")
        return 

def fill_form_temp(json_path: str, json_data: dict) -> None:
    """Fill form with temporary data from top until reaching specified json_path"""
    log_to_file(f"Filling form with temporary data from top until reaching {json_path}")
    
    def _fill_temp_value(node: dict):
        """Fill a single node with temporary value if it's empty"""
        if node.get("value") is not None:
            return False  # Already filled
            
        node_type = node.get("type")
        if node_type == "string":
            node["value"] = "sample_text"
        elif node_type == "integer":
            node["value"] = 1
        elif node_type == "boolean":
            node["value"] = True
        elif node_type == "date":
            node["value"] = "01-01-2000"
        elif node_type == "enum":
            enum_options = node.get("enum", [])
            if enum_options:
                node["value"] = enum_options[0]
            else:
                node["value"] = "option1"
        
        if node_type in ["string", "integer", "boolean", "date", "enum"]:
            log_to_file(f"Filled field at path: {node.get('json_path', 'unknown')} with type: {node_type}")
            return True  # Successfully filled
        
        return False

    def _traverse_and_fill_until_target(node: dict) -> bool:
        """Recursively traverse and fill nodes until target path is reached. Returns True if target found."""
        if not isinstance(node, dict):
            return False
            
        # Check if this node has the target json_path
        node_json_path = node.get("json_path", "")
        if node_json_path == json_path:
            # Found our target! Fill this field and stop
            _fill_temp_value(node)
            log_to_file(f"Reached target path: {json_path}")
            return True
        
        # If this is a fillable field (has json_path and is primitive), fill it
        if node_json_path and node.get("type") in ["string", "integer", "boolean", "date", "enum"]:
            _fill_temp_value(node)
        
        # Traverse into nested structures
        node_type = node.get("type")
        
        if node_type == "object" and "value" in node and isinstance(node["value"], dict):
            # Traverse object fields in order
            for key, child_node in node["value"].items():
                if _traverse_and_fill_until_target(child_node):
                    return True  # Target found, stop traversal
                    
        elif node_type == "list" and "value" in node and isinstance(node["value"], list):
            # Traverse list items in order
            for item in node["value"]:
                if isinstance(item, dict):
                    if _traverse_and_fill_until_target(item):
                        return True  # Target found, stop traversal
        
        # Also check any other nested dictionaries
        for key, value in node.items():
            if key != "value" and isinstance(value, dict):
                if _traverse_and_fill_until_target(value):
                    return True
            elif key == "value":
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict):
                            if _traverse_and_fill_until_target(sub_value):
                                return True
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            if _traverse_and_fill_until_target(item):
                                return True
        
        return False  # Target not found in this branch

    # Start traversal from the root of the form
    # We need to traverse the top-level sections in order
    for section_name, section_data in json_data.items():
        if _traverse_and_fill_until_target(section_data):
            break  # Target found, stop processing
    
    log_to_file(f"Completed filling form with temporary data until: {json_path}")
    return


@function_tool(strict_mode=False)
async def update_field(form: RunContextWrapper[Form], path: str, operation: str, value: Any = None) -> bool:
    """This field will update the given field with given value"""
    log_to_file(f"updating field with: {path} {operation} {value}")
    print(f"updating field with: {path} {operation} {value}")
    tokens = _parse_tokens(path)
    cur = form.context.data
    try:
        # Walk down to parent of final token
        for i, token in enumerate(tokens[:-1]):
            cur = cur[token]
        final = tokens[-1]

        # === perform the base update/add/delete ===
        if operation == "update":
            if cur["type"] == 'object':
                return {"message":"cannot change value of type object"}
            if isinstance(final, int):
                cur[final] = value
            else:
                cur[final] = value

        elif operation == "add":
            if isinstance(cur[final], list):
                cur[final].append(value)
            elif isinstance(cur, dict) and "value" in cur[final] and isinstance(cur[final]["value"], list):
                cur[final]["value"].append(value)

        elif operation == "delete":
            if isinstance(cur[final], list):
                cur[final].pop(value)
            elif isinstance(cur, dict) and "value" in cur[final] and isinstance(cur[final]["value"], list):
                cur[final]["value"].pop(value)

        # === hook into special fields ===
        json_path = ".".join(
            tok if isinstance(tok, str) else f"[{tok}]"
            for tok in tokens
        )

        # number_of_detached → resize detached_details list
        if json_path.endswith("questionaire_repo.value.number_of_detached.value"):
            count = int(value or 0)
            resize_list_with_ordinal(
                form.context.data,
                ["questionaire_repo", "value", "detached_details", "value"],
                count
            )
            update_assigned_driver_enums(form.context.data)

        elif json_path.endswith("questionaire_repo.value.number_of_animals.value"):
            count = int(value or 0)
            resize_list_with_ordinal(
                form.context.data,
                ["questionaire_repo", "value", "animal_details", "value"],
                count
            )
            update_assigned_driver_enums(form.context.data)

        elif json_path.endswith("questionaire_repo.value.number_of_co_insured.value"):
            count = int(value or 0)
            resize_list_with_ordinal(
                form.context.data,
                ["questionaire_repo", "value", "co_insured", "value"],
                count
            )
            current_drivers = len(form.context.data["questionaire_repo"]["value"]["driver_details"]["value"])
            count = count + current_drivers
            if current_drivers < count:
                resize_list_with_ordinal(
                    form.context.data,
                    ["questionaire_repo", "value", "driver_details", "value"],
                    count
                )
            update_assigned_driver_enums(form.context.data)


        elif "driver_details.value[" in json_path and json_path.endswith(".first_name.value") \
             or json_path.endswith(".middle_name.value") \
             or json_path.endswith(".last_name.value"):
            update_assigned_driver_enums(form.context.data)

        # Clear related policy fields when current_carrier is set to empty string
        elif json_path == "questionaire_repo.value.policy_details.value.current_carrier.value" and (value == ' ' or value == '' or value == None or value == " " or value == 0):
            # List of related policy fields to clear
            related_policy_paths = [
                "questionaire_repo.value.policy_details.value.current_carrier_premium.value",
                "questionaire_repo.value.policy_details.value.years_with_prior_carrier.value", 
                "questionaire_repo.value.policy_details.value.prior_insurance_liability_limit.value",
                "questionaire_repo.value.policy_details.value.policy_term_length.value",
                "questionaire_repo.value.policy_details.value.payment_frequency.value"
            ]
            
            # Clear each related field
            for related_path in related_policy_paths:
                try:
                    related_tokens = _parse_tokens(related_path)
                    related_cur = form.context.data
                    for token in related_tokens[:-1]:
                        related_cur = related_cur[token]
                    related_final = related_tokens[-1]
                    related_cur[related_final] = ' '
                    log_to_file(f"Cleared related policy field: {related_path}")
                except Exception as e:
                    log_to_file(f"Error clearing related policy field {related_path}: {str(e)}")

        # Sync co-insured relationship and marital status
        elif "questionaire_repo.value.co_insured.value.[" in json_path and json_path.endswith(".relationship.value"):
            # When relationship is set to "Spouse", auto-set marital_status to "Married" (case insensitive)
            if value and str(value).lower() == "spouse":
                try:
                    # Extract the co-insured index from the path
                    index = json_path.split('[')[1].split(']')[0]
                    if index is not None:
                        marital_status_path = f"questionaire_repo.value.co_insured.value[{index}].value.marital_status.value"
                        # Update marital status to "Married"
                        marital_tokens = _parse_tokens(marital_status_path)
                        marital_cur = form.context.data
                        for token in marital_tokens[:-1]:
                            marital_cur = marital_cur[token]
                        marital_final = marital_tokens[-1]
                        marital_cur[marital_final] = "Married"
                        log_to_file(f"Auto-updated marital status to 'Married' for co-insured {index} when relationship set to '{value}'")
                except Exception as e:
                    log_to_file(f"Error auto-updating marital status for co-insured: {str(e)}")
        
        # Handle additional_co_insured boolean field  
        elif json_path.endswith("questionaire_repo.value.additional_co_insured.value"):
            try:
                if value is False:
                    # Add one more co-insured but don't store the false value
                    current_co_insured = form.context.data["questionaire_repo"]["value"]["number_of_co_insured"]["value"] or 0
                    new_co_insured_count = current_co_insured + 1
                    
                    # Update number_of_co_insured
                    form.context.data["questionaire_repo"]["value"]["number_of_co_insured"]["value"] = new_co_insured_count
                    
                    # Resize co-insured list
                    resize_list_with_ordinal(
                        form.context.data,
                        ["questionaire_repo", "value", "co_insured", "value"],
                        new_co_insured_count
                    )
                
                    current_detached = len(form.context.data["questionaire_repo"]["value"]["detached_details"]["value"])
                    required_detached = current_detached + 1
                    if current_detached < required_detached:
                        resize_list_with_ordinal(
                            form.context.data,
                            ["questionaire_repo", "value", "detached_details", "value"],
                            required_detached
                        )
                        form.context.data["questionaire_repo"]["value"]["number_of_detached"]["value"] = required_detached
                    
                    # Keep additional_co_insured as None (don't store false)
                    form.context.data["questionaire_repo"]["value"]["additional_co_insured"]["value"] = None
                    
                    update_assigned_driver_enums(form.context.data)
                    log_to_file(f"Added one more co-insured (total: {new_co_insured_count}) - additional_co_insured kept as None")
                    
                elif value is True:
                    # Set additional_co_insured to true (no more co-insured wanted)
                    form.context.data["questionaire_repo"]["value"]["additional_co_insured"]["value"] = True
                    log_to_file("Set additional_co_insured to True - no more co-insured will be added")
                    
            except Exception as e:
                log_to_file(f"Error handling additional_co_insured: {str(e)}")

        # Handle additional_vehicles boolean field
        elif json_path.endswith("questionaire_repo.value.additional_vehicles.value"):
            try:
                if value is False:
                    # Add one more vehicle but don't store the false value
                    current_vehicles = form.context.data["questionaire_repo"]["value"]["number_of_vehicles"]["value"] or 0
                    new_vehicle_count = current_vehicles + 1
                    
                    # Update number_of_vehicles
                    form.context.data["questionaire_repo"]["value"]["number_of_vehicles"]["value"] = new_vehicle_count
                    
                    # Resize vehicle list
                    resize_list_with_ordinal(
                        form.context.data,
                        ["questionaire_repo", "value", "vehicle_details", "value"],
                        new_vehicle_count
                    )
                    
                    # Keep additional_vehicles as None (don't store false)
                    form.context.data["questionaire_repo"]["value"]["additional_vehicles"]["value"] = None
                    
                    update_assigned_driver_enums(form.context.data)
                    log_to_file(f"Added one more vehicle (total: {new_vehicle_count}) - additional_vehicles kept as None")
                    
                elif value is True:
                    # Set additional_vehicles to true (no more vehicles wanted)
                    form.context.data["questionaire_repo"]["value"]["additional_vehicles"]["value"] = True
                    log_to_file("Set additional_vehicles to True - no more vehicles will be added")
                    
            except Exception as e:
                log_to_file(f"Error handling additional_vehicles: {str(e)}")

        elif "lead_repo.value.marital_status.value" in json_path:
            if value.lower() == "single":
                form.context.data["questionaire_repo"]["value"]["co_insured"]["value"][0]["value"]["relationship"]["enums"].pop("Spouse")

        # Handle additional_detached_structures boolean field
        elif json_path.endswith("questionaire_repo.value.additional_detached_structures.value"):
            try:
                if value is False:
                    # Add one more detached structure but don't store the false value
                    current_detached = form.context.data["questionaire_repo"]["value"]["number_of_detached"]["value"] or 1
                    new_detached_count = current_detached + 1
                    
                    # Update number_of_detached
                    form.context.data["questionaire_repo"]["value"]["number_of_detached"]["value"] = new_detached_count
                    
                    # Resize detached list
                    resize_list_with_ordinal(
                        form.context.data,
                        ["questionaire_repo", "value", "detached_details", "value"],
                        new_detached_count
                    )
                    
                    # Keep additional_detached_structures as None (don't store false)
                    form.context.data["questionaire_repo"]["value"]["additional_detached_structures"]["value"] = None
                    
                    update_assigned_driver_enums(form.context.data)
                    log_to_file(f"Added one more detached structure (total: {new_detached_count}) - additional_detached_structures kept as None")
                    
                elif value is True:
                    # Set additional_detached_structures to true (no more detached structures wanted)
                    form.context.data["questionaire_repo"]["value"]["additional_detached_structures"]["value"] = True
                    log_to_file("Set additional_detached_structures to True - no more detached structures will be added")
                    
            except Exception as e:
                log_to_file(f"Error handling additional_detached_structures: {str(e)}")

        # Handle additional_animals boolean field
        elif json_path.endswith("questionaire_repo.value.additional_animals.value"):
            try:
                if value is False:
                    # Add one more animal but don't store the false value
                    current_animals = form.context.data["questionaire_repo"]["value"]["number_of_animals"]["value"] or 0
                    new_animal_count = current_animals + 1
                    
                    # Update number_of_animals
                    form.context.data["questionaire_repo"]["value"]["number_of_animals"]["value"] = new_animal_count
                    
                    # Resize animal list
                    resize_list_with_ordinal(
                        form.context.data,
                        ["questionaire_repo", "value", "animal_details", "value"],
                        new_animal_count
                    )
                    
                    # Keep additional_animals as None (don't store false)
                    form.context.data["questionaire_repo"]["value"]["additional_animals"]["value"] = None
                    
                    update_assigned_driver_enums(form.context.data)
                    log_to_file(f"Added one more animal (total: {new_animal_count}) - additional_animals kept as None")
                    
                elif value is True:
                    # Set additional_animals to true (no more animals wanted)
                    form.context.data["questionaire_repo"]["value"]["additional_animals"]["value"] = True
                    log_to_file("Set additional_animals to True - no more animals will be added")
                    
            except Exception as e:
                log_to_file(f"Error handling additional_animals: {str(e)}")

    except Exception as e:
        log_to_file(f"error in multiplying fields: {path} {str(e)}")
        return False

    finally:
      try:
        # print(db_form_conversion(form.context.data,{"lead_repo":form.context.lead_repo,"questionaire_repo":form.context.questionaire_repo},field_mapping,get_form=False))
        normalise(form.context.data)
        normalize_questionnaire(form.context.data["questionaire_repo"])
        log_to_file(f"json file:{form.context.data}")
        log_to_file(f"next_field: {next_field(form.context.data)}")
        if next_field(form.context.data) is None:
          return "form is completed"
        else:
          return {"next_field":next_field(form.context.data)}
      except Exception as e:
        log_to_file(f"error in updating fields: {path} {str(e)}")
        return False

INPUT_TOKEN_PRICE = 0.40  
CACHED_TOKEN_PRICE = 0.10  
OUTPUT_TOKEN_PRICE = 1.60  

def calculate_costs(input_tokens, cached_tokens, output_tokens):
    """Calculate costs for different token types"""
    input_cost = (input_tokens / 1_000_000) * INPUT_TOKEN_PRICE
    cached_cost = (cached_tokens / 1_000_000) * CACHED_TOKEN_PRICE
    output_cost = (output_tokens / 1_000_000) * OUTPUT_TOKEN_PRICE
    total_cost = input_cost + cached_cost + output_cost
    
    return {
        'input_cost': input_cost,
        'cached_cost': cached_cost, 
        'output_cost': output_cost,
        'total_cost': total_cost
    }

@function_tool(strict_mode=False)
async def get_field(form: RunContextWrapper[Form],field_description : str):
  print("get_field called with field_description: ",field_description)
  """this fucntion returns fields based in given description"""
  ctx= next_field(form.context.data)
  log_to_file(f"field_description: {field_description}")
  try:
    desc_path_mapping = extract_description_to_path(form.context.data)
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    you will be given a mapping of description and relative paths and a search field_description and context field
    your task is to analyze the search field_description and mapping and return the value that matches most closely to the search field_description in mapping
    the path should be close the the path of the context field ( for example description is 'date of birth' and context is field of driver one then return path of dob of driver one)
    value should be close to both description and context field.
    Strictly the output should be in this format
    {{
      found : true/false,
      path : path will be here
    }}
    if you dont find any close matches return false in found
    """

    response = await client.chat.completions.create(
                  messages=[
                      {
                          "role": "system",
                          "content": "You are a helpful assistant designed to output JSON.",
                      },
                      {
                          "role": "user",
                          "content": f"{prompt},search description - {field_description}, mapping - {desc_path_mapping}, context - {ctx}",
                      },
                  ],
                  model = 'gpt-4.1-mini',
                  max_tokens=16384,
                  response_format={"type": "json_object"},
              )

    response = response.to_dict()
    prompt_tokens = response["usage"]["prompt_tokens"]
    completion_tokens = response["usage"]["completion_tokens"]
    cached_tokens = response["usage"].get("prompt_tokens_details", {}).get("cached_tokens", 0)
    
    # Calculate actual input tokens (total input - cached)
    actual_input_tokens = prompt_tokens - cached_tokens
    
    form.context.input_tokens += int(actual_input_tokens)
    form.context.output_tokens += int(completion_tokens)
    form.context.cached_tokens += int(cached_tokens)
        
    response = json.loads(response["choices"][0]["message"]["content"])
    print("get_field response: ",response)
    if response["found"]:
      print("get_field response: ",find_object_by_json_path(form.context.data,response["path"]))
      log_to_file(f"get_field response: {find_object_by_json_path(form.context.data,response['path'])}")
      return find_object_by_json_path(form.context.data,response["path"])
    else :
      return None
  except Exception as e:
      log_to_file(str(e))

def get_today_date():
  """Returns today's date in dd-mm-yyyy format"""
  return str(datetime.now().strftime("%d-%m-%Y"))

def validate_date(language_processor_response,data):
    if language_processor_response.get("command_type") == "update":
        for field, value in language_processor_response.get("fields").items():
          if 'date' in field.lower():
              if 'effective' in field.lower():
                  try:
                      value_date = datetime.strptime(value, "%d-%m-%Y")
                      today_date = datetime.strptime(get_today_date(), "%d-%m-%Y")
                      if value_date < today_date:
                          return {"command_type":"reply_to_user","message":"Can you please provide date again? Effective date cannot be in past"}
                  except Exception as e:
                      log_to_file(f"error in validate_date: {str(e)}")
                      return {"command_type":"reply_to_user","message":"Please provide date again."}
              elif 'dob' in field.lower():
                  try:
                      value_date = datetime.strptime(value, "%d-%m-%Y") 
                      today_date = datetime.strptime(get_today_date(), "%d-%m-%Y")
                      if value_date > today_date:
                          return {"command_type":"reply_to_user","message":"Can you please provide date again? Date of birth cannot be in the future"}
                  except Exception as e:
                      log_to_file(f"error in validate_date: {str(e)}")
                      return {"command_type":"reply_to_user","message":"Please provide date again."}
          elif 'Years at address' in field.lower():
              try:
                  form_data = data.data
                  log_to_file(f"form_data: {form_data}")
                  birth_date = form_data['lead_repo']['value']['date_of_birth']['value']
                  birth_date = datetime.strptime(birth_date, "%d-%m-%Y")
                  today_date = datetime.strptime(get_today_date(), "%d-%m-%Y")
                  age = today_date.year - birth_date.year - ((today_date.month, today_date.day) < (birth_date.month, birth_date.day))

                  if int(value) > age:
                      return {"command_type":"reply_to_user","message":"Can you please years at current address? It should be less than or equal to your age"}
              except Exception as e:
                  log_to_file(f"error in validate_date: {str(e)}")
                  return {"command_type":"reply_to_user","message":"Please provide Years at current address again."}
          elif 'age' in field.lower() and 'licensed' in field.lower():
              try:
                  if int(value) < 15:
                      return {"command_type":"reply_to_user","message":"Can you please provide age again? Age when licensed cannot be less than 15"}
              except Exception as e:
                  log_to_file(f"error in validate_date: {str(e)}")
                  return {"command_type":"reply_to_user","message":"Please provide Age when licensed again."}

    return language_processor_response

async def language_processor(data, message):
    try:
      print("language_processor called with message: ", message)
      log_to_file(f"language_processor called with message: {message}")
      descriptions = extract_descriptions(data.data)
      nf = next_field(data.data)
      history = data.history
      
      prompt = f"""
      you are a language processor for an agent
      you have access to
      chat_history - chat history between user and agent
      user_response - user's response to agent
      next_field - next field that is asked to user
      descriptions - descriptions of all fields in form

      you task is to analyze user_response and understand the user's intent and based on that catagorize it into one of the following catagories:
      catagory 1 : update
      catagory 2 : delete
      catagory 3 : find
      catagory 4 : message

      you need to figure out what needs to be updated, deleted, found or message based on data you are given.

      eg: if user response is 'my name is john doe' your response should be {{"command_type": "update","fields":{{ "First name of the insured": "john","Middle name of the insured":"","Last name of the insured":"doe"}}}} 
      or if user response is 'new colony udaipur rajasthan 313001' your response should be {{"command_type": "find","fields":{{ "Primary street address":"new colony","City of residence":"udaipur","State of residence":"rajasthan","ZIP or postal code":"313001"}}}}
      or if user response is 'delete driver where name is john' your response should be {{"command_type": "delete","fields":{{ "List of driver profiles": "delete where driver name in john"}}}} 
      or if user response is 'what is driver one's name' your response should be {{"command_type": "find","fields":{{ "field_description": "Driver one's name"}}}} 
      if user response does not contain any information about next_field then return {{"command_type": "message","message":"message from user"}}

      if user asks for 'add another [co-insured, driver, vehicle]' then return {{"command_type": "update","fields":{{ "number_of_[co-insured, driver, vehicle]": "add another"}}}}
      "number_of_[co-insured, driver, vehicle]" can be '0'

      if user ask to skip or leave a field blank that where 'is_required' is true return {{"command_type":"reply_to_user","message":"message saying that field is required please provide the information with a friendly tone"}} message should be in a friendly tone.
      also if user provide invalid information for a field like negative numbers,invalid format for email or wrong input for enum or any other invalid information then return {{"command_type":"reply_to_user","message":"message saying that field is required please provide the information with a friendly tone"}} message should be in a friendly tone.
      if user says 'dont have' or similar and is_required is false then return fields as empty string.
      if user says 'dont want to add more [co-insured, driver, vehicle]' or ' remove last [co-insured, driver, vehicle]' then return {{"command_type":"update","fields":{{"List of [co-insured, driver, vehicle]": 'remove last'}}}}

      if user says 'same as before : value' or 'same as this field : value' or 'same as previous field : value' then return {{"command_type":"update","fields":{{"field_description from next_field":"value from user"}}}} do not pass 'same as before' or 'same as this field' or 'same as previous field' text in value. 
      if user provide information that is not in next_field then catagorize and make fields based on descriptions.
      for field 'Skip more [co-insured, driver, vehicle]?' with 'yes' then return {{"command_type":"update","fields":{{"Skip more [co-insured, driver, vehicle]?":"false"}}}} else return {{"command_type":"update","fields":{{"Skip more [co-insured, driver, vehicle]?":"true"}}}}
      field name should be strictly from descriptions.

      if user response is not in descriptions then return {{"command_type": "message","message":"message from user"}}

      if user asks for any information put that in find catagory.
      
      your response should strictly be in json

      all dates should be in this format dd-mm-yyyy

      think for longer while analyzing user_response and understand the user's intent.

      chat_history : {history} 
      user_response : {message}
      next_field: {nf}
      descriptions: {descriptions}
      """
      client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

      response = await client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant designed to output JSON.",
                        },
                        {
                            "role": "user",
                            "content": f"{prompt}",
                        },
                    ],
                    model = 'gpt-4.1-mini',
                    max_tokens=16384,
                    response_format={"type": "json_object"},
                )

      response = response.to_dict()
      prompt_tokens = response["usage"]["prompt_tokens"]
      completion_tokens = response["usage"]["completion_tokens"]
      cached_tokens = response["usage"].get("prompt_tokens_details", {}).get("cached_tokens", 0)
      
      # Calculate actual input tokens (total input - cached)
      actual_input_tokens = prompt_tokens - cached_tokens
      
      data.input_tokens += int(actual_input_tokens)
      data.output_tokens += int(completion_tokens)
      data.cached_tokens += int(cached_tokens)
      
      
      response = json.loads(response["choices"][0]["message"]["content"])
      if response['command_type'] == 'reply_to_user':
          data.history.append({"role":"assistant","content":response['message']})
      data.language_processor_response.append(response)
      data.language_processor_response = data.language_processor_response[-5:]
      history.append({"role":"user","content":message})
      data.history = history[-5:]
      log_to_file(f"language processor response: {response}")
      return response
    except Exception as e:
      log_to_file(f"error in language processor: {e}")
      return {"command_type": "message","message":"message from user"}


async def json_agent(data,message):
  log_to_file(f"json_agent called with message: {message}")
  print(f"json_agent called with message: {message}")
  ctx = next_field(data.data)
  log_to_file(f"ctx: {ctx}")
  INSTRUCTIONS = f"""
  you are a assistant that will be used to fill the fields in the form.
  You have access to:

  {ctx} : next_field that needs to be filled

  {message}: command from user

  there are three catagories in command
  catagory 1 : update
  catagory 2 : delete
  catagory 3 : find
  catagory 4 : message
  Your Responsibilities:  

    0. if command catagory is find then use get_field to get details of fields provided and return the fields details in reply_message.

    1. analyze the user's command and put it in one of two catagories - a) Path is available for the information given or asked in next_field. or b) No path is available for the information given or asked in next_field.

      1.1 strictly if No information is given in user's command then Ask user for all next_field's details in next_field at the same time
      1.2 strictly if user command with information based on previous/other information (e.g. same as before, use previos address etc...) put that in b catagory call get_field of the requied information then update current

    2.1 if it falls in category b then :
    get_field
    • field_description: a clear and brief description of what the user provided
      (e.g., "email address", "vehicle registration number", "employer name")
    → Use the returned path from get_field to immediately call update_field and store the data.

    2.2 if it falls in category a then strictly call:
    update_field
    • path: the known JSON path
    • action: "update" (or "add"/"delete" if modifying a list)
    • new_value: the parsed value from the user's response ( all dates should be in this format dd-mm-yyyy) (when deleting list item strictly provide index of the list as value to delete)
    → if successful this will return the next field that needs to be asked to user strictly.
    if update_field returns false in updating field then strictly call get_field with discription of fields needs to be updated and use that path instead and call update_field again

    if you get delete command then
    1. get the list of fields using get_field
    2. get the index of the field by analyzing the command and the list of fields from get_field
    3. call update_field with path and action as delete and value as index of the field to delete
    4. if successful this will return the next field that needs to be asked to user strictly.
    strictly do not delete any field that is not in command.

    strictly do not update values where type is 'object' you can only update childrens value of that object

    if command is asked to delete a field that is not in json then dont return message saying field not found do not delete unneccesary fields.
    if user ask 'same as before' or 'same as this field' or 'same as previous field' then strictly get path and value using get_field and update_field with that path and value.

    3.Data integrity rules:

    Required fields must never be updated with empty strings. If the user skips a required field, politely ask again.
    Optional fields can be set as "" if the user does not provide an answer.

    4. Do not assume or store anything in memory temporarily.

    strictly do not update any field if its path is unknown or missing get it using get_field.
    strictly do not store data in memory—only persist it using update_field and get_field.


  response should be in this json format:
  {{
    reply_message:string (eg "name is updated as john k doe"),
  }}

 """
  


  agent = Agent[Form](
      name="Assistant",
      model = "gpt-4.1-mini",
      instructions=INSTRUCTIONS.strip(),
      tools=[update_field,get_field],
  )
  retries = 3
  last_error = None
  
  for attempt in range(retries):
      try:
          result = await Runner.run(agent, str(message), context=data, max_turns=30)
          input_tokens_sum = sum(r.usage.input_tokens for r in result.raw_responses)
          output_tokens_sum = sum(r.usage.output_tokens for r in result.raw_responses)
          cached_tokens_sum = sum(r.usage.input_tokens_details.cached_tokens for r in result.raw_responses)
          
          # Calculate actual input tokens (total input - cached)  
          actual_input_tokens_sum = input_tokens_sum - cached_tokens_sum
          
          data.input_tokens += int(actual_input_tokens_sum)
          data.output_tokens += int(output_tokens_sum)
          data.cached_tokens += int(cached_tokens_sum)
          
          break
      except Exception as e:
          last_error = e
          log_to_file(f"error in json_agent attempt {attempt + 1}: {str(e)}")
          if attempt == retries - 1:
              return {"reply_message": f"error in json_agent after {retries} attempts: {str(last_error)}"}
          continue
  response = result.final_output
  response = json.loads(response)
  log_to_file(f"response: {response}")
  return response

async def validation_agent(data):
  print("validation_agent called")
  language_processor_response = data.language_processor_response[-1]
  filled_fields = str(extract_non_null_values(data.data)).strip()
  log_to_file(f"filled_fields in validation_agent: {filled_fields}")
  prompt = f"""
  You are a validation agent that validate if form is filled correctly. 

  You receive two inputs:

    1. command: command from user

    2.filled_fields: a mapping of field names to values already filled in the form ( this does not include all fields from filled_fields so dont get confused and dont ask to delete unneccesary fields)

    you need to analyze the command and understand the user's intent and then look in filled_fields if the data is filled correctly.
    closely analyze the command and its meaning and then analyze the filled_fields accordingly.
    any data that is in command and not in filled_fields should be filled.
    carefully analyze when comparing values and understand the meaning of the values.
    strictly make update commands for the fields that are in command but not in filled_fields, command with the values provided in command or from filled_fields.

    strictly ignore all the format and datatype mismatches if the values's meaning are same like ( yes == true, '1' == 1 or '1' == 1.0 or 31/05/2003 == 31-05-2003).

    if command field is to 'Do not add more co-insured/driver/vehicle' then skip validation and return empty list.
    if command field is to 'remove last co-insured/driver/vehicle' skip validation.

    if command is 'no prior claim' or 'no address' or 'dont have' or similar then value should be empty string instead of text like 'no prior claim' or 'no address'.

    if the command is to delete a field that is not in filled_fields then dont return any command.

    if not then return a list of commands to fix them.

    If there are no commands to generate, return an empty list.

    Output exactly as JSON with one key "commands" whose value is an array of strings, for example:
    {{
    "commands": [list of commands to fix the form]
    }}
    example: [    
    "Incorrect value for dob: expected 31/05/2003, found 30/05/2003",
    "Copy insured address : {{value}} - into mailing address field",
    ]
 
    think for longer while analyzing the command and intent behind each command.
  """

  client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

  response = await client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant designed to output JSON.",
                    },
                    {
                        "role": "user",
                        "content": f"{prompt},command: {language_processor_response},filled_fields: {filled_fields}",
                    },
                ],
                model = 'gpt-4.1-mini',
                max_tokens=16384,
                response_format={"type": "json_object"},
            )

  response = response.to_dict()
  prompt_tokens = response["usage"]["prompt_tokens"]
  completion_tokens = response["usage"]["completion_tokens"]
  cached_tokens = response["usage"].get("prompt_tokens_details", {}).get("cached_tokens", 0)
  
  # Calculate actual input tokens (total input - cached)
  actual_input_tokens = prompt_tokens - cached_tokens
  
  data.input_tokens += int(actual_input_tokens)
  data.output_tokens += int(completion_tokens)
  data.cached_tokens += int(cached_tokens)
  
   
  response = json.loads(response["choices"][0]["message"]["content"])
  log_to_file(f"validation_agent response: {response}")
  return response

def get_suggestion_values(data,nxt):
    path = nxt['json_path']
    suggestion_values = []
    if 'questionaire_repo.value.vehicle_details.value[' in path and '].value.garaging_address.value' in path:
        insured_address = data.data['lead_repo']['value']['address_detail']['value']['insured_address']['value']
        suggestion_values.append(f"insured address: {insured_address}")
        mail_address = data.data['lead_repo']['value']['address_detail']['value']['mailing_address']['value']
        suggestion_values.append(f"mailing address: {mail_address}")
    return suggestion_values

async def reply_agent(data,message):
  try:
    log_to_file("reply_agent called")
    print("reply_agent called :",message)
    history = data.history
    log_to_file(f"history: {history}")
    filled_fields = str(extract_non_null_values(data.data)).strip()
    log_to_file(f"filled_fields: {filled_fields}")
    nxt = next_field(data.data)
    suggestion_values = get_suggestion_values(data,nxt)
    prompt = f"""
    You are 'Robert', a friendly and proffesional agent from Nationwide Insurance Agency.
    Your role is to assist users in completing their insurance information by analyzing the chat history and the current state of filled fields.

    Available Data:
    1. filled_fields: A dict containing already provided user information, e.g., {{"name of insured":"john"}}.
    2. history: A chronological list of messages exchanged between the user and you.
    3. next_field: next_field that needs to be filled.
    4. message: message from json_agent.

    Instructions:

    0. if user asks for any details and message from json_agent provide that details then return that in reply message.

    1.  analyze next_field:
      - Determine a list of the next required fields that needs to be collected from user and ask thos fields to user strictly all at once.
      - provide enums if any.

    2. If the required field closely matches any existing descriptions in filled_fields, suggest those values as options or suggest from your knowledge as suggestion_values to the user, can be blank as well.
      - you can suggest from your knowledge as well( like you can suggest state and zip code based on city or education based on occupation)
      - you can also look at the enums and suggest best enum value for the field based on already filled fields.

    3. When responding to the user:
      - Maintain a friendly and proffesional tone an help user to fill form.
      - Clearly specify the next piece of information required.
      - Provide suggested options (enums) if applicable.

    if you are asking for multiple fields at once then ask them in bullet points and only ask for fields from next_field.
    do not ask for fields that are not in next_field strictly.

    do not ask date in any structure.

    give suggestions as "same as previous field : value" or "same as this field : value" or "same as before : value" if same information is already filled in previous field for all fields combined in next_field.
    do not suggest same value two times and only one suggestion from multiple enums not all.  
    if you are providing suggestion for multiple fields provide that in a single suggestion.
    Response Format:
    {{
      message: string,         # The message content that will be sent to user should be in friendly tone.
      enums: list[string] or None,  # Suggested options for the user, if any.
      suggestion_values : list[string] or None, # suggestion for the user to fill the field.
    }}

    Note:
    - Ensure clarity and specificity in your messages.
    - Use delimiters or formatting to highlight key information when necessary.
    """

    if suggestion_values:
      prompt += f"\n\nSuggestion Values: {suggestion_values}"

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await client.chat.completions.create(
                  messages=[
                      {
                          "role": "system",
                          "content": "You are a helpful assistant designed to output JSON.",
                      },
                      {
                          "role": "user",
                          "content": f"{prompt},filled_fields: {filled_fields},history: {history},next_field: {nxt},message: {message}",
                      },
                  ],
                  model = 'gpt-4.1-mini',
                  max_tokens=16384,
                  response_format={"type": "json_object"},
              )

    response = response.to_dict()
    prompt_tokens = response["usage"]["prompt_tokens"]
    completion_tokens = response["usage"]["completion_tokens"]
    cached_tokens = response["usage"].get("prompt_tokens_details", {}).get("cached_tokens", 0)
    
    # Calculate actual input tokens (total input - cached)
    actual_input_tokens = prompt_tokens - cached_tokens
    
    data.input_tokens += int(actual_input_tokens)
    data.output_tokens += int(completion_tokens)
    data.cached_tokens += int(cached_tokens)
    
    costs = calculate_costs(actual_input_tokens, cached_tokens, completion_tokens)
    print(f"Input Tokens: {actual_input_tokens} - Cost: ${costs['input_cost']:.6f}")
    print(f"Cached Tokens: {cached_tokens} - Cost: ${costs['cached_cost']:.6f}")
    print(f"Output Tokens: {completion_tokens} - Cost: ${costs['output_cost']:.6f}")
    print(f"Total Cost: ${costs['total_cost']:.6f}")

    
    response = json.loads(response["choices"][0]["message"]["content"])
    data.history.append({"role":"assistant","content":f"message: {response['message']} - enums: {response['enums']} - suggestion_values: {response['suggestion_values']}"})
    log_to_file(f"reply_agent response: {response}")
    return response
  except Exception as e:
    log_to_file(f"error in reply_agent: {str(e)}")
    

async def chat_pipeline(data,message):
  processed_message = await language_processor(data,message)
  processed_message = validate_date(processed_message,data)
  if processed_message['command_type'] == 'reply_to_user':
    return processed_message['message']
  message = processed_message
  tries = 3
  while tries > 0:
    json_agent_response = await json_agent(data,message)
    if processed_message['command_type'] != 'find':
      validation_agent_response = await validation_agent(data)
      if validation_agent_response['commands'] == []:
        break
      else:
        message = "follow these commands" + str(validation_agent_response['commands'])
        tries -= 1
    else:
      break

  reply_agent_response = await reply_agent(data,json_agent_response)
  return reply_agent_response

lead_repo = {
    "_id": { "$oid": "684002e50d21f3a141d8a646" },
    "account_type": "Personal",
    "insurance_type": "Home",
    "chat_ids": [],
    "insured": {
      "first_name": "John",
      "middle_name": "A.",
      "last_name": "Doe"
    },
    "date_of_birth": { "$date": "1985-04-15T00:00:00.000Z" },
    "gender": "Male",
    "marital_status": "Single",
    "email": "yatinbadeja@gmail.com",
    "phone_number": {
      "country_code": "+1",
      "number": "5551234567"
    },
    "can_text": True,
    "contact_preference": "Phone",
    "occupation": "Software Engineer",
    "education": "High School",
    "social_security_number": "123456789",
    "address_detail": {
      "insured_address": {
        "street_address": "123 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62704"
      },
      "mailing_address": {
        "street_address": "456 Oak Ave",
        "city": "Springfield",
        "state": "IL",
        "zip_code": "62705"
      },
      "years_at_address": 5,
      "county": "Sangamon"
    },
    "send_questionnaire": False,
    "producer": {
      "$oid": "684001d40d21f3a141d8a641"
    },
    "customer_service_representative": None,
    "created_at": {
      "$date": "2025-06-04T08:25:09.598Z"
    },
    "updated_at": {
      "$date": "2025-06-06T08:27:41.108Z"
    },
    "deactivated": False,
    "status": "Contacted" 
  }


questionaire_repo = {
    "chat_id":None,
    "lead_id":None,
    "number_of_co_insured": None,
    "co_insured": [],
    "additional_co_insured": None,

    "policy_details": {
        "effective_date":None,
        "use":None,
        "policy_form":None,
        "protection_class":None,
        "prior_carrier":None,
        "prior_carrier_premium": None,
    },

    "property_details": {
        "year_built":              None,
        "effective_year_built":    None,
        "residence_type":          None,
        "square_footage":          None,
        "roof_type_shape":         None,
        "electrical_panel_type":   None,
        "foundation":              None,
        "floors_stories":          None,
        "exterior":                None,
        "framing":                 None,
        "construction_style":      None,
        "construction_quality":    None,
        "kitchen_quality":         None,
        "bedrooms":                None,
        "full_bathrooms":          None,
        "half_bathrooms":          None,
        "bathroom_quality":        None,
        "garage_type":             None,
        "garage_stalls":           None,
        "number_of_detached_structures":      None,
        "detached_structure_types":[],
        "additional_structures": None,
        "number_of_occupants":     None,
    },

    "risk_details": {
        "has_animals":              None,
        "number_of_animals":        None,
        "animals":                  [],
        "additional_animals":       None,
        "other_animals":            None,
        "has_trampoline":           None,
        "has_pool":                 None,
        "pool_has_protective_covering":None,
        "ni_owns_other_properties": None,
    },

    "mortgage_details": {
        "mortgage_company":         None,
        "loan_number":              None,
    },

    "prior_claims_last_5_years":  None,
    "claim_details":              None,

    "created_at":                 None,
    "updated_at":                 None,
}

normalise(form)
data = Form(data=form,history=[],language_processor_response=[],lead_repo=lead_repo,questionaire_repo=questionaire_repo,input_tokens=0,output_tokens=0,cached_tokens=0)
print(form)

async def main():
    print("Assistant:", "Hi! To get started with your insurance information, could you please provide Your Full Name.")

    while True:
        
        db_data = {
          'lead_repo': lead_repo,
          'questionaire_repo': questionaire_repo
        }

        updated_form = db_form_conversion(form, db_data, field_mapping, get_form=True)
        user_input = input("User: ")
        response = await chat_pipeline(data, user_input)
        costs = calculate_costs(data.input_tokens, data.cached_tokens, data.output_tokens)
        total_tokens = data.input_tokens + data.cached_tokens + data.output_tokens
        
        print(f"Input Tokens: {data.input_tokens} - Cost: ${costs['input_cost']:.6f}")
        print(f"Cached Tokens: {data.cached_tokens} - Cost: ${costs['cached_cost']:.6f}")
        print(f"Output Tokens: {data.output_tokens} - Cost: ${costs['output_cost']:.6f}")
        print(f"Total Tokens: {total_tokens} - Total Cost: ${costs['total_cost']:.6f}")
        print(response)

        if next_field(form) is None:
            print("Thank you! All required fields are completed.")
            break


if __name__ == "__main__":
    asyncio.run(main())