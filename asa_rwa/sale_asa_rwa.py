from subroutine import *
from asa_rwa.note_signature import note_signature

note_type = "sale"


def contract_sale_asa_rwa():

    on_create = Seq(
        App.globalPut(price, Btoi(Txn.application_args[0])),
        App.globalPut(name, Txn.application_args[1]),
        App.globalPut(description, Txn.application_args[2]),
        App.globalPut(counter_party_address, Txn.application_args[3]),
        App.globalPut(counter_party_fees, Btoi(Txn.application_args[4])),
        App.globalPut(paiment_asa_id, Btoi(Txn.application_args[5])),
        App.globalPut(fees_address, app_addr_from_id(Int(FEES_APP_ID))),
        App.globalPut(main_fees, Int(2)),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        Approve(),
    )

    on_buy = Seq(
        Assert(
            And(
                Gtxn[Txn.group_index() - Int(1)].asset_amount() == App.globalGet(price),
                Gtxn[Txn.group_index() - Int(1)].asset_receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.AssetTransfer,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender(),
                Gtxn[Txn.group_index() - Int(1)].xfer_asset() == App.globalGet(paiment_asa_id)
            )
        ),
        Seq(
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
            function_contract_fees_asa(
                Div(
                    Mul(
                        App.globalGet(price),
                        Add(
                            App.globalGet(main_fees),
                            App.globalGet(counter_party_fees)
                        )
                    ),
                    Int(100)
                ),
                Div(
                    Mul(
                        App.globalGet(price),
                        App.globalGet(counter_party_fees)
                    ),
                    Int(100)
                )
            ),
            function_payment_asa(
                Minus(
                    App.globalGet(price),
                    Div(
                        Mul(
                            App.globalGet(price),
                            Add(
                                App.globalGet(main_fees),
                                App.globalGet(counter_party_fees)
                            )
                        ),
                        Int(100)
                    )
                )
            ),
            function_asa_optout(App.globalGet(paiment_asa_id)),
            function_close_app(),
            Approve()
        ),
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(paiment_asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin_only_asa(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
