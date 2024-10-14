import os
import datetime 
from algosdk.v2client.algod import AlgodClient
from pyteal import compileTeal, Mode
from supabase import create_client
from dotenv import load_dotenv

from arc200_arc72 import contract_auction_arc200_arc72, contract_dutch_arc200_arc72, contract_sale_arc200_arc72
from arc200_rwa import contract_sale_arc200_rwa
from asa_asa import contract_auction_asa_asa, contract_dutch_asa_asa, contract_sale_asa_asa
from asa_rwa import contract_sale_asa_rwa
from main_arc72 import contract_auction_main_arc72, contract_dutch_main_arc72, contract_sale_main_arc72
from main_asa import contract_auction_main_asa, contract_dutch_main_asa, contract_sale_main_asa
from main_rwa import contract_sale_main_rwa

load_dotenv() 

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_KEY')

client_supabase = create_client(url, key)

dico_tag = {
    'algo_asa_auction_approval': {
        'chain': 'algo',
        'pyteal': contract_auction_main_asa
    },
    'algo_asa_dutch_approval': {
        'chain': 'algo',
        'pyteal': contract_dutch_main_asa
    },
    'algo_asa_sale_approval': {
        'chain': 'algo',
        'pyteal': contract_sale_main_asa
    },
    'algo_offchain_sale_approval': {
        'chain': 'algo',
        'pyteal': contract_sale_main_rwa
    },
    'asa_asa_auction_approval': {
        'chain': 'algo',
        'pyteal': contract_auction_asa_asa
    },
    'asa_asa_dutch_approval': {
        'chain': 'algo',
        'pyteal': contract_dutch_asa_asa
    },
    'asa_asa_sale_approval': {
        'chain': 'algo',
        'pyteal':contract_sale_asa_asa
    },
    'asa_offchain_sale_approval': {
        'chain': 'algo',
        'pyteal': contract_sale_asa_rwa
    },
    'voi_arc72_auction_approval': {
        'chain': 'voi',
        'pyteal': contract_auction_main_arc72
    },
    'voi_arc72_dutch_approval': {
        'chain': 'voi',
        'pyteal': contract_dutch_main_arc72
    },
    'voi_arc72_sale_approval': {
        'chain': 'voi',
        'pyteal': contract_sale_main_arc72
    },
    'voi_offchain_sale_approval': {
        'chain': 'voi',
        'pyteal': contract_sale_main_rwa
    },
    'arc200_arc72_auction_approval': {
        'chain': 'voi',
        'pyteal': contract_auction_arc200_arc72
    },
    'arc200_arc72_dutch_approval': {
        'chain': 'voi',
        'pyteal': contract_dutch_arc200_arc72
    },
    'arc200_arc72_sale_approval': {
        'chain': 'voi',
        'pyteal': contract_sale_arc200_arc72
    },
    'arc200_offchain_sale_approval': {
        'chain': 'voi',
        'pyteal': contract_sale_arc200_rwa
    }
}

def compile_contract(tag, proxy_app_id):
    compiled = compileTeal(dico_tag[tag]['pyteal'](proxy_app_id), mode=Mode.Application, version=10)
    algod_token_tx = ""
    headers_tx = {"X-Algo-API-Token": algod_token_tx}
    client = AlgodClient(
        algod_token=algod_token_tx,
        algod_address="https://testnet-api.voi.nodly.io:443",
        headers=headers_tx,
    )
    return client.compile(compiled)['result']


if __name__ == "__main__":
    fees_app_id_dict = {
        'algo': {
            'testnet': 724182571,
            'mainnet': 2337523785
        },
        'voi': {
            'testnet': 87414541,
            'mainnet': 87414541
        }
    }


    tags = list(dico_tag.keys())
    if os.environ.get('TAG_FILTER', '') != '':
        tags = [el for el in tags if os.environ.get('TAG_FILTER') in el]

    # If version is specified, use it, otherwise get the latest version
    if os.environ.get('VERSION', '') != '':
        version = os.environ.get('VERSION')
    else:
        version = client_supabase.table('sdk_versions').select('id').order('created_at', desc=True).limit(1).execute().data[0]['id']
    
    for tag in tags:
        proxy_app_id = fees_app_id_dict[dico_tag[tag]['chain']][os.environ.get('NETWORK')]
        print(f"Processing {tag}")
        byte_code = compile_contract(tag, proxy_app_id)
        comment = os.environ.get('COMMENT')
        check_contract = client_supabase.table('contracts').select('*').eq('byte_code', byte_code).execute()
        if len(check_contract.data) == 1:
            new_id = check_contract.data[0]['id']
        elif len(check_contract.data) == 0:
            result_contract = client_supabase.table('contracts').insert({"byte_code": byte_code, 'name': tag + comment}).execute()
            new_id = result_contract.data[0]['id']
        else:
            raise Exception('Contract duplicated in database: the contract should be unique but found multiple entries.')
        client_supabase.table('contracts_tags_association').upsert({'chain': f"{dico_tag[tag]['chain']}:{os.environ.get('NETWORK')}", 'tag': tag, 'version': version, 'contract': new_id}).execute()

