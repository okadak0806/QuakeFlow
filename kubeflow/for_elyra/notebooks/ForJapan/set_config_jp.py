# %%


import json

config = {
    "minlatitude": 41.7,
    "maxlatitude": 43.1,
    "minlongitude": 140.9,
    "maxlongitude": 143.1,
    "starttime": "2018-09-08T03:00:00",
    "endtime": "2018-09-08T05:00:00",
}



# %%
with open("config/config.json", "w") as f:
    json.dump(config, f, indent=2)

# %%
