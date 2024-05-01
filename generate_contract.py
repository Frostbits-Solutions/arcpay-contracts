from algosdk.v2client.algod import AlgodClient
from auction_arc200_arc72 import approval_program as contract_auction_arc200_arc72
from auction_voi_arc72 import approval_program as contract_auction_voi_arc72
from dutch_arc200_arc72 import approval_program as contract_dutch_arc200_arc72
from dutch_voi_arc72 import approval_program as contract_dutch_voi_arc72
from rwa_arc200 import approval_program as contract_rwa_arc200
from rwa_voi import approval_program as contract_rwa_voi
from sale_arc200_arc72 import approval_program as contract_sale_arc200_arc72
from sale_voi_arc72 import approval_program as contract_sale_voi_arc72
from pyteal import compileTeal, Mode


if __name__ == "__main__":
    compiled = compileTeal(contract_auction_voi_arc72(), mode=Mode.Application, version=10)
    algod_token_tx = ""
    headers_tx = {"X-Algo-API-Token": algod_token_tx}
    client = AlgodClient(
        algod_token=algod_token_tx,
        algod_address="https://testnet-api.voi.nodly.io:443",
        headers=headers_tx,
    )
    print(client.compile(compiled)['result'])