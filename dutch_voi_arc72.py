from pyteal import *
from subroutine import FEES_ADDRESS, PURCHASE_FEES, FEES_APP_ID, NOTE_ADDRESS
from subroutine import nft_id, nft_app_id, fees_address, main_fees, counter_party_fees, counter_party_address, fees_app_id, note_address
from subroutine import function_send_note, function_close_app, function_transfer_arc72, function_payment, function_contract_fees
from subroutine import on_delete, on_fund, nft_max_price, nft_min_price, start_time_key, end_time_key, completion_reject


def approval_program():

    on_create = Seq(
        App.globalPut(nft_app_id, Btoi(Txn.application_args[0])),
        App.globalPut(nft_id, Txn.application_args[1]),
        App.globalPut(nft_max_price, Btoi(Txn.application_args[2])),
        App.globalPut(nft_min_price, Btoi(Txn.application_args[3])),
        App.globalPut(end_time_key, Btoi(Txn.application_args[4])),
        App.globalPut(start_time_key, Global.latest_timestamp()),
        App.globalPut(fees_address, Addr(FEES_ADDRESS)),
        Assert(App.globalGet(nft_max_price) > App.globalGet(nft_min_price)),
        Assert(App.globalGet(end_time_key) > App.globalGet(start_time_key)),
        App.globalPut(main_fees, Int(2)),
        App.globalPut(counter_party_fees, Int(1)),
        App.globalPut(counter_party_address, Addr('6J4RO7U2WYQWOGWXQOZUTBBA46W4QSFL5HTHJWC5BZR53RSYRAOPAY7KPM')),
        App.globalPut(fees_app_id, Int(FEES_APP_ID)),
        App.globalPut(note_address, Addr(NOTE_ADDRESS)),

        Approve(),
    )

    on_buy = Seq(
        Assert(
            And(
                # formula to compute price is y = (((max-min)/(start-end)) * (current_time - start )) + max
                # new formula : max - (current-start)((max-min)/(end-start))
                Gtxn[Txn.group_index() - Int(1)].amount() >= Minus(
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
                Gtxn[Txn.group_index() - Int(1)].receiver() == Global.current_application_address(),
                Gtxn[Txn.group_index() - Int(1)].type_enum() == TxnType.Payment,
                Gtxn[Txn.group_index() - Int(1)].sender() == Txn.sender()
            )
        ),
        Seq(
            function_contract_fees(
                Div(
                    Mul(
                        Gtxn[Txn.group_index() - Int(1)].amount(),
                        Add(
                            App.globalGet(main_fees),
                            App.globalGet(counter_party_fees)
                        )
                    ),
                    Int(100)
                ),
                Div(
                    Mul(
                        Gtxn[Txn.group_index() - Int(1)].amount(),
                        App.globalGet(counter_party_fees)
                    ),
                    Int(100)
                )
            ),
            function_payment(
                Minus(
                    Gtxn[Txn.group_index() - Int(1)].amount(),
                    Div(
                        Mul(
                            Gtxn[Txn.group_index() - Int(1)].amount(),
                            Add(
                                App.globalGet(main_fees),
                                App.globalGet(counter_party_fees)
                            )
                        ),
                        Int(100)
                    )
                )
            ),
            function_transfer_arc72(Txn.sender()),
            function_send_note(Int(PURCHASE_FEES), Bytes("dutch,buy,1/72")),
            function_close_app(),
            Approve()
        ),
        Reject(),
    )

    program = Cond(
        [Txn.application_id() == Int(0), on_create],
        [Txn.on_completion() == OnComplete.DeleteApplication, on_delete("dutch,cancel,1/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("fund")), on_fund("dutch,create,1/72")],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("pre_validate")), Approve()],
        [And(Txn.on_completion() == OnComplete.NoOp, Txn.application_args[0] == Bytes("buy")), on_buy],
        completion_reject()
    )

    return program
