from pyteal import *
from subroutine import FEES_ADDRESS, PURCHASE_FEES
from subroutine import function_send_note, function_transfer_arc72, function_fund_arc200, function_transfer_arc200
from subroutine import fees_address, nft_app_id, nft_id, arc200_app_address, arc200_app_id, price, main_fees, counter_party_fees
from subroutine import on_fund, on_delete, on_update, completion_reject, function_close_app, function_contract_fees_arc200, counter_party_address, fees_app_id, note_address, NOTE_ADDRESS, FEES_APP_ID


def approval_program():

    on_create = Seq(
        App.globalPut(nft_app_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_id, Txn.application_args[1]),
        App.globalPut(price, Btoi(Txn.application_args[2])),
        App.globalPut(arc200_app_id, Btoi(Txn.application_args[3])),
        App.globalPut(arc200_app_address, Txn.application_args[4]),
        App.globalPut(counter_party_address, Txn.application_args[5]),
        App.globalPut(counter_party_fees, Btoi(Txn.application_args[6])),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        App.globalPut(main_fees, Int(2)),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        App.globalPut(note_address, Addr(NOTE_ADDRESS)),
        Approve(),
    )

    on_buy = Seq(
        Seq(
            function_send_note(Int(0), Bytes("sale,buy,200/72")),
            function_contract_fees_arc200(
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
            function_fund_arc200(),
            function_transfer_arc200(
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
                ),
                Global.creator_address()
            ),
            function_transfer_arc72(Txn.sender()),
            function_close_app(),
            Approve()
        ),
        Approve()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("sale,cancel,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("sale,create,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update("sale,update,200/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
