from algosdk.v2client.algod import AlgodClient
from pyteal import compileTeal, Mode
from supabase import create_client

from arc200_arc72 import contract_auction_arc200_arc72, contract_dutch_arc200_arc72, contract_sale_arc200_arc72
from arc200_rwa import contract_sale_arc200_rwa
from asa_asa import contract_auction_asa_asa, contract_dutch_asa_asa, contract_sale_asa_asa
from asa_rwa import contract_sale_asa_rwa
from main_arc72 import contract_auction_main_arc72, contract_dutch_main_arc72, contract_sale_main_arc72
from main_asa import contract_auction_main_asa, contract_dutch_main_asa, contract_sale_main_asa
from main_rwa import contract_sale_algo_rwa


url = ''
key = ''

client_supabase = create_client(url, key)


dico_tag = {
    'algo:testnet:algo_rwa_sale_approval:latest': contract_sale_algo_rwa,

    'algo:testnet:asa_rwa_sale_approval:latest': contract_sale_asa_rwa,

    'algo:testnet:algo_asa_auction_approval:latest': contract_auction_main_asa,
    'algo:testnet:algo_asa_dutch_approval:latest': contract_dutch_main_asa,
    'algo:testnet:algo_asa_sale_approval:latest': contract_sale_main_asa,

    'algo:testnet:asa_asa_auction_approval:latest': contract_auction_asa_asa,
    'algo:testnet:asa_asa_dutch_approval:latest': contract_dutch_asa_asa,
    'algo:testnet:asa_asa_sale_approval:latest': contract_sale_asa_asa,

    'voi:testnet:voi_arc72_auction_approval:latest': contract_auction_main_arc72,
    'voi:testnet:voi_arc72_dutch_approval:latest': contract_dutch_main_arc72,
    'voi:testnet:voi_arc72_sale_approval:latest': contract_sale_main_arc72,

    'voi:testnet:arc200_arc72_auction_approval:latest': contract_auction_arc200_arc72,
    'voi:testnet:arc200_arc72_dutch_approval:latest': contract_dutch_arc200_arc72,
    'voi:testnet:arc200_arc72_sale_approval:latest': contract_sale_arc200_arc72,

    'voi:testnet:arc200_rwa_sale_approval:latest': contract_sale_arc200_rwa,
}

if __name__ == "__main__":
    list_to_proces = list(dico_tag.keys())
    # list_to_proces = [el for el in list_to_proces if 'arc72' in el]
    # list_to_proces = ['voi:testnet:voi_arc72_dutch_approval:latest']
    for to_process in list_to_proces:
        print(to_process)
        compiled = compileTeal(dico_tag[to_process](), mode=Mode.Application, version=10)
        algod_token_tx = ""
        headers_tx = {"X-Algo-API-Token": algod_token_tx}
        client = AlgodClient(
            algod_token=algod_token_tx,
            algod_address="https://testnet-api.voi.nodly.io:443",
            headers=headers_tx,
        )
        final_result = client.compile(compiled)['result']
        a = client_supabase.table('contracts_tags')
        check_contract = client_supabase.table('contracts').select('*').eq('byte_code', final_result).execute()
        comment = 'fund_arc72'
        if len(check_contract.data) == 1:
            new_id = check_contract.data[0]['id']
        elif len(check_contract.data) == 0:
            result_contract = client_supabase.table('contracts').insert({"byte_code": final_result, 'name': to_process.split(':')[2] + comment}).execute()
            data_result_contract = result_contract.data
            new_id = result_contract.data[0]['id']
        else:
            raise '2 data for the bytecode'
        client_supabase.table('contracts_tags').update({'contract_id': new_id}).eq('tag', to_process).execute()

