HF_TOKEN_2 = "ro7 a zebi cree token jdida"

import os
from huggingface_hub import InferenceClient
from google.colab import userdata

# Ensure the HF_TOKEN secret is loaded into os.environ
if "HF_TOKEN_2" not in os.environ:
    os.environ["HF_TOKEN_2"] = userdata.get("HF_TOKEN_2")

client = InferenceClient(
    provider="fal-ai",
    api_key=os.environ["HF_TOKEN_2"],
)

# output is a PIL.Image object
image = client.text_to_image(
    "logo for laghouat football club",
    model="black-forest-labs/FLUX.1-dev",#hna t3amar l description
)
#taswira tchufha kima hak
image