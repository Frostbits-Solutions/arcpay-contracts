from subroutine import *
from asa_asa.note_signature import note_signature

note_type = "dutch"


def contract_dutch_asa_asa():

    on_create = Seq(
        App.globalPut(asa_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_max_price, Btoi(Txn.application_args[1])),
        App.globalPut(nft_min_price, Btoi(Txn.application_args[2])),
        App.globalPut(end_time_key, Btoi(Txn.application_args[3])),
        App.globalPut(counter_party_address, Txn.application_args[4]),
        App.globalPut(counter_party_fees, Btoi(Txn.application_args[5])),
        App.globalPut(paiment_asa_id, Btoi(Txn.application_args[6])),
        App.globalPut(start_time_key, Global.latest_timestamp()),
        App.globalPut(fees_address, app_addr_from_id(Int(FEES_APP_ID))),
        Assert(App.globalGet(nft_max_price) > App.globalGet(nft_min_price)),
        Assert(App.globalGet(end_time_key) > App.globalGet(start_time_key)),
        App.globalPut(main_fees, Int(2)),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        Approve(),
    )

    on_buy = Seq(
        Assert(
            And(
                # formula to compute price is y = (((max-min)/(start-end)) * (current_time - start )) + max
                # new formula : max - (current-start)((max-min)/(end-start))
                Gtxn[Txn.group_index() - Int(1)].asset_amount() >= Minus(
                    App.globalGet(nft_max_price),
                    Div(
                        Mul(
                            Minus(
                                App.globalGet(nft_max_price),
                                App.globalGet(nft_min_price)
                            ),
                            Minus(
                                Global.latest_timestamp(),
                                App.globalGet(start_time_key)
                            )
                        ),
                        Minus(
                            App.globalGet(end_time_key),
                            App.globalGet(start_time_key)
                        )
                    )
                ),
                Global.latest_timestamp() <= App.globalGet(end_time_key),
                Gtxn[Txn.group_index() - Int(1)].asset_receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender(),
                Gtxn[Txn.group_index() - Int(1)].xfer_asset() == App.globalGet(paiment_asa_id)
            )
        ),
        Seq(
            function_send_note(Int(PURCHASE_FEES), Bytes(f"{note_type},buy,{note_signature}")),
            function_contract_fees_asa(
                Div(
                    Mul(
                        Gtxn[Txn.group_index() - Int(1)].asset_amount(),
                        Add(
                            App.globalGet(main_fees),
                            App.globalGet(counter_party_fees)
                        )
                    ),
                    Int(100)
                ),
                Div(
                    Mul(
                        Gtxn[Txn.group_index() - Int(1)].asset_amount(),
                        App.globalGet(counter_party_fees)
                    ),
                    Int(100)
                )
            ),
            function_payment_asa(
                Minus(
                    Gtxn[Txn.group_index() - Int(1)].asset_amount(),
                    Div(
                        Mul(
                            Gtxn[Txn.group_index() - Int(1)].asset_amount(),
                            Add(
                                App.globalGet(main_fees),
                                App.globalGet(counter_party_fees)
                            )
                        ),
                        Int(100)
                    )
                )
            ),
            function_send_nft_asa(Txn.sender(), Int(1)),
            function_asa_optout(App.globalGet(asa_id)),
            function_asa_optout(App.globalGet(paiment_asa_id)),
            function_close_app(),
            Approve()
        ),
        Reject(),
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(asa_id)), function_asa_optout(App.globalGet(paiment_asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin_asa(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
