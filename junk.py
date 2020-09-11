from typing import Dict
def str_user(user: Dict):
    req_fields = ["email", "name", "id"]
    missing_fields = []
    for f in req_fields:
        if f not in user.keys():
            missing_fields.append(f)
    if missing_fields:
        return f"Wrong data, missing fields: {missing_fields}"
    return f"User: [{user['name']}] ({user['email']})"

import json
d = {"name": "ttt",
     "cat": 5}
print(json.dumps(d) )