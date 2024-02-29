# Configure whichever you want to use for the node

block_frost_project_id = ""
blockfrost_base_url = ""

ogmios_host = ""
ogmios_port = ""
ogmios_protocol = ""
ogmios_url = f"{ogmios_protocol}://{ogmios_host}:{ogmios_port}"

kupo_host = ""
kupo_port = ""
kupo_protocol = ""
kupo_url = (f"{kupo_protocol}://{kupo_host}:{kupo_port}" if kupo_host is not None else None)
