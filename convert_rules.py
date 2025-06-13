import asyncio
import aiohttp
import aiofiles
import yaml
import os
import json
from pathlib import Path

# Raw configuration data in YAML format.
RAW_CONFIG = """
rule-providers:
  reject:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/reject.txt"
    path: ./rule-set/reject.yaml
    interval: 86400
  icloud:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/icloud.txt"
    path: ./rule-set/icloud.yaml
    interval: 86400
  apple:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/apple.txt"
    path: ./rule-set/apple.yaml
    interval: 86400
  google:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/google.txt"
    path: ./rule-set/google.yaml
    interval: 86400
  proxy:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/proxy.txt"
    path: ./rule-set/proxy.yaml
    interval: 86400
  direct:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/direct.txt"
    path: ./rule-set/direct.yaml
    interval: 86400
  private:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/private.txt"
    path: ./rule-set/private.yaml
    interval: 86400
  gfw:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/gfw.txt"
    path: ./rule-set/gfw.yaml
    interval: 86400
  tld-not-cn:
    type: http
    behavior: domain
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/tld-not-cn.txt"
    path: ./rule-set/tld-not-cn.yaml
    interval: 86400
  telegramcidr:
    type: http
    behavior: ipcidr
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/telegramcidr.txt"
    path: ./rule-set/telegramcidr.yaml
    interval: 86400
  cncidr:
    type: http
    behavior: ipcidr
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/cncidr.txt"
    path: ./rule-set/cncidr.yaml
    interval: 86400
  lancidr:
    type: http
    behavior: ipcidr
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/lancidr.txt"
    path: ./rule-set/lancidr.yaml
    interval: 86400
  applications:
    type: http
    behavior: classical
    url: "https://cdn.jsdelivr.net/gh/Loyalsoldier/clash-rules@release/applications.txt"
    path: ./rule-set/applications.yaml
    interval: 86400
"""

async def process_provider(session, name, provider_info):
    """
    Asynchronously downloads, processes, and saves the rules for a single provider.
    """
    url = provider_info.get('url')
    behavior = provider_info.get('behavior')
    path_str = provider_info.get('path')

    if not all([url, behavior, path_str]):
        print(f"Skipping '{name}': missing url, behavior, or path.")
        return

    print(f"Processing '{name}'...")
    try:
        # Asynchronously download the content from the URL.
        async with session.get(url) as response:
            response.raise_for_status()
            content = await response.text()

        # Asynchronously save the original downloaded content.
        path = Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content)
        print(f"Successfully downloaded to {path} for '{name}'")

        # Initialize rule lists.
        rules = {
            "domain": [],
            "domain_suffix": [],
            "ip_cidr": [],
            "process_name": []
        }

        # Process the content line by line.
        for line in content.splitlines():
            clean_line = line.strip()

            if not clean_line or clean_line.startswith('#') or clean_line == 'payload:':
                continue
            
            # If the line is a YAML list item like "- 'rule.com'", extract the rule.
            if clean_line.startswith('- '):
                clean_line = clean_line[2:].strip("'\"")

            rule = clean_line

            if behavior == 'domain':
                if rule.startswith('+.'):
                    if len(rule.split('.')) > 2:
                        rules["domain_suffix"].append(rule[1:])
                        rules["domain"].append(rule[2:])
                    else:
                        rules["domain_suffix"].append(rule[1:])
                else:
                    rules["domain"].append(rule)
            elif behavior == 'ipcidr':
                rules["ip_cidr"].append(rule)
            elif behavior == 'classical':
                if rule.startswith('PROCESS-NAME,'):
                    rules["process_name"].append(rule.split(',', 1)[1])

        # Prepare the final JSON output structure.
        output_json_obj = {
            "version": 1,
            "rules": [rules]
        }
        
        # Pretty-print the JSON string.
        output_json_str = json.dumps(output_json_obj, indent=2)

        # Asynchronously write the final JSON file to the 'sing-box' directory.
        output_filename = Path(f"sing-box/{name}.json")
        async with aiofiles.open(output_filename, 'w', encoding='utf-8') as f:
            await f.write(output_json_str)

        print(f"Successfully generated '{output_filename}'.")
        print("---")

    except aiohttp.ClientError as e:
        print(f"Error downloading {url} for '{name}': {e}")
    except IOError as e:
        print(f"Error writing file for '{name}': {e}")
    except Exception as e:
        print(f"An unexpected error occurred for '{name}': {e}")


async def main():
    """
    Main function to coordinate the asynchronous processing of all rule providers.
    """
    config = yaml.safe_load(RAW_CONFIG)
    rule_providers = config.get('rule-providers', {})
    
    # Create a single aiohttp session to be reused for all requests.
    async with aiohttp.ClientSession() as session:
        # Create a list of tasks, one for each rule provider.
        tasks = [
            process_provider(session, name, info)
            for name, info in rule_providers.items()
        ]
        # Run all tasks concurrently and wait for them to complete.
        await asyncio.gather(*tasks)
    
    print("All rule files processed.")

if __name__ == "__main__":
    # To run this script, you need to install the necessary libraries:
    # pip install aiohttp aiofiles pyyaml
    
    # Ensure the target directories exist.
    Path("./rule-set").mkdir(exist_ok=True)
    Path("./sing-box").mkdir(exist_ok=True)
    print("Created directories: ./rule-set, ./sing-box")
    print("---")
    
    # Start the asyncio event loop.
    asyncio.run(main())
