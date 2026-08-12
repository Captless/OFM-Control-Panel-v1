import json, urllib.request

# Fetch live models
r = urllib.request.urlopen('http://localhost:20128/v1/models')
data = json.loads(r.read().decode('utf-8', errors='ignore'))
model_ids = [m['id'] for m in data['data']]

# Build models object
models_obj = {}
for mid in model_ids:
    name = mid.replace('/', ' ').replace('_', ' ').replace('-', ' ').title()
    models_obj[mid] = {'name': name}

# Full config
config = {
    "$schema": "https://opencode.ai/config.json",
    "provider": {
        "omniroute": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "OmniRoute",
            "options": {
                "baseURL": "http://localhost:20128/v1",
                "apiKey": "sk_omniroute"
            },
            "models": models_obj
        }
    }
}

# Write
with open(r'C:\Users\User\.config\opencode\opencode.jsonc', 'w') as f:
    json.dump(config, f, indent=2)

print(f'Updated config with {len(models_obj)} models')