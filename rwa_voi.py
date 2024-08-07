from pyteal import *
from subroutine import FEES_ADDRESS, FEES_APP_ID, NOTE_ADDRESS
from subroutine import fees_address, price, name, description, main_fees, counter_party_fees, fees_app_id, counter_party_address, note_address
from subroutine import function_send_note, function_close_app, function_payment, function_contract_fees
from subroutine import on_update, on_fund, on_delete, completion_reject


def approval_program():

    on_create = Seq(
        App.globalPut(price, Btoi(Txn.application_args[0])),
        App.globalPut(name, Txn.application_args[1]),
        App.globalPut(description, Txn.application_args[2]),
        App.globalPut(counter_party_address, Txn.application_args[3]),
        App.globalPut(counter_party_fees, Btoi(Txn.application_args[4])),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        App.globalPut(main_fees, Int(2)),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        App.globalPut(note_address, Addr(NOTE_ADDRESS)),
        Approve(),
    )

    on_buy = Seq(
        Assert(
            And(
                Gtxn[Txn.group_index() - Int(1)].amount() == App.globalGet(price),
                Gtxn[Txn.group_index() - Int(1)].receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.Payment,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender()
            )
        ),
        Seq(
            function_contract_fees(
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
            function_payment(
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
            function_send_note(Int(0), Bytes("sale,buy,1/rwa")),
            function_close_app(),
            Approve()
        ),
        Reject()
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("sale,cancel,1/rwa")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("sale,create,1/rwa")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("update_price")), on_update("sale,update,1/rwa")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
