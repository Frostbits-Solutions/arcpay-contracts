from subroutine import *
from asa_asa.note_signature import note_signature

note_type = "sale"


def contract_sale_asa_asa():

    on_create = Seq(
        init_asa(0),
        App.globalPut(price, Btoi(Txn.application_args[1])),
        init_payment_asa(2),
        initialisation_smartcontract(3)
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
            read_fees := App.globalGetEx(App.globalGet(fees_app_id), App.globalGet(counter_party_address)),
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
            function_contract_fees_asa(
                Div(
                    Mul(
                        App.globalGet(price),
                        Add(
                            App.globalGet(main_fees),
                            read_fees.value()
                        )
                    ),
                    Int(100)
                ),
                Div(
                    Mul(
                        App.globalGet(price),
                        read_fees.value()
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
                                read_fees.value()
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
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, Seq(function_asa_optout(App.globalGet(asa_id)), function_asa_optout(App.globalGet(paiment_asa_id)), on_delete(f"{note_type},cancel,{note_signature}"))],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund_optin_asa(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
