from subroutine import *
from arc200_rwa.note_signature import note_signature

note_type = "sale"


def contract_sale_arc200_rwa():

    on_create = Seq(
        initialisation_rwa(),
        App.globalPut(arc200_app_id, Btoi(Txn.application_args[3])),
        App.globalPut(arc200_app_address, app_addr_from_id(App.globalGet(arc200_app_id))),
        initialisation_smartcontract(4)
    )

    on_buy = Seq(
        Seq(
            read_fees := App.globalGetEx(App.globalGet(fees_app_id), App.globalGet(counter_party_address)),
            function_send_note(Int(ZERO_FEES), Bytes(f"{note_type},buy,{note_signature}")),
            function_contract_fees_arc200(
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
            function_fund_arc(arc200_app_address),
            function_transfer_arc200(
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
                ),
                Global.creator_address()
            ),
            function_close_app(),
        ),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete(f"{note_type},cancel,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund(f"{note_type},create,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update(f"{note_type},update,{note_signature}")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
