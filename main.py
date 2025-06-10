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
    "description": "Lead repository metadata",
    "is_required": True,
    "value": {
      "insured": {
        "type": "object",
        "description": "Personal details of the insured",
        "ask_collected":True,
        "is_required": True,
        "value": {
          "first_name": {
            "type": "string",
            "description": "First name of the insured",
            "is_required": True,
            "value": None
          },
          "middle_name": {
            "type": "string",
            "description": "Middle name of the insured",
            "is_required": False,
            "value": None
          },
          "last_name": {
            "type": "string",
            "description": "Last name of the insured",
            "is_required": True,
            "value": None
          }
        }
      },
      "date_of_birth": {
        "type": "date",
        "description": "Date of birth of the insured",
        "is_required": True,
        "value": None
      },
      "gender": {
        "type": "enum",
        "description": "Gender of the insured",
        "is_required": True,
        "value": None,
        "enum": ["Male", "Female", "Other"]
      },
      "marital_status": {
        "type": "enum",
        "description": "Marital status of the insured",
        "is_required": False,
        "value": None,
        "enum": ["Single", "Married", "Divorced", "Widowed", "Domestic Partner"]
      },
      "email": {
        "type": "string",
        "description": "Email address of the insured",
        "is_required": True,
        "value": None
      },
      "phone_number": {
        "type": "object",
        "description": "Phone contact details",
        "ask_collected":True,
        "is_required": True,
        "value": {
          "country_code": {
            "type": "string",
            "description": "Phone number country code (e.g., +1)",
            "is_required": True,
            "value": None
          },
          "number": {
            "type": "string",
            "description": "Primary phone number of the insured",
            "is_required": True,
            "value": None
          }
        }
      },
      "can_text": {
        "type": "boolean",
        "description": "Whether the insured can receive text messages",
        "is_required": False,
        "value": None
      },
      "contact_preference": {
        "type": "enum",
        "description": "Preferred contact method",
        "is_required": False,
        "value": None,
        "enum": ["Phone", "Email", "Text"]
      },
      "occupation": {
        "type": "string",
        "description": "Occupation of the insured",
        "is_required": False,
        "value": None
      },
      "education": {
        "type": "enum",
        "description": "Highest level of education completed",
        "is_required": False,
        "value": None,
        "enum": ["High School", "Some College", "Associates Degree", "Bachelors", "Masters", "PhD"]
      },
      "social_security_number": {
        "type": "string",
        "description": "Social Security Number of the insured",
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
            "description": "Primary residence address",
            "ask_collected":True,
            "is_required": True,
            "value": {
              "street_address": {
                "type": "string",
                "description": "Primary street address",
                "is_required": True,
                "value": None
              },
              "city": {
                "type": "string",
                "description": "City of residence",
                "is_required": True,
                "value": None
              },
              "state": {
                "type": "string",
                "description": "State of residence",
                "is_required": True,
                "value": None
              },
              "zip_code": {
                "type": "string",
                "description": "ZIP or postal code",
                "is_required": True,
                "value": None
              }
            }
          },
          "mailing_address": {
            "type": "object",
            "description": "Mailing address (if different)",
            "ask_collected":True,
            "is_required": False,
            "value": {
              "street_address": {
                "type": "string",
                "description": "Mailing street address",
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
                "description": "Mailing ZIP or postal code",
                "is_required": False,
                "value": None
              }
            }
          },
          "years_at_address": {
            "type": "integer",
            "description": "Number of years at the current address",
            "is_required": False,
            "value": None
          },
          "county": {
            "type": "string",
            "description": "County of residence",
            "is_required": False,
            "value": None
          }
        }
      }
    }
  },
  "questionaire_repo": {
    "type": "object",
    "description": "Questionnaire repository metadata",
    "is_required": False,
    "value": {
      "number_of_co_insured":{
        "type":"integer",
        "description":"Total number of co-insured individuals",
        "is_required":False,
        "value":None
        },
      "co_insured": {
        "type": "list",
        "description": "List of co‑insured individuals",
        "is_required": False,
        "value": [
          {
            "type": "object",
            "description": "Details for co‑insured one",
            "is_required": False,
            "value": {
              "name": {
                "type": "object",
                "description": "Co‑insured one's name",
                "ask_collected":True,
                "is_required": False,
                "value": {
                  "first_name": {
                    "type": "string",
                    "description": "First name of co‑insured one",
                    "is_required": False,
                    "value": None
                  },
                  "middle_name": {
                    "type": "string",
                    "description": "Middle name of co‑insured one",
                    "is_required": False,
                    "value": None
                  },
                  "last_name": {
                    "type": "string",
                    "description": "Last name of co‑insured one",
                    "is_required": False,
                    "value": None
                  }
                }
              },
              "date_of_birth": {
                "type": "date",
                "description": "Date of birth of co-insured one",
                "is_required": False,
                "value": None
              },
              "gender": {
                "type": "enum",
                "description": "Gender of co-insured one",
                "is_required": False,
                "value": None,
                "enum": ["Male", "Female", "Other"]
              },
              "relationship": {
                "type": "enum",
                "description": "Relationship to the policyholder of co-insured one",
                "is_required": False,
                "value": None,
                "enum": ["Spouse", "Child", "Parent", "Other"]
              },
              "marital_status": {
                "type": "enum",
                "description": "Marital status of co-insured one",
                "is_required": False,
                "value": None,
                "enum": ["Single", "Married", "Divorced", "Widowed", "Domestic Partner"]
              },
              "occupation": {
                "type": "string",
                "description": "Occupation of co-insured one",
                "is_required": False,
                "value": None
              },
              "education": {
                "type": "enum",
                "description": "Education level of co-insured one",
                "is_required": False,
                "value": None,
                "enum": ["High School", "Some College", "Associates Degree", "Bachelors", "Masters", "PhD"]
              }
            }
          }
        ]
      },
      "additional_co_insured":{
        "type":"boolean",
        "description":"Do not add more co-insured",
        "is_required":False,
        "value":None
      },
      "policy_details": {
        "type": "object",
        "description": "Details of the current and prior policy",
        "is_required": True,
        "value": {
          "effective_date": {
            "type": "string",
            "description": "Effective date of the policy",
            "is_required": True,
            "value": None
          },
          "current_carrier": {
            "type": "string",
            "description": "Name of the current insurance carrier",
            "is_required": False,
            "value": None
          },
          "current_carrier_premium": {
            "type": "integer",
            "description": "Premium amount from current carrier",
            "is_required": True,
            "value": None
          },
          "years_with_prior_carrier": {
            "type": "integer",
            "description": "Years with the prior carrier",
            "is_required": False,
            "value": None
          },
          "years_continuous_coverage": {
            "type": "integer",
            "description": "Years of continuous coverage",
            "is_required": False,
            "value": None
          },
          "prior_insurance_liability_limit": {
            "type": "enum",
            "description": "Liability limit of the prior policy",
            "is_required": False,
            "value": None,
            "enum": ["25/50", "50/100", "100/300", "250/500", "300/500", "500/500"]
          },
          "policy_term_length": {
            "type": "enum",
            "description": "Length of the policy term in months",
            "is_required": False,
            "value": None,
            "enum": ["6 months", "12 months"]
          },
          "payment_frequency": {
            "type": "enum",
            "description": "Premium payment frequency",
            "is_required": False,
            "value": None,
            "enum": ["Monthly", "Annually"]
          }
        }
      },
      "coverage_details": {
        "type": "object",
        "description": "Liability and protection limits",
        "is_required": False,
        "value": {
          "bodily_injury": {
            "type": "enum",
            "description": "Bodily injury liability limit",
            "is_required": False,
            "value": None,
            "enum": ["25/50", "50/100", "100/300", "250/500", "300/500", "500/500"]
          },
          "property_damage": {
            "type": "enum",
            "description": "Property damage liability limit",
            "is_required": False,
            "value": None,
            "enum": ["25000", "50000", "100000", "300000", "500000"]
          },
          "personal_injury_protection": {
            "type": "enum",
            "description": "Personal injury protection limit",
            "is_required": False,
            "value": None,
            "enum": ["2500", "5000", "10000"]
          },
          "uninsured_motorist": {
            "type": "enum",
            "description": "Uninsured motorist bodily injury limit",
            "is_required": False,
            "value": None,
            "enum": ["25/50", "50/100", "100/300", "250/500", "300/500", "500500"]
          },
          "uninsured_motorist_pd": {
            "type": "enum",
            "description": "Uninsured motorist property damage limit",
            "is_required": False,
            "value": None,
            "enum": ["10000", "25000", "50000"]
          },
          "underinsured_motorist": {
            "type": "enum",
            "description": "Underinsured motorist bodily injury limit",
            "is_required": False,
            "value": None,
            "enum": ["25/50", "50/100", "100/300", "250/500", "300/500", "500500"]
          },
          "medical_payments": {
            "type": "enum",
            "description": "Medical payments limit",
            "is_required": False,
            "value": None,
            "enum": ["500", "1000", "2000", "5000", "10000"]
          }
        }
      },
      "number_of_drivers": {
        "type": "integer",
        "description": "Number of drivers to be insured",
        "is_required": False,
        "value": None
      },
      "driver_details": {
        "type": "list",
        "description": "List of driver profiles",
        "is_required": False,
        "value": [
          {
            "type": "object",
            "description": "Details for driver one",
            "is_required": False,
            "value": {
              "name": {
                "type": "object",
                "description": "Driver one's name",
                "ask_collected":True,
                "is_required": False,
                "value": {
                  "first_name": {
                    "type": "string",
                    "description": "First name of driver one",
                    "is_required": False,
                    "value": None
                  },
                  "middle_name": {
                    "type": "string",
                    "description": "Middle name of driver one",
                    "is_required": False,
                    "value": None
                  },
                  "last_name": {
                    "type": "string",
                    "description": "Last name of driver one",
                    "is_required": False,
                    "value": None
                  }
                }
              },
              "date_of_birth": {
                "type": "date",
                "description": "Date of birth of driver one",
                "is_required": False,
                "value": None
              },
              "gender": {
                "type": "enum",
                "description": "Gender of driver one",
                "is_required": False,
                "value": None,
                "enum": ["Male", "Female", "Other"]
              },
              "relationship": {
                "type": "enum",
                "description": "Relationship to the policyholder of driver one",
                "is_required": False,
                "value": "Self",
                "enum": ["Spouse", "Child", "Parent", "Self", "Other"]
              },
              "marital_status": {
                "type": "enum",
                "description": "Marital status of driver one",
                "is_required": False,
                "value": None,
                "enum": ["Single", "Married", "Divorced", "Widowed", "Domestic Partner"]
              },
              "occupation": {
                "type": "string",
                "description": "Occupation of driver one",
                "is_required": False,
                "value": None
              },
              "education": {
                "type": "enum",
                "description": "Education level of driver one",
                "is_required": False,
                "value": None,
                "enum": ["High School", "Some College", "Associates Degree", "Bachelors", "Masters", "PhD"]
              },
              "license_status": {
                "type": "enum",
                "description": "License status of driver one",
                "is_required": False,
                "value": None,
                "enum": ["Valid", "Suspended", "Expired"]
              },
              "licensed_state": {
                "type": "string",
                "description": "State where the driver one is licensed",
                "is_required": False,
                "value": None
              },
              "license_number": {
                "type": "string",
                "description": "Driver one's license number (min. 8 chars)",
                "is_required": False,
                "value": None
              },
              "licensed_age": {
                "type": "integer",
                "description": "Age when the driver one was licensed",
                "is_required": False,
                "value": None
              },
              "rated": {
                "type": "boolean",
                "description": "Whether the driver one is rated",
                "is_required": False,
                "value": None
              },
              "sr22_required": {
                "type": "boolean",
                "description": "Whether an SR‑22 is required of driver one",
                "is_required": False,
                "value": None
              },
              "drive_for_rideshare": {
                "type": "boolean",
                "description": "Whether the driver one uses rideshare services",
                "is_required": False,
                "value": None
              },
              "drive_for_delivery": {
                "type": "boolean",
                "description": "Whether the driver one uses delivery services",
                "is_required": False,
                "value": None
              },
              "driver_discounts": {
                "type": "string",
                "description": "Any discounts applicable to the driver one",
                "is_required": False,
                "value": None
              },
              "good_student_discount": {
                "type": "boolean",
                "description": "Good student discount eligibility to driver one",
                "is_required": False,
                "value": None
              },
              "mature_driver_discount": {
                "type": "boolean",
                "description": "Mature driver discount eligibility to driver one",
                "is_required": False,
                "value": None
              },
              "safe_driver_discount": {
                "type": "boolean",
                "description": "Safe driver discount eligibility to driver one",
                "is_required": False,
                "value": None
              }
            }
          }
        ]
      },
      "additional_drivers":{
        "type":"boolean",
        "description":"Do not add more drivers",
        "is_required":False,
        "value":None
      },
      "number_of_vehicles": {
        "type": "integer",
        "description": "Number of vehicles to be insured",
        "is_required": False,
        "value": None
      },
      "vehicle_details": {
        "type": "list",
        "description": "List of vehicles covered",
        "is_required": False,
        "value": [
          {
            "type": "object",
            "description": "Details for vehicle one",
            "is_required": False,
            "value": {
              "vin": {
                "type": "string",
                "description": "Vehicle one Identification Number",
                "is_required": False,
                "value": None
              },
              "make": {
                "type": "string",
                "description": "Vehicle one make",
                "is_required": False,
                "value": None
              },
              "model": {
                "type": "string",
                "description": "Vehicle one model",
                "is_required": False,
                "value": None
              },
              "year": {
                "type": "integer",
                "description": "Vehicle one year",
                "is_required": False,
                "value": None
              },
              "assigned_driver": {
                "type": "enum",
                "description": "Assigned driver details of vehicle one",
                "is_required": False,
                "value": None,
                "enum": []
              },
              "garaged_state": {
                "type": "string",
                "description": "State where the vehicle one is garaged",
                "is_required": False,
                "value": None
              },
              "garaging_address": {
                "type": "object",
                "description": "Vehicle one garaging address",
                "ask_collected":True,
                "is_required": False,
                "value": {
                  "street_address": {
                    "type": "string",
                    "description": "Garaging street address of vehicle one",
                    "is_required": False,
                    "value": None
                  },
                  "city": {
                    "type": "string",
                    "description": "Garaging city of vehicle one",
                    "is_required": False,
                    "value": None
                  },
                  "state": {
                    "type": "string",
                    "description": "Garaging state of vehicle one",
                    "is_required": False,
                    "value": None
                  },
                  "zip_code": {
                    "type": "string",
                    "description": "Garaging ZIP or postal code of vehicle one",
                    "is_required": False,
                    "value": None
                  }
                }
              },
              "annual_miles": {
                "type": "integer",
                "description": "Annual miles driven of vehicle one",
                "is_required": False,
                "value": None
              },
              "vehicle_usage": {
                "type": "enum",
                "description": "Vehicle one usage type",
                "is_required": False,
                "value": None,
                "enum": ["Pleasure", "Commute", "Business", "Rideshare"]
              },
              "financed_vehicle": {
                "type": "boolean",
                "description": "Is the vehicle one financed?",
                "is_required": False,
                "value": None
              },
              "coverage_details": {
                "type": "object",
                "description": "Vehicle‑specific coverages of vehicle one",
                "is_required": False,
                "value": {
                  "comprehensive_deductible": {
                    "type": "enum",
                    "description": "Comprehensive deductible amount of vehicle one",
                    "is_required": False,
                    "value": None
                  },
                  "collision_deductible": {
                    "type": "enum",
                    "description": "Collision deductible amount of vehicle one",
                    "is_required": False,
                    "value": None
                  },
                  "towing_coverage": {
                    "type": "object",
                    "description": "Towing coverage details of vehicle one",
                    "is_required": False,
                    "value": {
                      "coverage_limit": {
                        "type": "integer",
                        "description": "Towing coverage limit of vehicle one",
                        "is_required": False,
                        "value": None
                      }
                    }
                  },
                  "rental_reimbursement": {
                    "type": "object",
                    "description": "Rental reimbursement limits of vehicle one",
                    "is_required": False,
                    "value": {
                      "daily_limit": {
                        "type": "integer",
                        "description": "Daily limit for rental reimbursement of vehicle one",
                        "is_required": False,
                        "value": None
                      },
                      "total_limit": {
                        "type": "integer",
                        "description": "Total limit for rental reimbursement of vehicle one",
                        "is_required": False,
                        "value": None
                      }
                    }
                  },
                  "full_glass_coverage": {
                    "type": "boolean",
                    "description": "Full glass coverage included of vehicle one?",
                    "is_required": False,
                    "value": None
                  }
                }
              },
              "rented_on_turo": {
                "type": "boolean",
                "description": "Is vehicle one rented on Turo?",
                "is_required": False,
                "value": None
              },
              "ownership_type": {
                "type": "enum",
                "description": "Vehicle one ownership type",
                "is_required": False,
                "value": None,
                "enum": ["Owned", "Leased", "Financed"]
              },
              "anti_theft_installed": {
                "type": "boolean",
                "description": "Anti‑theft device installed of vehicle one?",
                "is_required": False,
                "value": None
              }
            }
          }
        ]
      },
      "additional_vehicles":{
        "type":"boolean",
        "description":"Do not add more vehicles",
        "is_required":False,
        "value":None
      }
    }
  }
}

def isComplete(field_object):
    try:
      field_type = field_object['type']
      value = field_object['value']
      if field_type not in {'list', 'object'}:
        return False if value is None else True

      elif field_type ==  "object":
        for sub_field_name, sub_field_object in value.items():
          if not isComplete(sub_field_object):
            return False
        return True

      elif field_type == "list":
        if not value:
          return False
        elif not isinstance(value[0],dict):
          return True
        for sub_field_object in value:
          sub_field_object = {f'field':sub_field_object}
          if not isComplete(sub_field_object):
            return False
        return True
    except Exception as e:
        log_to_file(f"exeption occured while finding if complete or not : { str(e)}")
        return True

def normalise(field_dict, current_path=""):
    for key, field in field_dict.items():
        field_path = f"{current_path}.value.{key}" if current_path else f"{key}"
        field["json_path"] = field_path + ".value"

        # Recurse into objects
        if field["type"] == "object":
            normalise(field["value"], field_path)

        # Recurse into lists
        elif field["type"] == "list":
            for idx, item in enumerate(field["value"]):
                item_path = f"{field_path}.value[{idx}]"
                item["json_path"] = item_path + ".value"
                if item["type"] == "object":
                    normalise(item["value"], item_path)

def next_field(form_object):
  for field_name, field_object in form_object.items():
    value = field_object['value']

    if "ask_collected" in field_object and field_object['ask_collected']:
      if not isComplete(field_object):
        field_object["key"] = field_name
        return field_object

    if field_object['type'] == 'object':
        field = next_field(value)
        if field is not None:
          return field

    elif field_object['type'] == 'list':
      if not value:
        return field_object
      elif not isinstance(value[0],dict):
        return None
      for i,sub_field_object in enumerate(value):
        sub_field_object = {f'{field_name} {i}':sub_field_object}
        field = next_field(sub_field_object)
        if field is not None:
          return field

    else :
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
    for token in re.findall(r"\w+|\[\d+\]", path):
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
    """
    Generic helper: given the path tokens to a list (e.g.
    ['questionaire_repo','value','driver_details','value']), clone index-0 template
    and fix descriptions up to new_count, then sync enums.
    """
    # Navigate to parent of list
    cur = data
    for t in list_path:
        cur = cur[t]
    lst = cur  # this is the list itself
    template = lst[0] if lst else None
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
    groups = ["driver_details", "co_insured", "vehicle_details"]

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
        "number_of_drivers":    len(q_repo["value"].get("driver_details", {}).get("value", [])),
        "number_of_co_insured": len(q_repo["value"].get("co_insured",    {}).get("value", [])),
        "number_of_vehicles":   len(q_repo["value"].get("vehicle_details", {}).get("value", []))
    }
    for cf, new_val in count_fields.items():
        node = q_repo["value"].get(cf)
        if node and node.get("value") is not None:
            node["value"] = new_val

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


        if path in COMMON_SYNC_FIELDS :
          driver_tokens = _parse_tokens(COMMON_SYNC_FIELDS[path])
          driver_cur = form.context.data
          for i, driver_token in enumerate(driver_tokens[:-1]):
              driver_cur = driver_cur[driver_token]
          driver_final = driver_tokens[-1]

          if operation == "update":
              if isinstance(driver_final, int):
                  driver_cur[driver_final] = value
              else:
                  driver_cur[driver_final] = value

          elif operation == "add":
              if isinstance(driver_cur[driver_final], list):
                  driver_cur[driver_final].append(value)
              elif isinstance(driver_cur, dict) and "value" in driver_cur[driver_final] and isinstance(driver_cur[driver_final]["value"], list):
                  driver_cur[driver_final]["value"].append(value)

          elif operation == "delete":
              if isinstance(driver_cur[driver_final], list):
                  driver_cur[driver_final].pop(value)
              elif isinstance(cur, dict) and "value" in driver_cur[driver_final] and isinstance(driver_cur[driver_final]["value"], list):
                  driver_cur[driver_final]["value"].pop(value)


    except Exception as e:
      log_to_file(f"error in updating field: {path} {str(e)}")
      return False

    try:
        # === hook into special fields ===
        json_path = ".".join(
            tok if isinstance(tok, str) else f"[{tok}]"
            for tok in tokens
        )

        # number_of_drivers → resize driver_details list
        if json_path.endswith("questionaire_repo.value.number_of_drivers.value"):
            count = int(value or 0)
            resize_list_with_ordinal(
                form.context.data,
                ["questionaire_repo", "value", "driver_details", "value"],
                count
            )
            update_assigned_driver_enums(form.context.data)

        elif json_path.endswith("questionaire_repo.value.number_of_vehicles.value"):
            count = int(value or 0)
            resize_list_with_ordinal(
                form.context.data,
                ["questionaire_repo", "value", "vehicle_details", "value"],
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
        

        # Auto-sync co-insured data to drivers and increase driver count



        # Handle additional_drivers boolean field
        elif json_path.endswith("questionaire_repo.value.additional_drivers.value"):
            try:
                if value is False:
                    # Add one more driver but don't store the false value
                    current_drivers = form.context.data["questionaire_repo"]["value"]["number_of_drivers"]["value"] or 1
                    new_driver_count = current_drivers + 1
                    
                    # Update number_of_drivers
                    form.context.data["questionaire_repo"]["value"]["number_of_drivers"]["value"] = new_driver_count
                    
                    # Resize driver list
                    resize_list_with_ordinal(
                        form.context.data,
                        ["questionaire_repo", "value", "driver_details", "value"],
                        new_driver_count
                    )
                    
                    # Keep additional_drivers as None (don't store false)
                    form.context.data["questionaire_repo"]["value"]["additional_drivers"]["value"] = None
                    
                    update_assigned_driver_enums(form.context.data)
                    log_to_file(f"Added one more driver (total: {new_driver_count}) - additional_drivers kept as None")
                    
                elif value is True:
                    # Set additional_drivers to true (no more drivers wanted)
                    form.context.data["questionaire_repo"]["value"]["additional_drivers"]["value"] = True
                    log_to_file("Set additional_drivers to True - no more drivers will be added")
                    
            except Exception as e:
                log_to_file(f"Error handling additional_drivers: {str(e)}")

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

                    
                    
                    # Also increase drivers to accommodate new co-insured
                
                    current_drivers = len(form.context.data["questionaire_repo"]["value"]["driver_details"]["value"])
                    required_drivers = current_drivers + 1
                    if current_drivers < required_drivers:
                        resize_list_with_ordinal(
                            form.context.data,
                            ["questionaire_repo", "value", "driver_details", "value"],
                            required_drivers
                        )
                        form.context.data["questionaire_repo"]["value"]["number_of_drivers"]["value"] = required_drivers
                    
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
        if "questionaire_repo.value.co_insured.value.[" in json_path:
            try:
                # Extract co-insured index from the path
                index = json_path.split('[')[1].split(']')[0]
                if index is not None:
                    co_insured_index = int(index)
                    driver_index = co_insured_index + 1  # co-insured[0] -> driver[1], co-insured[1] -> driver[2], etc.
                    
                    # Get current number of drivers
                    current_drivers = len(form.context.data["questionaire_repo"]["value"]["driver_details"]["value"])
                    required_drivers = driver_index + 1  # +1 because we need driver[driver_index] to exist
                    
                    # Increase number of drivers if needed
                    if current_drivers < required_drivers:
                        resize_list_with_ordinal(
                            form.context.data,
                            ["questionaire_repo", "value", "driver_details", "value"],
                            required_drivers
                        )
                        # Update number_of_drivers field
                        form.context.data["questionaire_repo"]["value"]["number_of_drivers"]["value"] = required_drivers
                        log_to_file(f"Auto-increased number of drivers to {required_drivers} to accommodate co-insured {co_insured_index}")
                    
                    # Copy co-insured data to corresponding driver
                    co_insured_data = form.context.data["questionaire_repo"]["value"]["co_insured"]["value"][co_insured_index]["value"]
                    driver_data = form.context.data["questionaire_repo"]["value"]["driver_details"]["value"][driver_index]["value"]
                    
                    # Define fields to sync from co-insured to driver
                    new_sync_fields = [
                        "name", "date_of_birth", "gender", "relationship", 
                        "marital_status", "occupation", "education"
                    ]
                    
                    for field in new_sync_fields:
                        if field in co_insured_data and field in driver_data:
                            if field == "name":
                                # Copy all name sub-fields
                                for name_field in ["first_name", "middle_name", "last_name"]:
                                    if (co_insured_data[field]["value"][name_field]["value"] is not None and 
                                        co_insured_data[field]["value"][name_field]["value"] != ""):
                                        driver_data[field]["value"][name_field]["value"] = co_insured_data[field]["value"][name_field]["value"]
                            else:
                                # Copy simple field
                                if (co_insured_data[field]["value"] is not None and 
                                    co_insured_data[field]["value"] != ""):
                                    driver_data[field]["value"] = co_insured_data[field]["value"]
                    
                    # Update assigned driver enums after adding new drivers
                    update_assigned_driver_enums(form.context.data)
                    
                    log_to_file(f"Auto-synced co-insured {co_insured_index} data to driver {driver_index}")
                    
            except Exception as e:
                log_to_file(f"Error auto-syncing co-insured to driver: {str(e)}")

    except Exception as e:
        log_to_file(f"error in multiplying fields: {path} {str(e)}")
        return False

    finally:
      try:
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


normalise(form)
data = Form(data=form, history=[],language_processor_response=[],input_tokens=0,output_tokens=0,cached_tokens=0)

# Token pricing constants (per 1M tokens)
INPUT_TOKEN_PRICE = 0.80  # $0.80 / 1M tokens
CACHED_TOKEN_PRICE = 0.20  # $0.20 / 1M tokens  
OUTPUT_TOKEN_PRICE = 3.20  # $3.20 / 1M tokens

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
async def get_field(field_description : str):
  print("get_field called with field_description: ",field_description)
  """this fucntion returns fields based in given description"""
  ctx= next_field(data.data)
  log_to_file(f"field_description: {field_description}")
  try:
    desc_path_mapping = extract_description_to_path(data.data)
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
    
    data.input_tokens += int(actual_input_tokens)
    data.output_tokens += int(completion_tokens)
    data.cached_tokens += int(cached_tokens)
    
    costs = calculate_costs(actual_input_tokens, cached_tokens, completion_tokens)
    print(f"Input Tokens: {actual_input_tokens} - Cost: ${costs['input_cost']:.6f}")
    print(f"Cached Tokens: {cached_tokens} - Cost: ${costs['cached_cost']:.6f}")
    print(f"Output Tokens: {completion_tokens} - Cost: ${costs['output_cost']:.6f}")
    print(f"Total Cost: ${costs['total_cost']:.6f}")
    
    response = json.loads(response["choices"][0]["message"]["content"])
    print("get_field response: ",response)
    if response["found"]:
      print("get_field response: ",find_object_by_json_path(data.data,response["path"]))
      log_to_file(f"get_field response: {find_object_by_json_path(data.data,response['path'])}")
      return find_object_by_json_path(data.data,response["path"])
    else :
      return None
  except Exception as e:
      log_to_file(str(e))

def get_today_date():
  """Returns today's date in dd-mm-yyyy format"""
  return str(datetime.now().strftime("%d-%m-%Y"))

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
      also check for dates today's date is {get_today_date()} date of birth should be in the past and effective date should be in the future.

      if user says 'same as before : value' or 'same as this field : value' or 'same as previous field : value' then return {{"command_type":"update","fields":{{"field_description from next_field":"value from user"}}}} do not pass 'same as before' or 'same as this field' or 'same as previous field' text in value. 
      if user provide information that is not in next_field then catagorize and make fields based on descriptions.

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
      print("language processor response: ",response)
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
          
          costs = calculate_costs(actual_input_tokens_sum, cached_tokens_sum, output_tokens_sum)
          print(f"Input Tokens: {actual_input_tokens_sum} - Cost: ${costs['input_cost']:.6f}")
          print(f"Cached Tokens: {cached_tokens_sum} - Cost: ${costs['cached_cost']:.6f}")
          print(f"Output Tokens: {output_tokens_sum} - Cost: ${costs['output_cost']:.6f}")
          print(f"Total Cost: ${costs['total_cost']:.6f}")
          
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

    if the command is to delete a field that is not in filled_fields then dont return any command.

    if not then return a list of commands to fix them.

    If there are no commands to generate, return an empty list.

    Output exactly as JSON with one key "commands" whose value is an array of strings, for example:
    {{
    "commands": [list of commands to fix the form]
    }}
    example: [    
    "Incorrect value for dob: expected 31/05/2003, found 30/05/2003",
    "Copy insured address into mailing address field",
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
  
  costs = calculate_costs(actual_input_tokens, cached_tokens, completion_tokens)
  print(f"Input Tokens: {actual_input_tokens} - Cost: ${costs['input_cost']:.6f}")
  print(f"Cached Tokens: {cached_tokens} - Cost: ${costs['cached_cost']:.6f}")
  print(f"Output Tokens: {completion_tokens} - Cost: ${costs['output_cost']:.6f}")
  print(f"Total Cost: ${costs['total_cost']:.6f}")
  
  
  response = json.loads(response["choices"][0]["message"]["content"])
  log_to_file(f"validation_agent response: {response}")
  return response

async def reply_agent(data,message):
  log_to_file("reply_agent called")
  print("reply_agent called :",message)
  history = data.history
  log_to_file(f"history: {history}")
  filled_fields = str(extract_non_null_values(data.data)).strip()
  log_to_file(f"filled_fields: {filled_fields}")
  nxt = next_field(data.data)
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

async def chat_pipeline(data,message):
  processed_message = await language_processor(data,message)
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


async def main():
    print("Assistant:", "Hi! To get started with your insurance information, could you please provide Your Full Name.")

    while True:
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